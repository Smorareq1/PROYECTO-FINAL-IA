# Plan de Implementación — Módulo de Entrenamiento

> **Alcance**: implementar el módulo `src/training/` completo + los entrypoints CLI `cli/train.py` y `cli/evaluate.py` para entrenar el modelo CNN base (6 clases simples) y el modelo BiLSTM (4 clases compuestas) a partir del corpus propio.
> **Restricciones de la rúbrica** (no negociables): entrenamiento 100 % local, sin internet, sin pesos preentrenados, sin transferencia de aprendizaje desde corpus público. Sólo se usan los WAV grabados por el grupo según `docs/guia_grabacion.md`.
> **Librerías permitidas** (instrucciones.md §Software): PyTorch, torchaudio, scikit-learn, librosa, NumPy, SciPy, Matplotlib. No se permite Hugging Face Transformers, Whisper, Wav2Vec2, ni APIs externas.

---

## 0. Tabla de contenidos

1. [Restricciones y trazabilidad con la rúbrica](#1-restricciones-y-trazabilidad-con-la-rúbrica)
2. [Vista de alto nivel del módulo](#2-vista-de-alto-nivel-del-módulo)
3. [Dataset (`src/training/dataset.py`)](#3-dataset)
4. [DataLoader (`src/training/dataloader.py`)](#4-dataloader)
5. [Scheduler (`src/training/scheduler.py`)](#5-scheduler)
6. [Callbacks (`src/training/callbacks.py`)](#6-callbacks)
7. [Metrics (`src/training/metrics.py`)](#7-metrics)
8. [Trainer (`src/training/trainer.py`)](#8-trainer)
9. [CLI de entrenamiento (`src/cli/train.py`)](#9-cli-de-entrenamiento)
10. [CLI de evaluación (`src/cli/evaluate.py`)](#10-cli-de-evaluación)
11. [Hiperparámetros: CNN vs BiLSTM](#11-hiperparámetros-cnn-vs-bilstm)
12. [Reproducibilidad](#12-reproducibilidad)
13. [Salidas esperadas](#13-salidas-esperadas)
14. [Verificación end-to-end con corpus mock](#14-verificación-end-to-end-con-corpus-mock)
15. [Notebooks asociados](#15-notebooks-asociados)
16. [Comandos de extremo a extremo](#16-comandos-de-extremo-a-extremo)
17. [Riesgos y mitigaciones](#17-riesgos-y-mitigaciones)

---

## 1. Restricciones y trazabilidad con la rúbrica

### Restricciones técnicas

| Restricción | Origen | Cómo se cumple en este plan |
|---|---|---|
| Sin internet en runtime | instrucciones.md §Restricciones | `pip install` se hace antes; el código no hace ningún `requests`/`urlopen`/`huggingface_hub.download`. Se valida con `grep -r "from transformers\|requests.get\|urlopen" src/`. |
| Sin pesos preentrenados | instrucciones.md §Modelos | `BaseModel.__init__` deja pesos en su inicialización por defecto de PyTorch (Xavier/He según capa). Primer commit del modelo entrenado muestra accuracy ~random; commits posteriores muestran convergencia → defensa lo verifica. |
| Sin APIs externas (Whisper, Vosk, Google Speech) | instrucciones.md §Restricciones | Los únicos imports permitidos son los de la lista §Librerías. CI grep contra denylist (ver §17). |
| Entrenado desde cero por el grupo | instrucciones.md §Modelos | Todas las capas se definen en `src/models/{cnn,lstm}.py` (ya existen). El Trainer las instancia y entrena con `nn.CrossEntropyLoss`. |
| Sólo corpus propio para evaluar | instrucciones.md §Dataset | Los splits los genera `scripts/generate_splits.py` sobre `data/manifests/corpus.csv` — corpus 100 % propio. El corpus público (Speech Commands, Common Voice) NO se mezcla. |
| ≥3 técnicas de aumento de datos | instrucciones.md §Técnicas Obligatorias | Ya implementadas en `src/audio/augmentation.py` (5 técnicas). Aplicadas SÓLO al split train; val/test quedan limpios. |
| MFCC ≥13 coeficientes | instrucciones.md §Técnicas Obligatorias | `configs/preprocessing.yaml` fija `n_mfcc: 13`. Implementado en `src/audio/features.py:MFCCExtractor` con `torchaudio`. |

### Trazabilidad por criterio de la rúbrica

| Criterio rúbrica | Pts | Cómo lo cubre este módulo |
|---|---|---|
| 3. Modelo Base de Clasificación | 12 | `src/cli/train.py --model cnn` entrena CNN2D desde cero; `notebooks/04_entrenamiento_cnn.ipynb` documenta. Output: `models/cnn_base/model.pt` + métricas. |
| 4. Modelo Secuencial (LSTM/GRU) | 8 | `src/cli/train.py --model bilstm` entrena BiLSTM. Compara contra CNN para compuestos. |
| 7. Reporte de Métricas | 7 | `cli/evaluate.py` genera matriz de confusión, F1 por clase, top errores, JSON. |
| 2. Recolección y Procesamiento | 12 (parcial) | El Trainer aplica augmentation online (SpecAugment); el dataset lee del manifest auditado. |

---

## 2. Vista de alto nivel del módulo

```
backend/src/
├── training/
│   ├── __init__.py
│   ├── dataset.py        # CommandDataset(torch.utils.data.Dataset)
│   ├── dataloader.py     # make_dataloaders() + class weights
│   ├── scheduler.py      # build_scheduler(name, optimizer, total_steps)
│   ├── callbacks.py      # EarlyStopping, ModelCheckpoint
│   ├── metrics.py        # accuracy, F1 por clase, matriz de confusión, classification report
│   └── trainer.py        # Trainer.fit() / evaluate()
└── cli/
    ├── train.py          # entrypoint: python -m src.cli.train --model {cnn,bilstm}
    └── evaluate.py       # entrypoint: python -m src.cli.evaluate --model {cnn,bilstm} --split {val,test}
```

**Diagrama de dependencias**:

```
configs/{data,preprocessing,training}.yaml
                 │
                 ▼
        src/utils/config_loader.py
                 │
                 ▼
   cli/train.py ──────────┐
        │                 │
        ▼                 ▼
  training/dataloader.py  models/factory.py
        │                 │
        ▼                 ▼
training/dataset.py     models/{cnn,lstm}.py
        │                 │
        ▼                 ▼
audio/features.py       training/trainer.py
audio/augmentation.py        │
audio/normalization.py       ▼
audio/vad.py            training/{scheduler,callbacks,metrics}.py
                             │
                             ▼
                    models/<modelo>/model.pt + metrics.json
```

**Principios de diseño**:

1. **Un solo Trainer genérico** que entrena CNN o BiLSTM. La única diferencia es el modelo, su loss, scheduler, y el reshape del tensor de entrada. El Trainer no contiene lógica condicional por modelo — recibe los componentes por inyección.
2. **El Dataset es agnóstico al modelo**. Devuelve `(mfcc, label)` con `mfcc.shape = (n_mfcc, time)`. La adaptación al input shape de cada modelo se hace en una capa `InputAdapter` que el Trainer aplica antes del forward.
3. **Augmentation online sólo para train**, controlado por el flag `is_train` del Dataset. SpecAugment se aplica sobre el MFCC ya extraído. Las 4 técnicas de waveform (time-shift, pitch-shift, gauss-noise, bg-mix) se aplican offline por `scripts/augment_offline.py` y los WAV resultantes ya están en `data/augmented/` antes de entrenar.
4. **Class weights automáticos**: el DataLoader detecta desbalance y pasa `pos_weight` a la loss.
5. **Sin GPU asumida**: todo el código corre en CPU. Si hay CUDA disponible se usa automáticamente vía `torch.device("cuda" if torch.cuda.is_available() else "cpu")`. La inferencia en la demo es CPU-only (Plan_Software §3.3), así que entrenar en GPU es OK pero no requerido.

---

## 3. Dataset

**Archivo**: `src/training/dataset.py`

### 3.1 Responsabilidades

- Leer el split CSV (`data/splits/{train,val,test}.csv`) y filtrar por la tarea (clases simples o compuestas).
- Cargar el WAV (`raw/` para val/test; `raw/` + `augmented/` para train).
- Aplicar quality check + padding/trim a 2.0 s.
- Extraer MFCC vía `MFCCExtractor` ya implementado.
- Aplicar SpecAugment online (sólo train).
- Devolver `(mfcc_tensor, label_int)`.

### 3.2 Firma propuesta

```python
# src/training/dataset.py
from __future__ import annotations
from pathlib import Path
from typing import Literal

import numpy as np
import soundfile as sf
import torch
from torch.utils.data import Dataset

from src.audio.augmentation import spec_augment
from src.audio.features import MFCCExtractor
from src.audio.normalization import normalize_amplitude
from src.utils.config_loader import load_yaml

Task = Literal["simple", "compound"]


class CommandDataset(Dataset):
    def __init__(
        self,
        split_csv: Path,
        task: Task,                     # "simple" → 6 clases, "compound" → 4 clases
        data_root: Path,
        extractor: MFCCExtractor,
        sample_rate: int = 16_000,
        target_duration_s: float = 2.0,
        is_train: bool = False,
        include_augmented: bool = False,  # True sólo cuando is_train=True
        spec_augment_freq_param: int = 8,
        spec_augment_time_param: int = 25,
        cache_in_memory: bool = True,     # corpus es chico (~80 MB MFCC), cachear ayuda
    ) -> None: ...

    @property
    def class_names(self) -> list[str]: ...

    def __len__(self) -> int: ...

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        # Returns (mfcc, label_int) where mfcc.shape == (n_mfcc, time)
        ...
```

### 3.3 Mapeo de clases

| `task` | `class_names` | Etiqueta entera |
|---|---|---|
| `simple` | `["enciende", "apaga", "izquierda", "derecha", "detente", "ruido_fondo"]` | 0–5 |
| `compound` | `["enciende_rapido", "enciende_lento", "gira_izquierda", "gira_derecha"]` | 0–3 |

Importar `SIMPLE_CLASS_NAMES` y `COMPOUND_CLASS_NAMES` desde `src/domain/commands.py` para mantener consistencia.

### 3.4 Pipeline de cada `__getitem__`

```
row = self._rows[idx]                       # fila del split CSV
audio = load_wav(data_root / row.filepath)  # 16 kHz mono
audio = pad_or_trim(audio, target_samples)  # 2.0 s exactos
audio = normalize_amplitude(audio, 0.9)     # pico 0.9

waveform = torch.from_numpy(audio).unsqueeze(0)  # (1, samples)
mfcc = self._extractor(waveform).squeeze(0)      # (n_mfcc, time) = (13, 201)

if self._is_train:
    mfcc = spec_augment(
        mfcc,
        freq_mask_param=self._spec_freq_param,
        time_mask_param=self._spec_time_param,
        n_freq_masks=2,
        n_time_masks=2,
    )

label = self._class_to_idx[row.class_]
return mfcc, label
```

### 3.5 Carga del split y filtrado por tarea

```python
def _load_split(self, csv_path: Path) -> list[Row]:
    rows = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cls = r["class"]
            if cls not in self.class_names:
                continue                  # filtra simple vs compuesta
            rows.append(Row(filepath=r["filepath"], class_=cls))
    return rows
```

Para `include_augmented=True`: también barre `data/augmented/<clase>/*.wav` y los agrega como muestras del split train con la misma etiqueta. Las clases que no están en `class_names` se ignoran.

### 3.6 Caching

Con ~1500 clips × (13×201) float32 ≈ 16 MB raw MFCC. Aumentado ×5 ≈ 80 MB. Cabe en RAM sin problema. Cachear los MFCC al primer acceso evita re-cómputo en cada época (~30 % más rápido el entrenamiento).

---

## 4. DataLoader

**Archivo**: `src/training/dataloader.py`

### 4.1 Responsabilidad

Una sola función `make_dataloaders()` que construye los 3 loaders (train/val/test) para una tarea dada y calcula los pesos de clase si hace falta.

### 4.2 Firma

```python
# src/training/dataloader.py
def make_dataloaders(
    task: Literal["simple", "compound"],
    data_root: Path,
    splits_dir: Path,
    extractor: MFCCExtractor,
    batch_size: int = 32,
    num_workers: int = 4,
    include_augmented_train: bool = True,
    pin_memory: bool = False,            # True si hay GPU
) -> tuple[DataLoader, DataLoader, DataLoader, list[float]]:
    """
    Returns (train_loader, val_loader, test_loader, class_weights).
    class_weights es una lista de longitud n_classes con pesos inversos
    a la frecuencia (para pasar a CrossEntropyLoss).
    """
```

### 4.3 Class weights

```python
counts = Counter(class_idx for _, class_idx in train_dataset)
total = sum(counts.values())
weights = [total / (len(counts) * counts[i]) for i in range(n_classes)]
# normalizamos para que la media sea 1.0 (no afecta gradientes, sólo escala)
weights = [w / np.mean(weights) for w in weights]
```

Si la clase más numerosa tiene <1.5× la frecuencia de la menos numerosa, NO usar weights (overhead innecesario). El Trainer recibe `class_weights=None` o un tensor; ambos casos se manejan.

### 4.4 Splits: train con augmentation, val/test sin

| Split | Origen | Augmentation |
|---|---|---|
| `train` | `splits/train.csv` + `data/augmented/<clase>/*.wav` | SpecAugment online + 4 variantes offline |
| `val` | `splits/val.csv` | Ninguna |
| `test` | `splits/test.csv` | Ninguna |

**Validación importante**: el `train_loader` debe usar `shuffle=True`, `val_loader`/`test_loader` `shuffle=False`. Esto está dado por `DataLoader(shuffle=...)` no por el Dataset.

---

## 5. Scheduler

**Archivo**: `src/training/scheduler.py`

Wrapper para los dos schedulers exigidos por `configs/training.yaml`:

```python
def build_scheduler(
    name: Literal["one_cycle", "cosine_annealing"],
    optimizer: torch.optim.Optimizer,
    total_steps: int | None = None,    # requerido para one_cycle
    max_lr: float | None = None,       # requerido para one_cycle
    epochs: int | None = None,         # requerido para cosine_annealing
) -> torch.optim.lr_scheduler.LRScheduler:
    if name == "one_cycle":
        return OneCycleLR(
            optimizer,
            max_lr=max_lr,
            total_steps=total_steps,
            pct_start=0.3,
            anneal_strategy="cos",
        )
    if name == "cosine_annealing":
        return CosineAnnealingLR(optimizer, T_max=epochs)
    raise ValueError(f"Unknown scheduler: {name}")
```

**Cuándo se llama `.step()`**:
- `OneCycleLR`: **cada batch** (después del optimizer.step()).
- `CosineAnnealingLR`: **cada época** (al final del epoch).

El Trainer recibe un flag `scheduler_step_per_batch: bool` para diferenciar.

---

## 6. Callbacks

**Archivo**: `src/training/callbacks.py`

Dos callbacks mínimos. Diseño tipo Keras pero ligero (sin framework de events).

### 6.1 EarlyStopping

```python
class EarlyStopping:
    def __init__(self, patience: int = 10, mode: str = "min", min_delta: float = 1e-4) -> None:
        ...

    def step(self, metric: float) -> bool:
        """Devuelve True si hay que parar."""
        ...
```

Monitorea `val_loss` (mode="min") por default. Patience según `configs/training.yaml` (10 para CNN, 15 para BiLSTM).

### 6.2 ModelCheckpoint

```python
class ModelCheckpoint:
    def __init__(self, dir_path: Path, mode: str = "max", monitor: str = "val_f1_macro") -> None:
        ...

    def step(self, model: nn.Module, metric: float, epoch: int) -> bool:
        """Guarda si la métrica mejoró. Devuelve True si guardó."""
        ...
```

Guarda `model.pt` cada vez que mejora `val_f1_macro` (más estable que accuracy con clases desbalanceadas). Mantiene 1 sólo archivo (sobreescribe).

---

## 7. Metrics

**Archivo**: `src/training/metrics.py`

Funciones puras, sin estado. Usa `sklearn.metrics` (permitido).

```python
def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None,
    class_names: list[str],
) -> dict:
    """
    Returns dict con:
      accuracy, f1_macro, f1_micro,
      precision_per_class, recall_per_class, f1_per_class,
      confusion_matrix (np.ndarray),
      classification_report (str),
      top_errors (lista de los 10 clips peor clasificados con su clase real/predicha/conf)
    """
```

```python
def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: list[str],
    out_path: Path,
    normalize: bool = True,
) -> None:
    """Genera PNG con matplotlib + seaborn (ambos permitidos)."""
```

```python
def save_metrics_json(metrics: dict, out_path: Path) -> None:
    """Convierte numpy → list/float, dump a JSON."""
```

---

## 8. Trainer

**Archivo**: `src/training/trainer.py`

### 8.1 Diseño

Una clase `Trainer` que encapsula el loop completo. Inyección de dependencias: recibe model, loaders, loss, optimizer, scheduler, callbacks. No conoce el modelo concreto.

```python
class Trainer:
    def __init__(
        self,
        model: nn.Module,
        input_adapter: Callable[[torch.Tensor], torch.Tensor],
        train_loader: DataLoader,
        val_loader: DataLoader,
        loss_fn: nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: torch.optim.lr_scheduler.LRScheduler | None,
        scheduler_step_per_batch: bool,
        callbacks: list[Callback],
        device: str = "cpu",
        gradient_clip_norm: float = 1.0,
        class_names: list[str] = None,
        log_every_n_steps: int = 20,
    ) -> None: ...

    def fit(self, epochs: int) -> dict:
        """Train loop completo. Retorna historial de métricas por época."""
        ...

    def validate(self) -> dict:
        """Una pasada sobre val_loader, devuelve métricas."""
        ...
```

### 8.2 `input_adapter` — clave para reutilizar el Trainer

El Dataset devuelve `(mfcc, label)` con `mfcc.shape == (n_mfcc, time)`. La forma esperada por cada modelo es distinta:

| Modelo | Forma del input que espera `forward()` |
|---|---|
| CNN2DCommandClassifier | `(batch, 1, n_mfcc, time)` |
| BiLSTMSequentialClassifier | `(batch, time, n_mfcc)` |

El `input_adapter` se construye en `cli/train.py`:

```python
# Para CNN
def cnn_adapter(x: torch.Tensor) -> torch.Tensor:
    # x: (batch, n_mfcc, time)
    return x.unsqueeze(1)                     # → (batch, 1, n_mfcc, time)

# Para BiLSTM
def lstm_adapter(x: torch.Tensor) -> torch.Tensor:
    # x: (batch, n_mfcc, time)
    return x.permute(0, 2, 1).contiguous()    # → (batch, time, n_mfcc)
```

### 8.3 Esqueleto del loop

```python
for epoch in range(1, epochs + 1):
    model.train()
    for batch_idx, (x, y) in enumerate(train_loader):
        x = input_adapter(x).to(device, non_blocking=pin_memory)
        y = y.to(device, non_blocking=pin_memory)

        optimizer.zero_grad()
        logits = model(x)
        loss = loss_fn(logits, y)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), gradient_clip_norm)
        optimizer.step()

        if scheduler is not None and scheduler_step_per_batch:
            scheduler.step()

    if scheduler is not None and not scheduler_step_per_batch:
        scheduler.step()

    val_metrics = self.validate()
    history.append({"epoch": epoch, "train_loss": ..., **val_metrics})

    for cb in callbacks:
        stop = cb.step(model=model, metric=val_metrics["f1_macro"], epoch=epoch, ...)
        if stop:
            return history

return history
```

### 8.4 Mixup (opcional, mejora ~1-2 % F1 con corpus chico)

Activable con flag. Aplica mezcla lineal de pares dentro del mismo batch con `α=0.2`:

```python
def mixup_batch(x, y, alpha=0.2, rng=None):
    if alpha <= 0: return x, y, y, 1.0
    lam = np.random.beta(alpha, alpha)
    idx = torch.randperm(x.size(0))
    x_mix = lam * x + (1 - lam) * x[idx]
    return x_mix, y, y[idx], lam

# en el step:
x_mix, y_a, y_b, lam = mixup_batch(x, y, alpha=0.2)
logits = model(input_adapter(x_mix))
loss = lam * loss_fn(logits, y_a) + (1 - lam) * loss_fn(logits, y_b)
```

Sólo se aplica con probabilidad 0.5 por batch (mantiene batches "limpios" para que el modelo no olvide la tarea original).

---

## 9. CLI de entrenamiento

**Archivo**: `src/cli/train.py`

### 9.1 Argumentos

```bash
python -m src.cli.train \
    --model {cnn,bilstm} \
    --config configs/training.yaml \
    --data-config configs/data.yaml \
    --preprocessing-config configs/preprocessing.yaml \
    --splits-dir backend/data/splits \
    --output-dir backend/models \
    [--epochs 60] \
    [--batch-size 32] \
    [--mixup] \
    [--no-augmented] \
    [--seed 42]
```

### 9.2 Flujo

1. `set_global_seed(args.seed)` — semilla en numpy/torch/random.
2. Cargar los 3 YAML de config.
3. Construir el extractor MFCC desde `preprocessing.yaml`.
4. Determinar `task` según `--model` (cnn → simple; bilstm → compound).
5. `make_dataloaders(task, ...)` con el extractor y batch_size del config.
6. Construir el modelo con `create_model(args.model, n_classes=..., n_mfcc=13)`.
7. Construir loss:
   - CNN: `CrossEntropyLoss(weight=class_weights, label_smoothing=0.1)`.
   - BiLSTM: `CrossEntropyLoss(weight=class_weights)` (sin label smoothing).
8. Construir optimizer: `torch.optim.AdamW(lr=..., weight_decay=...)` desde config.
9. Construir scheduler con `build_scheduler(...)` usando `total_steps = epochs * len(train_loader)` para one_cycle.
10. Construir input_adapter según el modelo.
11. Construir callbacks: `[EarlyStopping(...), ModelCheckpoint(output_dir / model_name)]`.
12. `Trainer(...).fit(epochs)`.
13. Cargar el mejor checkpoint (ModelCheckpoint lo guardó).
14. Correr `evaluate.py` sobre split val (sanity check final) y persistir métricas.
15. Copiar `configs/training.yaml` a `models/<model>/config.yaml` para trazabilidad.

### 9.3 Outputs

```
backend/models/cnn_base/
  ├── model.pt              # state_dict del mejor checkpoint
  ├── config.yaml           # copia de configs/training.yaml usado
  ├── history.json          # métricas por época
  ├── val_metrics.json      # métricas finales sobre val
  └── (confusion_matrix.png se genera en evaluate.py)
```

---

## 10. CLI de evaluación

**Archivo**: `src/cli/evaluate.py`

### 10.1 Argumentos

```bash
python -m src.cli.evaluate \
    --model {cnn,bilstm} \
    --split {val,test} \
    --weights backend/models/cnn_base/model.pt \
    --output-dir backend/models/cnn_base \
    [--tta]                                  # Test Time Augmentation
```

### 10.2 Flujo

1. Cargar el modelo con `load_model(args.model, args.weights)`.
2. Construir el split correspondiente con `CommandDataset(is_train=False, include_augmented=False)`.
3. Iterar sobre el loader, acumular `y_true`, `y_pred`, `y_proba`, file_paths.
4. (Opcional con `--tta`) repetir la predicción 3 veces con augmentation distinta y promediar logits.
5. `compute_metrics(...)` → dict.
6. `plot_confusion_matrix(...)` → PNG.
7. `save_metrics_json(...)`.
8. Imprimir tabla resumen y top 10 errores.

### 10.3 Outputs

```
backend/models/cnn_base/
  ├── test_metrics.json
  ├── confusion_matrix_test.png
  └── top_errors_test.json     # 10 peores predicciones para análisis
```

---

## 11. Hiperparámetros: CNN vs BiLSTM

Tomados de `configs/training.yaml` (ya existe). El plan no los inventa; los referencia.

| Hyperparam | CNN base | BiLSTM | Justificación |
|---|---|---|---|
| Clases | 6 (5 simples + ruido_fondo) | 4 (compuestas) | Cada modelo se especializa. |
| Input shape al `forward` | `(B, 1, 13, T)` | `(B, T, 13)` | Convolución 2D vs LSTM secuencial. |
| Parámetros entrenables | ~95 K | ~70 K | Modelos chicos → corpus chico. |
| Optimizer | AdamW | AdamW | Estándar moderno. |
| Learning rate inicial | 1e-3 | 5e-4 | LSTM más sensible a LR. |
| Weight decay | 1e-4 | 1e-4 | Regularización L2 leve. |
| Scheduler | OneCycleLR (max_lr=1e-2) | CosineAnnealing | OneCycle converge más rápido en CNN; Cosine es estable para LSTM. |
| Loss | CrossEntropy + label smoothing 0.1 | CrossEntropy (sin smoothing) | Smoothing en CNN ayuda con 6 clases; en BiLSTM con 4 clases es marginal. |
| Batch size | 32 | 32 | Ajustar si OOM. |
| Epochs (máximo) | 60 | 80 | LSTM requiere más por convergencia más lenta. |
| Early stopping patience | 10 | 15 | Ídem. |
| Gradient clip | 1.0 | 1.0 | Protección contra explosión (clave en LSTM). |
| Mixup | Opcional, α=0.2 | No | Mixup en LSTM puede romper la coherencia temporal. |
| Class weights | Si desbalance > 1.5× | Si desbalance > 1.5× | Calculado por dataloader. |
| Métrica de selección | val_f1_macro | val_f1_macro | F1 macro es robusto al desbalance. |
| Reproducibilidad | seed 42 | seed 42 | Determinismo de torch + numpy + random. |

---

## 12. Reproducibilidad

`src/utils/seed.py:set_global_seed(42)` ya existe. Llamarla al inicio de `cli/train.py` y `cli/evaluate.py`. Verificar que setea:

```python
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
```

`DataLoader(num_workers > 0, worker_init_fn=lambda wid: np.random.seed(seed + wid))` para que cada worker tenga semilla determinística.

Limitación conocida: con `num_workers > 0` puede haber diferencias minúsculas entre runs por el orden no determinístico de workers; `torch.use_deterministic_algorithms(True)` lo soluciona pero ralentiza ~10-15 %. Para la entrega, dejar deterministic ON.

---

## 13. Salidas esperadas

Después de correr ambos `train.py`, el árbol de `backend/models/` debe verse así:

```
backend/models/
├── cnn_base/
│   ├── model.pt
│   ├── config.yaml
│   ├── history.json
│   ├── val_metrics.json
│   ├── test_metrics.json
│   ├── confusion_matrix_val.png
│   ├── confusion_matrix_test.png
│   └── top_errors_test.json
└── bilstm/
    └── (mismo patrón con métricas sobre 4 clases)
```

### Métricas objetivo (de Plan_Software §7.4)

| Métrica | Mínimo aceptable | Objetivo |
|---|---|---|
| Accuracy CNN base (test) | > 85 % | > 93 % |
| F1 macro CNN base | > 0.83 | > 0.92 |
| Accuracy BiLSTM (test) | > 80 % | > 90 % |
| F1 macro BiLSTM | > 0.78 | > 0.88 |
| Tasa de rechazo correcto de RUIDO_FONDO | > 90 % | > 95 % |

Si las métricas caen muy por debajo del mínimo después de entrenar con augmentation, ver §17 (riesgos).

---

## 14. Verificación end-to-end con corpus mock

Antes de recibir las grabaciones reales, validar que todo el pipeline corre con el corpus sintético generado por `scripts/extra/generate_mock_corpus.py`:

```bash
# 1. Generar corpus mock (~1800 clips sintéticos, NO son habla real)
python -m scripts.extra.generate_mock_corpus --output backend/data/raw_mock --speakers 10 --per-class 18

# 2. Copiar los WAV a la estructura esperada
cp -r backend/data/raw_mock/* backend/data/raw/

# 3. Augmentar y splitear como con el corpus real
python -m scripts.augment_offline --variants 4 --seed 42
python -m scripts.generate_splits --test-speakers 2 --val-frac 0.15 --seed 42

# 4. Entrenar CNN (debería tardar ~5-10 min y dar accuracy >99% porque las clases sintéticas son trivialmente separables)
python -m src.cli.train --model cnn --epochs 5

# 5. Evaluar
python -m src.cli.evaluate --model cnn --split test
```

**Criterio de éxito de la verificación**: el comando 4 termina sin excepciones, escribe `models/cnn_base/model.pt`, y el comando 5 imprime una matriz de confusión razonable.

Si esto pasa con mock, el pipeline está OK y la diferencia con el corpus real será sólo de métricas (más bajas con habla real, pero la mecánica funciona).

**Importante**: limpiar `data/raw/` antes de las grabaciones reales para no mezclar:

```bash
rm -rf backend/data/raw/* backend/data/processed/* backend/data/augmented/*
# y vaciar manifest
head -1 backend/data/manifests/corpus.csv > /tmp/header && mv /tmp/header backend/data/manifests/corpus.csv
```

---

## 15. Notebooks asociados

Los notebooks (Plan_Software §11) llaman al módulo de entrenamiento como librería, no redefinen lógica:

| Notebook | Qué hace |
|---|---|
| `04_entrenamiento_cnn.ipynb` | Llama a `Trainer.fit()` con un loop interactivo, muestra curvas de loss/accuracy en vivo con matplotlib. |
| `05_entrenamiento_lstm.ipynb` | Ídem para BiLSTM. |
| `06_evaluacion_metricas.ipynb` | Carga `models/<modelo>/model.pt`, corre `evaluate.compute_metrics`, despliega matriz de confusión y top errores. |
| `07_data_augmentation.ipynb` | Ablation study: entrenar `cli/train.py --no-augmented` vs con augmentation, comparar accuracy. |

Convención: cada notebook empieza con:

```python
%load_ext autoreload
%autoreload 2
import sys; sys.path.insert(0, "../backend")
from src.utils.seed import set_global_seed
set_global_seed(42)
```

---

## 16. Comandos de extremo a extremo

Una vez con el corpus real ya grabado, splits hechos y augmentación corrida:

```bash
cd backend
source .venv/bin/activate          # asume PyTorch ya instalado

# 1. Entrenar CNN (6 clases simples + ruido_fondo)
python -m src.cli.train --model cnn --epochs 60 --batch-size 32 --seed 42
# → models/cnn_base/model.pt + history.json + val_metrics.json

# 2. Evaluar CNN sobre test (hablantes held-out)
python -m src.cli.evaluate --model cnn --split test --tta
# → models/cnn_base/test_metrics.json + confusion_matrix_test.png

# 3. Entrenar BiLSTM (4 clases compuestas)
python -m src.cli.train --model bilstm --epochs 80 --batch-size 32 --seed 42
# → models/bilstm/model.pt + history.json + val_metrics.json

# 4. Evaluar BiLSTM
python -m src.cli.evaluate --model bilstm --split test --tta
# → models/bilstm/test_metrics.json + confusion_matrix_test.png

# 5. Verificar que ambos modelos cargan y predicen en modo offline
python -m scripts.predemo_checklist --skip-arduino --skip-network --skip-ambient
# → chequea que models/cnn_base/model.pt y models/bilstm/model.pt cargan + latencia p95 < 250 ms

# 6. Smoke test del pipeline en vivo (sin Arduino)
python -m src.cli.live --mock --mock-dir backend/data/raw
# → corre 20 predicciones contra los WAV reales, compara predicho vs nombre de carpeta
```

Tiempo estimado en CPU (laptop estándar):
- CNN: ~15-25 min para 60 épocas
- BiLSTM: ~25-40 min para 80 épocas

Con GPU (CUDA disponible): ~5-8 min CNN, ~10-15 min BiLSTM.

---

## 17. Riesgos y mitigaciones

| # | Riesgo | Mitigación |
|---|---|---|
| R1 | **Accuracy CNN < 85 %** después de entrenar con corpus real + augmentation. | Verificar primero el balance del corpus con `audit_corpus.py`. Si una clase está <120 muestras, agendar sesión de grabación extra. Si el problema persiste: subir `variants_per_sample` en augmentation a 6, activar mixup, probar lr 5e-4 en lugar de 1e-3. |
| R2 | **Modelo overfittea** (train >>val): patience temprana, gap creciente. | Subir Dropout de 0.4 a 0.5 en CNN; bajar lr; aumentar weight_decay a 5e-4. |
| R3 | **BiLSTM no converge** (loss oscila). | Bajar lr a 2e-4; subir gradient_clip a 0.5; verificar que el input sea `(B, T, F)` y no `(B, F, T)`. |
| R4 | **Test set tiene <10 clips por clase** con 2 held-out speakers + 4 clases compuestas. | Bajar a `--test-speakers 1` con `--val-frac 0.20` en generate_splits. Reportar la limitación en el documento PDF entregable. |
| R5 | **Detección de uso de modelo preentrenado** durante la defensa. | Verificación automática previa: `grep -rE "from transformers\|huggingface\|torchvision.models\|pretrained=True" backend/src/` debe devolver vacío. Documentar en el PDF que los pesos iniciales son aleatorios. |
| R6 | **Run no reproducible** entre máquinas (mismo seed, métricas diferentes). | Usar `torch.use_deterministic_algorithms(True)`. Fijar versión exacta de PyTorch + torchaudio en requirements.txt (ya está: 2.3.0). Documentar la versión en `models/<m>/config.yaml`. |
| R7 | **Class imbalance ruido_fondo vs comandos**: ruido_fondo tiene 200 vs ~125 cada comando simple → algo desbalanceado. | Aplicar class_weights inversamente proporcionales en CrossEntropyLoss. |

---

## Apéndice A — Mapa de archivos a crear

| Archivo | Líneas estimadas | Dependencias internas | Dependencias externas |
|---|---|---|---|
| `src/training/__init__.py` | 0 | — | — |
| `src/training/dataset.py` | 150 | `audio.features`, `audio.augmentation`, `audio.normalization`, `domain.commands` | torch, soundfile, numpy |
| `src/training/dataloader.py` | 80 | `training.dataset` | torch.utils.data |
| `src/training/scheduler.py` | 30 | — | torch.optim.lr_scheduler |
| `src/training/callbacks.py` | 80 | — | torch, numpy |
| `src/training/metrics.py` | 120 | — | sklearn.metrics, numpy, matplotlib, seaborn |
| `src/training/trainer.py` | 200 | `training.callbacks`, `training.metrics` | torch, numpy |
| `src/cli/train.py` | 140 | todo lo anterior + `models.factory`, `utils.config_loader`, `utils.seed` | argparse |
| `src/cli/evaluate.py` | 100 | `training.dataset`, `training.metrics`, `models.factory` | argparse |
| **TOTAL** | **~900** | | |

---

## Apéndice B — Verificación de cumplimiento de restricciones

Antes de la entrega, correr:

```bash
# Sin imports prohibidos
grep -rE "from transformers|from huggingface_hub|whisper|wav2vec|vosk|pretrained=True" backend/src/ && echo "FAIL" || echo "OK"

# Sin URLs hardcoded
grep -rE "https?://" backend/src/ | grep -v docstring | grep -v "github.com/anthropics" && echo "REVISAR" || echo "OK"

# Sólo librerías permitidas
pip freeze | grep -vE "^(torch|torchaudio|numpy|scipy|scikit-learn|librosa|soundfile|sounddevice|noisereduce|pyserial|fastapi|uvicorn|websockets|jinja2|pydantic|pyyaml|tqdm|matplotlib|seaborn|jupyter|ipykernel|black|ruff|mypy|pytest|.*-)" 
# La salida debería estar vacía (sólo deps transitive normales)

# Modo avión durante la entrega
# (no hay forma de testear esto automáticamente; validar con predemo_checklist)
```

---

**Final del plan.** Toda desviación durante implementación debe documentarse en CHANGELOG para defensa oral.
