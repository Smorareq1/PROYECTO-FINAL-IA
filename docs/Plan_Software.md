# Plan de Implementación — Software del Asistente Robótico por Comandos de Voz

> **Objetivo**: 100/100 puntos. Configuración B (PC + Arduino UNO), Modalidad C (panel domótico).
> **Stack**: Python 3.11 · PyTorch 2.x · torchaudio · FastAPI · pyserial · Notebooks Jupyter
> **Equipo software**: 2 personas (en adelante **SW1** y **SW2**)

---

## 0. Tabla de contenidos

1. [Filosofía técnica](#1-filosofía-técnica)
2. [Arquitectura de la solución](#2-arquitectura-de-la-solución)
3. [Stack tecnológico](#3-stack-tecnológico)
4. [Estructura de carpetas](#4-estructura-de-carpetas-clean-architecture)
5. [Pipeline de datos](#5-pipeline-de-datos)
6. [Arquitecturas de modelos](#6-arquitecturas-de-modelos)
7. [Entrenamiento y métricas](#7-entrenamiento-y-métricas)
8. [Inferencia en tiempo real](#8-inferencia-en-tiempo-real)
9. [Comunicación con Arduino](#9-comunicación-con-arduino)
10. [Dashboard FastAPI](#10-dashboard-fastapi)
11. [Notebooks Jupyter](#11-notebooks-jupyter)
12. [División de tareas SW1 / SW2](#12-división-de-tareas-sw1--sw2)
13. [Plan de 7 días](#13-plan-de-7-días)
14. [Defensa oral](#14-preparación-para-la-defensa-oral)
15. [Checklist anti-100](#15-checklist-anti-100-cosas-que-anulan-puntos)

---

## 1. Filosofía técnica

Decisiones de fondo que rigen todo el código:

- **Reproducibilidad obligatoria**. Semilla fija en NumPy, PyTorch, Python random. Determinismo activado en CUDA donde sea posible. Cada experimento se loggea con su `config.yaml`.
- **Separación estricta de capas**: la lógica de dominio (modelos, MFCC, VAD) no conoce nada del hardware ni de FastAPI. La capa de hardware (`pyserial`) no conoce nada del modelo. La capa de aplicación (FastAPI) orquesta sin contener lógica.
- **Type hints en todo**. `mypy --strict` debe pasar. Esto facilita la auditoría del código durante la defensa.
- **No modelos preentrenados**. Cada `nn.Module` se inicializa con pesos aleatorios. Verificable durante la defensa.
- **No internet en runtime**. Toda dependencia precargada en `models/` antes del modo avión.
- **Tests unitarios** en las funciones críticas (extracción MFCC, VAD, parseo de comandos serial). No es exigido por la rúbrica pero es 1 hora de trabajo que blinda la defensa.

---

## 2. Arquitectura de la solución

### 2.1 Diagrama de componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                         COMPUTADORA                              │
│                                                                  │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐   │
│  │  Micrófono  │──▶│   Capture   │──▶│   Audio Buffer      │   │
│  │  Fifine USB │   │  Service    │   │   (circular)        │   │
│  └─────────────┘   └─────────────┘   └──────────┬──────────┘   │
│                                                  │              │
│                                                  ▼              │
│                    ┌──────────────────────────────────────┐    │
│                    │  Preprocessing Pipeline              │    │
│                    │  VAD → Normalize → MFCC (torchaudio) │    │
│                    └──────────────┬───────────────────────┘    │
│                                   │                             │
│                          ┌────────┴────────┐                    │
│                          ▼                 ▼                    │
│              ┌────────────────┐  ┌────────────────┐            │
│              │   CNN 2D       │  │   BiLSTM       │            │
│              │   (comandos    │  │   (comandos    │            │
│              │    simples)    │  │    compuestos) │            │
│              └────────┬───────┘  └────────┬───────┘            │
│                       │                   │                     │
│                       └────────┬──────────┘                     │
│                                ▼                                │
│                    ┌────────────────────┐                       │
│                    │  Decision Layer    │                       │
│                    │  (umbral + mapeo)  │                       │
│                    └─────────┬──────────┘                       │
│                              │                                  │
│           ┌──────────────────┼──────────────────┐              │
│           ▼                  ▼                  ▼              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │ Serial Tx    │   │ FastAPI      │   │ Logger       │       │
│  │ (pyserial)   │   │ Dashboard    │   │ (CSV)        │       │
│  └──────┬───────┘   └──────┬───────┘   └──────────────┘       │
│         │                  │                                    │
└─────────┼──────────────────┼────────────────────────────────────┘
          │                  │
          │ USB              │ HTTP/WebSocket
          ▼                  ▼
   ┌─────────────┐    ┌─────────────┐
   │  Arduino    │    │  Navegador  │
   │  UNO R3     │    │  (operador) │
   └──────┬──────┘    └─────────────┘
          │
   ┌──────┴──────────────────────────────┐
   │       PANEL DOMÓTICO                │
   │  Relé · LED RGB · 2 Buzzers · Motor │
   └─────────────────────────────────────┘
```

### 2.2 Diagrama de secuencia (un comando)

```
Usuario   Mic   AudioBuffer   VAD   MFCC   Modelo   Decision   Serial   Arduino   Actuador
  │        │         │         │      │       │         │         │        │         │
  │ ─voz─▶ │         │         │      │       │         │         │        │         │
  │        │ ─16k──▶ │         │      │       │         │         │        │         │
  │        │         │ ──ven──▶│      │       │         │         │        │         │
  │        │         │         │ ─ok─▶│       │         │         │        │         │
  │        │         │         │      │ ─MFCC▶│         │         │        │         │
  │        │         │         │      │       │ ─pred──▶│         │        │         │
  │        │         │         │      │       │         │ ─byte──▶│        │         │
  │        │         │         │      │       │         │         │ ─USB─▶ │         │
  │        │         │         │      │       │         │         │        │ ─PWM──▶ │
  │        │         │         │      │       │         │         │        │         │
  └─────────────────── Latencia total objetivo: < 200 ms ────────────────────────────┘
```

### 2.3 Latencia objetivo por etapa

| Etapa | Tiempo objetivo | Tiempo real esperado |
|---|---|---|
| Captura de audio | < 30 ms | ~20 ms (chunks de 320 ms) |
| VAD por energía | < 5 ms | ~2 ms |
| Cómputo MFCC (torchaudio CUDA o CPU) | < 30 ms | ~15 ms |
| Inferencia CNN 2D (CPU) | < 30 ms | ~10 ms |
| Inferencia BiLSTM (CPU) | < 50 ms | ~25 ms |
| Decisión + serialización | < 5 ms | ~1 ms |
| Transmisión serial 1 byte @ 115200 | < 1 ms | ~87 µs |
| Respuesta del Arduino | < 50 ms | ~10 ms |
| **TOTAL extremo a extremo** | **< 200 ms** | **~85 ms** |

Margen amplio frente al límite de 500 ms exigido por la rúbrica.

---

## 3. Stack tecnológico

### 3.1 Lenguaje y entorno

- **Python 3.11** (estable, soporte completo de PyTorch 2.x).
- **Conda** o **venv** + `pip-tools` para reproducibilidad. Preferimos `conda` por el manejo de dependencias binarias de `torchaudio`.

### 3.2 Dependencias principales

```
# Núcleo ML
torch==2.3.0
torchaudio==2.3.0
numpy==1.26.4
scipy==1.13.0
scikit-learn==1.4.2

# Audio
sounddevice==0.4.6
soundfile==0.12.1
librosa==0.10.2  # Solo para data augmentation y comparación con torchaudio

# Hardware
pyserial==3.5

# Dashboard
fastapi==0.110.0
uvicorn[standard]==0.29.0
websockets==12.0
jinja2==3.1.3

# Utilidades
pydantic==2.6.4
pyyaml==6.0.1
tqdm==4.66.2
matplotlib==3.8.4
seaborn==0.13.2

# Notebooks
jupyter==1.0.0
ipykernel==6.29.4

# Calidad de código (dev)
black==24.4.0
ruff==0.4.1
mypy==1.10.0
pytest==8.1.1
```

### 3.3 ¿Por qué PyTorch sobre TensorFlow para este proyecto?

Tres razones concretas vinculadas al objetivo de **mejor resultado**:

1. **`torchaudio.transforms` es estado del arte**: incluye `MFCC`, `MelSpectrogram`, `FrequencyMasking` y `TimeMasking` (SpecAugment) como capas de PyTorch que se pueden mover a GPU y se pueden incluir dentro del modelo, evitando que la inferencia cambie de framework entre el preprocesamiento y la red.
2. **Control explícito del entrenamiento**: el bucle de entrenamiento manual permite implementar trucos que mejoran la convergencia con corpus pequeños (mixup, label smoothing, gradient clipping, scheduler de tasa de aprendizaje con `OneCycleLR`).
3. **Reproducibilidad superior**: las semillas en PyTorch son más fiables que en TF cuando hay capas con dropout y batch normalization; esto importa porque la rúbrica pide notebooks reproducibles.

### 3.4 ¿Por qué `torchaudio` sobre `librosa` para MFCC?

Mantenemos `librosa` solo para data augmentation (pitch shifting de calidad superior) y para validación cruzada de las MFCC durante la defensa. La inferencia usa `torchaudio` porque:

- Es ~5× más rápido en CPU.
- Está implementado como capa de red, así que el grafo computacional MFCC + CNN es uno solo.
- Soporta batch processing nativo (importante para entrenar con corpus aumentado de ~10,000 muestras).

---

## 4. Estructura de carpetas (clean architecture)

```
voz-asistente-robotico/
│
├── README.md                           # Descripción, instalación, uso
├── pyproject.toml                      # Configuración de Black, Ruff, Mypy, Pytest
├── requirements.txt                    # Dependencias congeladas (pip freeze)
├── environment.yml                     # Entorno Conda alternativo
├── .gitignore                          # Excluye __pycache__, .pt, .wav grandes, etc.
├── .python-version                     # 3.11
│
├── configs/                            # ⚙️ Configuración (YAML)
│   ├── data.yaml                       # Rutas, tasas de muestreo, splits
│   ├── preprocessing.yaml              # Parámetros MFCC, VAD, augmentation
│   ├── model_cnn.yaml                  # Arquitectura CNN base
│   ├── model_lstm.yaml                 # Arquitectura BiLSTM
│   ├── training.yaml                   # Hiperparámetros, epochs, optimizer
│   └── runtime.yaml                    # Puerto serial, baudios, umbrales
│
├── data/                               # 📂 Datos (gitignored excepto README)
│   ├── README.md                       # Estructura del corpus, instrucciones
│   ├── raw/                            # Grabaciones originales sin procesar
│   │   ├── enciende/
│   │   │   ├── speaker01_001.wav
│   │   │   └── ...
│   │   ├── apaga/
│   │   ├── izquierda/
│   │   ├── derecha/
│   │   ├── detente/
│   │   ├── ruido_fondo/
│   │   ├── enciende_rapido/
│   │   ├── enciende_lento/
│   │   ├── gira_izquierda/
│   │   └── gira_derecha/
│   ├── processed/                      # Audio normalizado y segmentado
│   ├── augmented/                      # Después del data augmentation
│   ├── splits/                         # train.csv, val.csv, test.csv
│   └── speakers.csv                    # Metadata de hablantes (id, género, edad)
│
├── models/                             # 🧠 Modelos entrenados (gitignored excepto los finales)
│   ├── cnn_base/
│   │   ├── model.pt                    # Pesos finales
│   │   ├── config.yaml                 # Config con la que se entrenó
│   │   ├── metrics.json                # Métricas en test
│   │   └── confusion_matrix.png
│   └── bilstm/
│       └── ... (mismo patrón)
│
├── src/                                # 💻 Código fuente principal
│   │
│   ├── __init__.py
│   │
│   ├── domain/                         # 🎯 LÓGICA DE NEGOCIO PURA
│   │   │                               #    (no depende de PyTorch, audio, hw)
│   │   ├── __init__.py
│   │   ├── commands.py                 # Enum Command (ENCIENDE, APAGA...)
│   │   ├── prediction.py               # Dataclass Prediction (label, confidence)
│   │   ├── exceptions.py               # Excepciones de dominio
│   │   └── interfaces.py               # Protocols (Predictor, Actuator)
│   │
│   ├── audio/                          # 🎤 CAPA DE AUDIO
│   │   ├── __init__.py
│   │   ├── capture.py                  # Captura desde sounddevice
│   │   ├── buffer.py                   # Buffer circular
│   │   ├── vad.py                      # Voice Activity Detection
│   │   ├── normalization.py            # Normalización de amplitud
│   │   ├── features.py                 # MFCC con torchaudio
│   │   └── augmentation.py             # 5 técnicas de data augmentation
│   │
│   ├── models/                         # 🧠 ARQUITECTURAS DE RED
│   │   ├── __init__.py
│   │   ├── base.py                     # Clase BaseModel abstracta
│   │   ├── cnn.py                      # CNN2DCommandClassifier
│   │   ├── lstm.py                     # BiLSTMSequentialClassifier
│   │   └── factory.py                  # Builder según config
│   │
│   ├── training/                       # 🏋️ ENTRENAMIENTO
│   │   ├── __init__.py
│   │   ├── dataset.py                  # CommandDataset (PyTorch)
│   │   ├── dataloader.py               # Splits estratificados
│   │   ├── trainer.py                  # Bucle de entrenamiento
│   │   ├── callbacks.py                # EarlyStopping, ModelCheckpoint
│   │   ├── metrics.py                  # Accuracy, F1, matriz de confusión
│   │   └── scheduler.py                # OneCycleLR
│   │
│   ├── inference/                      # ⚡ INFERENCIA EN TIEMPO REAL
│   │   ├── __init__.py
│   │   ├── pipeline.py                 # InferencePipeline (orquestador)
│   │   ├── predictor.py                # Wrappa los modelos cargados
│   │   ├── decision.py                 # Lógica de umbrales y rechazo
│   │   └── benchmark.py                # Medidor de latencia
│   │
│   ├── hardware/                       # 🔌 CONTROL DEL ARDUINO
│   │   ├── __init__.py
│   │   ├── serial_link.py              # Wrapper de pyserial
│   │   ├── command_protocol.py         # Mapeo Comando → byte
│   │   └── arduino_actuator.py         # Implementa Actuator
│   │
│   ├── api/                            # 🌐 FASTAPI DASHBOARD
│   │   ├── __init__.py
│   │   ├── main.py                     # App FastAPI
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── status.py               # GET /api/status
│   │   │   ├── inference.py            # WS /ws/inference
│   │   │   └── manual.py               # POST /api/command/{cmd}
│   │   ├── websocket.py                # Manager de conexiones WS
│   │   ├── schemas.py                  # Pydantic models
│   │   ├── static/                     # CSS, JS del dashboard
│   │   │   ├── style.css
│   │   │   └── dashboard.js
│   │   └── templates/
│   │       └── index.html
│   │
│   ├── utils/                          # 🛠️ UTILIDADES
│   │   ├── __init__.py
│   │   ├── seed.py                     # Setea semillas reproducibles
│   │   ├── logger.py                   # Logging estructurado
│   │   ├── config_loader.py            # Carga YAML con Pydantic
│   │   └── timer.py                    # Context manager para latencias
│   │
│   └── cli/                            # 💻 CLI ENTRYPOINTS
│       ├── __init__.py
│       ├── record.py                   # python -m src.cli.record
│       ├── train.py                    # python -m src.cli.train
│       ├── evaluate.py                 # python -m src.cli.evaluate
│       └── live.py                     # python -m src.cli.live (demo)
│
├── notebooks/                          # 📓 NOTEBOOKS JUPYTER
│   ├── 01_exploracion_corpus.ipynb     # EDA del corpus
│   ├── 02_pipeline_preprocesamiento.ipynb
│   ├── 03_visualizacion_mfcc.ipynb     # Espectrogramas, ejemplos por clase
│   ├── 04_entrenamiento_cnn.ipynb      # Entrenamiento del modelo base
│   ├── 05_entrenamiento_lstm.ipynb     # Entrenamiento del modelo secuencial
│   ├── 06_evaluacion_metricas.ipynb    # Matrices de confusión, F1, análisis
│   ├── 07_data_augmentation.ipynb      # Visualización del impacto del aug
│   ├── 08_analisis_latencia.ipynb      # Benchmark del pipeline completo
│   └── 09_comparativa_modelos.ipynb    # CNN vs LSTM, justificación final
│
├── arduino/                            # 🤖 FIRMWARE (hecho por físico-2)
│   ├── firmware.ino                    # Sketch principal del Arduino UNO
│   ├── README.md                       # Cómo cargar el firmware
│   └── protocol.md                     # Documentación del protocolo serial
│
├── tests/                              # ✅ TESTS UNITARIOS
│   ├── __init__.py
│   ├── test_audio_features.py
│   ├── test_vad.py
│   ├── test_command_protocol.py
│   ├── test_decision.py
│   └── fixtures/
│       └── sample.wav
│
├── docs/                               # 📚 DOCUMENTACIÓN ADICIONAL
│   ├── architecture.md
│   ├── protocol.md
│   ├── training_guide.md
│   └── images/
│       ├── component_diagram.png
│       ├── flow_diagram.png
│       └── sequence_diagram.png
│
└── scripts/                            # 🔧 SCRIPTS AUXILIARES
    ├── generate_splits.py              # Crea train/val/test
    ├── augment_offline.py              # Aplica augmentation a todo el corpus
    ├── export_metrics_pdf.py           # Genera tablas para el PDF entregable
    └── verify_offline.py               # Verifica modo avión funcional
```

### 4.1 Reglas de la arquitectura

- **`domain/` no importa nada externo** (ni PyTorch, ni audio, ni FastAPI). Solo dataclasses, enums, protocolos.
- **`audio/`, `models/`, `hardware/` dependen de `domain/`** pero no entre sí. El `Predictor` que usa el modelo recibe un `Command` del dominio sin saber qué hardware lo va a ejecutar.
- **`inference/` orquesta** llamando a `audio/`, `models/` y `hardware/`. Aquí está el "negocio aplicado".
- **`api/` y `cli/` son fachadas**: solo construyen objetos de `inference/` y exponen entradas. No contienen lógica.

### 4.2 Inversión de dependencias (ejemplo concreto)

```python
# src/domain/interfaces.py
from typing import Protocol
from src.domain.commands import Command

class Actuator(Protocol):
    def execute(self, command: Command) -> None: ...

# src/hardware/arduino_actuator.py
from src.domain.commands import Command
from src.domain.interfaces import Actuator
from src.hardware.serial_link import SerialLink

class ArduinoActuator:  # implementa Actuator estructuralmente
    def __init__(self, link: SerialLink) -> None:
        self._link = link

    def execute(self, command: Command) -> None:
        self._link.send_byte(command.to_protocol_byte())

# src/inference/pipeline.py
class InferencePipeline:
    def __init__(self, predictor: Predictor, actuator: Actuator) -> None:
        # No sabe si el Actuator es Arduino, simulado o un mock de tests
        self._predictor = predictor
        self._actuator = actuator
```

Esto permite testear la pipeline sin Arduino conectado, y enchufar un actuador simulado para CI.

---

## 5. Pipeline de datos

### 5.1 Recolección del corpus (script)

`src/cli/record.py` es el script que opera Físico-3 con los voluntarios. Funcionalidad:

- Prompt al hablante con el comando a pronunciar (texto en pantalla grande).
- Beep de inicio (0.5 s antes de grabar).
- Graba 2.0 segundos a 16 kHz, mono, 16-bit PCM.
- Calcula amplitud pico y RMS; rechaza si pico > 0.95 (saturación) o RMS < 0.01 (señal débil).
- Guarda `data/raw/<clase>/speakerNN_idMM.wav`.
- Muestra contador por clase y por hablante en tiempo real.

### 5.2 VAD (Voice Activity Detection)

Implementación dual:
- **Por energía**: ventana deslizante de 25 ms, umbral adaptativo basado en los primeros 200 ms de la grabación (asumidos como silencio).
- **Por cruces por cero (ZCR)**: complementa la energía para distinguir habla de ruido de baja frecuencia.

```python
# src/audio/vad.py — pseudocódigo
def detect_speech(signal: np.ndarray, sr: int = 16000) -> tuple[int, int]:
    """Devuelve (inicio_muestra, fin_muestra) del segmento con voz."""
    frame_len = int(0.025 * sr)
    hop = int(0.010 * sr)
    energy = compute_frame_energy(signal, frame_len, hop)
    zcr = compute_frame_zcr(signal, frame_len, hop)
    noise_floor = np.mean(energy[:int(0.2 * sr / hop)])
    threshold = noise_floor * 5.0  # 5× sobre el piso de ruido
    voiced = (energy > threshold) & (zcr < 0.3)
    start, end = first_and_last_true(voiced)
    return start * hop, min(end * hop + frame_len, len(signal))
```

### 5.3 Extracción de MFCC

Configuración elegida (en `configs/preprocessing.yaml`):

```yaml
sample_rate: 16000
n_fft: 512               # ventana de FFT (32 ms a 16 kHz)
win_length: 400          # 25 ms
hop_length: 160          # 10 ms (10 ms de paso, da 100 frames/seg)
n_mels: 40               # bandas Mel
n_mfcc: 13               # coeficientes (mínimo exigido por rúbrica)
f_min: 50
f_max: 8000
log_mels: true
```

```python
# src/audio/features.py
import torchaudio.transforms as T

class MFCCExtractor(nn.Module):
    def __init__(self, cfg: PreprocessingConfig) -> None:
        super().__init__()
        self.mfcc = T.MFCC(
            sample_rate=cfg.sample_rate,
            n_mfcc=cfg.n_mfcc,
            melkwargs={
                "n_fft": cfg.n_fft,
                "n_mels": cfg.n_mels,
                "hop_length": cfg.hop_length,
                "f_min": cfg.f_min,
                "f_max": cfg.f_max,
            },
        )

    def forward(self, waveform: torch.Tensor) -> torch.Tensor:
        # waveform: (batch, samples) → mfcc: (batch, n_mfcc, time)
        return self.mfcc(waveform)
```

**Salida esperada para 1 segundo a 16 kHz**: tensor de forma `(1, 13, 101)`.

### 5.4 Data augmentation (5 técnicas, mínimo exigido es 3)

Aplicadas **solo al conjunto de entrenamiento**, generando 4 variantes por muestra original (×5 efectivo):

| # | Técnica | Implementación | Parámetros |
|---|---|---|---|
| 1 | Time shifting | numpy roll con padding de ceros | ±200 ms aleatorio |
| 2 | Pitch shifting | `librosa.effects.pitch_shift` | ±2 semitonos uniforme |
| 3 | Ruido gaussiano | sumar `np.random.normal(0, σ, ...)` | SNR 15–25 dB |
| 4 | Ruido ambiente | mezcla con grabaciones de `ruido_fondo/` | SNR 10–20 dB |
| 5 | SpecAugment | `T.FrequencyMasking` + `T.TimeMasking` | freq: 2 bandas de hasta 8 mels; time: 2 bandas de hasta 25 frames |

`scripts/augment_offline.py` corre todo el corpus y crea `data/augmented/` antes del entrenamiento. Esto es más rápido que augmentar online.

### 5.5 Splits (train/val/test)

División **estratificada por clase y por hablante**:

- **Train**: 70% de las muestras de un subconjunto de hablantes.
- **Val**: 15% de los mismos hablantes (para early stopping).
- **Test**: 15% formado por **hablantes completamente disjuntos** (held-out speakers). Esto es crucial: la rúbrica valora la generalización a voces no vistas.

`scripts/generate_splits.py` produce `data/splits/{train,val,test}.csv` con columnas: `path,class,speaker_id`.

---

## 6. Arquitecturas de modelos

### 6.1 Modelo Base — CNN 2D sobre MFCC

```python
# src/models/cnn.py
class CNN2DCommandClassifier(nn.Module):
    def __init__(self, n_classes: int = 6, n_mfcc: int = 13) -> None:
        super().__init__()
        # Bloque 1
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)

        # Bloque 2
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)

        # Bloque 3
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.gap = nn.AdaptiveAvgPool2d(1)  # Global Average Pooling

        # Cabezal
        self.dropout = nn.Dropout(0.4)
        self.fc = nn.Linear(128, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, 1, n_mfcc, time)
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = F.relu(self.bn3(self.conv3(x)))
        x = self.gap(x).flatten(1)  # (batch, 128)
        x = self.dropout(x)
        return self.fc(x)  # (batch, n_classes)
```

**Parámetros entrenables**: ~95,000. **Tamaño en disco**: ~380 KB. **Latencia en CPU**: ~10 ms.

**Justificación del diseño**:
- Tres bloques convolucionales son suficientes para corpus de ~1500 muestras × 5 (aumentado).
- BatchNorm acelera convergencia y reduce sensibilidad al learning rate.
- Global Average Pooling en lugar de Flatten + Dense → menos parámetros, menos overfitting.
- Dropout solo en la cabeza, después de GAP: regulariza sin destruir features convolucionales.

### 6.2 Modelo Secuencial — BiLSTM

```python
# src/models/lstm.py
class BiLSTMSequentialClassifier(nn.Module):
    def __init__(self, n_classes: int = 4, n_mfcc: int = 13) -> None:
        super().__init__()
        self.lstm1 = nn.LSTM(
            input_size=n_mfcc, hidden_size=64,
            num_layers=1, bidirectional=True, batch_first=True,
            dropout=0.0,
        )
        self.lstm2 = nn.LSTM(
            input_size=128,  # 64 * 2 (bidireccional)
            hidden_size=32,
            num_layers=1, bidirectional=True, batch_first=True,
        )
        self.dropout = nn.Dropout(0.4)
        self.fc1 = nn.Linear(64, 32)  # 32 * 2
        self.fc2 = nn.Linear(32, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, time, n_mfcc) — la dim time es la que recurre
        x, _ = self.lstm1(x)              # (batch, time, 128)
        x = F.dropout(x, 0.3, self.training)
        x, (h_n, _) = self.lstm2(x)       # (batch, time, 64)
        # Tomamos el último estado oculto concatenado de ambas direcciones
        forward_h = h_n[-2, :, :]
        backward_h = h_n[-1, :, :]
        h = torch.cat([forward_h, backward_h], dim=1)  # (batch, 64)
        h = self.dropout(h)
        h = F.relu(self.fc1(h))
        return self.fc2(h)  # (batch, n_classes)
```

**Parámetros entrenables**: ~70,000. **Tamaño en disco**: ~280 KB. **Latencia en CPU**: ~25 ms.

**Justificación del diseño**:
- Bidireccional: el comando "enciende rápido" tiene información tanto en su inicio (verbo) como en su final (modificador). BiLSTM captura ambas.
- Dos capas: la primera modela fonemas, la segunda modela el orden de las palabras del comando compuesto.
- Tamaño reducido para mantener la latencia bajo el objetivo de 50 ms.

### 6.3 Por qué dos modelos en lugar de uno multitarea

Un solo modelo con 10 clases (6 simples + 4 compuestos) tendría dos problemas:

1. **Desbalance**: las clases compuestas tendrían 75 muestras vs 280 de las simples, sesgando el modelo.
2. **Pérdida de la justificación arquitectónica**: la rúbrica exige específicamente un modelo recurrente para los compuestos. Si un modelo único los resuelve, es más difícil defender por qué se incluyó la LSTM.

La separación permite además aplicar a cada modelo la arquitectura más natural (CNN para fonemas estáticos, RNN para secuencias).

---

## 7. Entrenamiento y métricas

### 7.1 Configuración de entrenamiento (`configs/training.yaml`)

```yaml
# CNN base
cnn:
  batch_size: 32
  epochs: 60
  optimizer: adamw
  learning_rate: 1e-3
  weight_decay: 1e-4
  scheduler: one_cycle
  scheduler_max_lr: 1e-2
  loss: cross_entropy_label_smoothing
  label_smoothing: 0.1
  early_stopping_patience: 10
  gradient_clip_norm: 1.0
  seed: 42

# BiLSTM
lstm:
  batch_size: 32
  epochs: 80
  optimizer: adamw
  learning_rate: 5e-4
  weight_decay: 1e-4
  scheduler: cosine_annealing
  loss: cross_entropy
  early_stopping_patience: 15
  gradient_clip_norm: 1.0
  seed: 42
```

### 7.2 Trucos para maximizar el resultado

Estas técnicas están en el código pero no son obvias; cada una suma 1–3 puntos de F1:

- **Label smoothing 0.1** en la pérdida: previene sobreconfianza, mejora generalización.
- **OneCycleLR** para la CNN: warmup + decay rápido, converge más estable que step decay.
- **Mixup con α=0.2** entre muestras de la misma clase: regulariza sin cambiar etiquetas.
- **Class weights** en la pérdida si el corpus queda desbalanceado tras la auditoría de Físico-3.
- **Test Time Augmentation (TTA)**: en evaluación, predecir 3 variantes de la misma muestra (original + 2 augmentadas) y promediar logits. Mejora ~1–2% accuracy.
- **Stochastic Weight Averaging (SWA)** en las últimas 10 épocas: promedia pesos, suaviza el mínimo.

### 7.3 Métricas a reportar

Por modelo, sobre el conjunto de **test (held-out speakers)**:

- **Accuracy global**.
- **Precision, recall, F1** por clase y macro promedio.
- **Matriz de confusión normalizada** (heatmap con seaborn).
- **Curvas de pérdida y precisión** entrenamiento vs validación.
- **Reporte de errores**: top 10 muestras peor clasificadas con su clase real, predicha y confianza.

Todo esto va en `notebooks/06_evaluacion_metricas.ipynb` y se exporta a `models/<modelo>/metrics.json` + PNGs.

### 7.4 Objetivos de métricas (lo que apuntamos para sacar 100)

| Métrica | Mínimo aceptable | Objetivo del grupo |
|---|---|---|
| Accuracy CNN base (test) | > 85% | > 93% |
| F1 macro CNN base | > 0.83 | > 0.92 |
| Accuracy BiLSTM (test) | > 80% | > 90% |
| F1 macro BiLSTM | > 0.78 | > 0.88 |
| Tasa de rechazo correcto de RUIDO_FONDO | > 90% | > 95% |
| Latencia end-to-end p95 | < 500 ms | < 200 ms |

---

## 8. Inferencia en tiempo real

### 8.1 Flujo del `InferencePipeline`

```python
# src/inference/pipeline.py — esqueleto
class InferencePipeline:
    def __init__(
        self,
        capture: AudioCapture,
        vad: VoiceActivityDetector,
        feature_extractor: MFCCExtractor,
        cnn_predictor: CNNPredictor,
        lstm_predictor: BiLSTMPredictor,
        decision: DecisionLayer,
        actuator: Actuator,
        ws_broadcaster: WebSocketBroadcaster,
    ) -> None:
        ...

    async def run(self) -> None:
        async for chunk in self._capture.stream():
            self._buffer.push(chunk)
            if self._vad.is_speech_ending(self._buffer):
                window = self._buffer.extract_speech_window()
                with timer() as t:
                    mfcc = self._feature_extractor(window)
                    cnn_pred = self._cnn_predictor.predict(mfcc)
                    if cnn_pred.is_compound_candidate():
                        lstm_pred = self._lstm_predictor.predict(mfcc)
                        prediction = self._decision.combine(cnn_pred, lstm_pred)
                    else:
                        prediction = self._decision.from_cnn(cnn_pred)
                latency_ms = t.elapsed_ms()

                if prediction.is_valid():
                    self._actuator.execute(prediction.command)

                await self._ws_broadcaster.publish({
                    "command": prediction.command.value,
                    "confidence": prediction.confidence,
                    "latency_ms": latency_ms,
                    "rejected": not prediction.is_valid(),
                })
```

### 8.2 Lógica de decisión

```python
# src/inference/decision.py
class DecisionLayer:
    def __init__(
        self,
        confidence_threshold: float = 0.85,
        compound_trigger_classes: set[Command] = {Command.ENCIENDE, Command.GIRA_PLACEHOLDER},
    ) -> None:
        ...

    def from_cnn(self, pred: CNNPrediction) -> Prediction:
        if pred.confidence < self.confidence_threshold:
            return Prediction.rejected()
        if pred.label == Command.RUIDO_FONDO:
            return Prediction.rejected()  # No accionar
        return Prediction(command=pred.label, confidence=pred.confidence)

    def combine(self, cnn: CNNPrediction, lstm: LSTMPrediction) -> Prediction:
        # Si LSTM tiene alta confianza en un compuesto, usarlo
        if lstm.confidence > 0.80:
            return Prediction(command=lstm.label, confidence=lstm.confidence)
        return self.from_cnn(cnn)
```

### 8.3 Buffer circular (zero-copy)

`src/audio/buffer.py` mantiene un buffer NumPy de 3 segundos con punteros circulares. Evita reallocaciones en cada chunk.

---

## 9. Comunicación con Arduino

### 9.1 Protocolo

| Byte (hex) | Comando | Acción del Arduino |
|---|---|---|
| `0x01` | ENCIENDE | Cierra relé |
| `0x02` | APAGA | Abre relé |
| `0x03` | IZQUIERDA | Motor pasos: 512 antihorario |
| `0x04` | DERECHA | Motor pasos: 512 horario |
| `0x05` | DETENTE | Beep 200 ms y todo apagado |
| `0x10` | ENCIENDE_RAPIDO | Relé ON + LED RGB blanco brillante |
| `0x11` | ENCIENDE_LENTO | Relé ON + LED RGB azul tenue con fade |
| `0x12` | GIRA_IZQUIERDA | Motor pasos: 1024 antihorario |
| `0x13` | GIRA_DERECHA | Motor pasos: 1024 horario |
| `0xFE` | HEARTBEAT | Arduino responde con `0xFE` (verifica conexión) |
| `0xFF` | RESET | Arduino vuelve a estado inicial |

### 9.2 SerialLink

```python
# src/hardware/serial_link.py
class SerialLink:
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1) -> None:
        self._serial = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(2.0)  # Esperar reset del Arduino al abrir el puerto

    def send_byte(self, byte: int) -> None:
        if not 0 <= byte <= 255:
            raise ValueError(f"Byte fuera de rango: {byte}")
        self._serial.write(bytes([byte]))
        self._serial.flush()

    def heartbeat(self) -> bool:
        self.send_byte(0xFE)
        response = self._serial.read(1)
        return response == bytes([0xFE])
```

### 9.3 Detección automática del puerto

El script `live.py` llama a `find_arduino_port()` que itera sobre los puertos disponibles enviando heartbeats. Esto evita hardcodear `COM3` vs `/dev/ttyUSB0`.

---

## 10. Dashboard FastAPI

### 10.1 Razones para incluirlo

- **Demostración visual**: durante la defensa, el evaluador ve en pantalla grande cada comando reconocido, su confianza y la latencia. Esto es **enorme** para el criterio de Presentación (40 pts).
- **Operación remota**: el dashboard tiene botones para enviar comandos manualmente al Arduino, útiles si la voz falla en vivo.
- **Logger en vivo**: cada predicción queda registrada con timestamp, útil para preparar gráficas.

### 10.2 Endpoints

```
GET  /                           → Dashboard HTML
GET  /api/status                 → Estado del sistema (Arduino conectado, modelos cargados)
WS   /ws/inference               → Stream en vivo de predicciones
POST /api/command/{cmd}          → Envía un comando manualmente al Arduino
GET  /api/metrics                → Métricas agregadas (predicciones por clase, latencias)
GET  /api/health                 → Healthcheck (modo avión, GPU, modelos)
```

### 10.3 Frontend (HTML + JS vanilla, sin frameworks)

El dashboard es una sola página con:

- **Indicador de escucha** (LED virtual verde/amarillo/rojo).
- **Última transcripción reconocida** (texto grande, animado al cambiar).
- **Gráfica de barras** con confianza por clase (Chart.js).
- **Gráfica de latencia** (últimas 30 inferencias).
- **Botones manuales** para cada comando (5 simples + 4 compuestos).
- **Log scrolleable** con timestamps.

### 10.4 Por qué NO usar Streamlit, Gradio o Dash

- **Streamlit**: no es real-time, hace polling.
- **Gradio**: pensado para inferencia uno-a-uno, no para streams continuos.
- **Dash**: trae 30+ MB de dependencias.

FastAPI + WebSocket nativo + HTML estático = ~50 KB de overhead, latencia de WS < 5 ms.

### 10.5 Lanzamiento

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
# Abrir http://localhost:8000 en el navegador
```

Durante la defensa, conectar la laptop a una pantalla externa o proyector y mostrar el dashboard en pantalla completa.

---

## 11. Notebooks Jupyter

La rúbrica exige notebooks reproducibles. Se entrega un set de 9, cada uno enfocado en un aspecto:

| Notebook | Contenido | Quién lo prepara |
|---|---|---|
| `01_exploracion_corpus.ipynb` | Conteo por clase, por hablante, por entorno. Histogramas de duración. Detección de outliers. | SW1 |
| `02_pipeline_preprocesamiento.ipynb` | Demo paso a paso de cargar un WAV → VAD → normalización. Visualizaciones en cada paso. | SW1 |
| `03_visualizacion_mfcc.ipynb` | Espectrogramas Mel y MFCC para una muestra de cada clase. Comparación visual. | SW1 |
| `04_entrenamiento_cnn.ipynb` | Entrenamiento completo del CNN base, con curvas de loss/accuracy en vivo. | SW1 |
| `05_entrenamiento_lstm.ipynb` | Entrenamiento del BiLSTM. Mismo formato. | SW1 |
| `06_evaluacion_metricas.ipynb` | Matrices de confusión, F1 por clase, top errores. | SW1 + SW2 |
| `07_data_augmentation.ipynb` | Ablation study: entrenar con y sin augmentation, comparar métricas. | SW1 |
| `08_analisis_latencia.ipynb` | Benchmark del pipeline completo, gráfica de latencias por etapa. | SW2 |
| `09_comparativa_modelos.ipynb` | Comparativa final CNN vs BiLSTM, justificación arquitectónica. | SW1 + SW2 |

**Reglas para los notebooks**:
- Primer celda: `%load_ext autoreload` + `%autoreload 2` + import de `src/` con paths relativos.
- Cada notebook fija semilla en su segunda celda.
- Cada notebook tiene un markdown final con conclusiones explícitas.
- Ningún notebook contiene lógica que no esté también en `src/`. Los notebooks **importan** funciones de `src/`, no las redefinen.

---

## 12. División de tareas SW1 / SW2

### SW1 — Pipeline de datos y modelos (camino crítico)

**Responsabilidad principal**: que los modelos entrenados produzcan métricas excelentes en el conjunto de test.

| Tarea | Entregable |
|---|---|
| Setup del repo: estructura de carpetas, `pyproject.toml`, `requirements.txt`, `.gitignore` | Repo creado con CI mínimo |
| `src/audio/capture.py` y `src/cli/record.py` | Script de grabación funcionando con barra de progreso por hablante |
| `src/audio/vad.py` con tests unitarios | VAD que aísla correctamente voz en muestras del kit fixtures |
| `src/audio/features.py` (MFCC con torchaudio) | Extractor que produce tensores `(13, 101)` para 1s de audio |
| `src/audio/augmentation.py` (las 5 técnicas) | 5 transforms aplicables individualmente o en pipeline |
| `scripts/augment_offline.py` | Genera `data/augmented/` desde `data/processed/` |
| `scripts/generate_splits.py` | Genera `train.csv`, `val.csv`, `test.csv` con splits estratificados por hablante |
| `src/training/dataset.py` y `dataloader.py` | `CommandDataset` que hereda de `torch.utils.data.Dataset` |
| `src/models/cnn.py` (CNN2D) | Modelo entrenable, parámetros ~95k |
| `src/models/lstm.py` (BiLSTM) | Modelo entrenable, parámetros ~70k |
| `src/training/trainer.py` con OneCycleLR, EarlyStopping, mixup | Bucle de entrenamiento que guarda mejor modelo |
| `notebooks/01` a `07` | Notebooks reproducibles con métricas finales |
| Modelos finales en `models/cnn_base/model.pt` y `models/bilstm/model.pt` | Pesos entrenados con métricas documentadas |

### SW2 — Inferencia en tiempo real, hardware y dashboard

**Responsabilidad principal**: que el sistema completo funcione en vivo el día de la defensa con latencia mínima y dashboard impecable.

| Tarea | Entregable |
|---|---|
| `src/audio/buffer.py` (buffer circular) | Buffer thread-safe con tests |
| `src/inference/predictor.py` (wrappers de CNN y LSTM) | Carga modelos desde disco y predice sin overhead |
| `src/inference/decision.py` | Lógica de umbrales, rechazo y combinación CNN+LSTM |
| `src/inference/pipeline.py` (orquestador async) | Pipeline completo end-to-end |
| `src/inference/benchmark.py` | Medidor de latencia por etapa |
| `src/hardware/serial_link.py` con heartbeat | Comunicación robusta con Arduino |
| `src/hardware/command_protocol.py` | Mapeo `Command` → byte |
| `src/hardware/arduino_actuator.py` | Implementación de `Actuator` |
| `src/api/main.py` y rutas | App FastAPI funcional |
| `src/api/websocket.py` | Manager de conexiones WS |
| `src/api/templates/index.html` + `static/dashboard.js` | Dashboard visual completo |
| `src/cli/live.py` | Punto de entrada de la demo |
| `notebooks/08` análisis de latencia | Benchmark documentado |
| Tests de integración (mockeando Arduino) | `pytest` que pasa al 100% |

### Sincronización SW1 ↔ SW2

- **Día 2**: SW1 entrega `MFCCExtractor` con interfaz estable. SW2 lo usa para empezar a construir `pipeline.py` con un modelo dummy.
- **Día 4**: SW1 entrega primer CNN entrenado (aunque sea con métricas pobres). SW2 conecta el pipeline real.
- **Día 5**: SW1 entrega modelos finales. SW2 valida latencia end-to-end.
- **Día 6–7**: ambos pulen, miden, ajustan umbrales.

---

## 13. Plan de 7 días

Asumimos que hoy es **Lunes 12 mayo**. Entrega: **Lunes 18 mayo**. Defensa: **Miércoles 20 mayo**.

### Día 1 — Lunes (setup y datos)

**Equipo completo**:
- Compra del micrófono y materiales (físico-3).
- Inicio de armado del banco (físico-1, físico-2).

**SW1**:
- Crear repo en GitHub privado (luego se hace público para entrega).
- Estructura de carpetas, `pyproject.toml`, `requirements.txt`.
- Implementar `src/cli/record.py` con la lista de 10 comandos.
- Probar grabación con un integrante: 50 muestras de cada clase como prueba.

**SW2**:
- Configurar entorno local idéntico al de SW1.
- Implementar `src/hardware/serial_link.py` con heartbeat.
- Coordinar con físico-2: tan pronto el firmware del Arduino esté cargado, validar comunicación serial.

### Día 2 — Martes (corpus + preprocesamiento)

**Físico-3**: sesiones de grabación con voluntarios (objetivo: 60% del corpus al final del día).

**SW1**:
- `src/audio/vad.py` + tests unitarios.
- `src/audio/features.py` (MFCC).
- `src/audio/augmentation.py` (las 5 técnicas).
- `notebooks/01_exploracion_corpus.ipynb` con lo grabado hasta ahora.
- `notebooks/02_pipeline_preprocesamiento.ipynb`.

**SW2**:
- `src/audio/buffer.py` con tests.
- `src/api/main.py` esqueleto + dashboard HTML básico (sin lógica real, mostrando datos mock).
- `src/inference/decision.py`.

### Día 3 — Miércoles (corpus completo + primer modelo)

**Físico-3**: completar el corpus (95–100%). Auditoría de calidad.

**SW1**:
- `scripts/generate_splits.py` con splits estratificados por hablante.
- `scripts/augment_offline.py` ejecutado sobre todo el corpus.
- `src/models/cnn.py`.
- `src/training/dataset.py`, `trainer.py`.
- Primer entrenamiento del CNN base (sin augmentation aún) — baseline.

**SW2**:
- `src/inference/predictor.py`.
- `src/inference/pipeline.py` integrando el CNN dummy con el SerialLink real.
- Test end-to-end: hablar al micrófono → byte llega al Arduino → actuador responde.

### Día 4 — Jueves (entrenamientos definitivos)

**SW1**:
- Reentrenar CNN con corpus aumentado.
- `src/models/lstm.py`.
- Entrenamiento del BiLSTM.
- `notebooks/04_entrenamiento_cnn.ipynb` y `05_entrenamiento_lstm.ipynb` finalizados.

**SW2**:
- Conectar predictor real al pipeline.
- `notebooks/08_analisis_latencia.ipynb` con primer benchmark.
- Dashboard FastAPI completo: WebSocket en vivo, gráficas, botones manuales.

### Día 5 — Viernes (métricas y pulido)

**SW1**:
- `notebooks/06_evaluacion_metricas.ipynb` con matrices de confusión.
- `notebooks/07_data_augmentation.ipynb` (ablation study).
- Si hay tiempo: probar mixup, TTA, SWA y elegir el mejor.

**SW2**:
- Optimización de latencia: profiling, caching, reducir conversiones tensor↔numpy.
- Pruebas en el aula real con todo el equipo.
- Ajustar umbral de confianza basado en pruebas reales.
- Implementar grabación del log de la demo a CSV.

### Día 6 — Sábado (documento PDF y video)

**Equipo completo**: redacción del documento entregable. Cada uno escribe la sección que dominará en la defensa.

**SW1**: secciones de modelos, dataset, métricas.
**SW2**: secciones de arquitectura, latencia, hardware, dashboard.
**Físico-1, Físico-2**: secciones de hardware físico, eléctrico, montaje.
**Físico-3**: evidencias, fotografías, video.

`notebooks/09_comparativa_modelos.ipynb` finalizado.

### Día 7 — Domingo (ensayo y entregas)

- Ensayar la defensa completa: cada uno presenta su sección, se hacen preguntas cruzadas.
- Subir repo público, modelos exportados, video.
- Commit final con tag `v1.0-entrega`.

**Lunes 18 mayo**: entrega oficial. **Miércoles 20**: defensa.

---

## 14. Preparación para la defensa oral

### Temas que SW1 debe dominar

1. **MFCC paso a paso**: FFT → potencia → banco de filtros Mel → log → DCT. Saber qué representa cada coeficiente.
2. **Arquitectura CNN**: por qué 3 bloques, por qué 32→64→128 filtros, por qué GAP en lugar de Flatten, por qué BatchNorm.
3. **Arquitectura BiLSTM**: por qué bidireccional, qué captura cada dirección, por qué tomar el último h en lugar de promediar.
4. **Data augmentation**: las 5 técnicas, cuál tuvo más impacto cuantitativo (sostener con números del notebook 07).
5. **Splits por hablante**: por qué es crucial separar hablantes en el test set, qué pasaría si se mezclaran.

### Temas que SW2 debe dominar

1. **Pipeline end-to-end**: cada etapa con su latencia medida.
2. **VAD por energía**: cómo se calibra el umbral, qué pasa con voz baja.
3. **Protocolo serial**: por qué 115200 baudios, por qué 1 byte por comando, por qué el heartbeat.
4. **Decisión multimodelo**: cuándo se usa CNN vs cuándo BiLSTM, cómo se combinan.
5. **Dashboard FastAPI**: por qué WebSocket en lugar de polling, cómo se mide la latencia desde el navegador.

### Preguntas trampa que probablemente harán

| Pregunta | Respuesta corta |
|---|---|
| "¿Por qué no usaron Whisper si es mejor?" | Está prohibido por la rúbrica. Además, Whisper hace ASR genérico; nuestro modelo está optimizado para el conjunto cerrado de comandos del proyecto, lo cual lo hace más rápido y robusto en este dominio específico. |
| "¿Cómo saben que el modelo no memorizó?" | El test set tiene hablantes completamente disjuntos del train. Las métricas reportadas son sobre voces nunca vistas. |
| "¿Qué pasa si dos personas hablan al mismo tiempo?" | El VAD detecta el inicio del habla y captura una ventana fija; si hay solapamiento, la confianza cae bajo el umbral y el comando se rechaza (LED rojo). |
| "¿Por qué 13 coeficientes MFCC y no 40?" | 13 es el mínimo exigido y captura información fonética suficiente. Probamos con 20 y 40 (mostrar notebook); la mejora es marginal y la latencia crece. |
| "¿Por qué la BiLSTM tiene tantos parámetros si la CNN ya clasifica?" | La CNN clasifica comandos aislados pero no captura orden. "Enciende rápido" y "rápido enciende" son distintos y la CNN no los distingue. La BiLSTM modela el orden temporal explícitamente. |
| "Muestren el código del MFCC sin librerías" | Tener listo `notebooks/03` con una implementación a mano (con NumPy puro) al lado de la de `torchaudio`, mostrando que producen los mismos coeficientes con error relativo < 1e-5. Esto blinda la pregunta. |

---

## 15. Checklist anti-100 (cosas que anulan puntos)

- [ ] **Modo avión activado** durante toda la defensa. Verificar antes de comenzar.
- [ ] Ningún `import` de modelos preentrenados (Whisper, Wav2Vec2, etc.). Comprobar con `grep -r "from transformers" src/`.
- [ ] Ningún llamado a APIs externas. Comprobar con `grep -r "requests.get\|httpx" src/inference/ src/audio/`.
- [ ] Modelos entrenados desde cero, sin pesos descargados. El primer commit del modelo debe ser pesos aleatorios; los siguientes muestran la convergencia.
- [ ] Repositorio público en GitHub al momento de la entrega (lunes 18 antes de medianoche).
- [ ] README con instrucciones de instalación verificadas en una máquina limpia.
- [ ] Modelos finales (`.pt`) en el repo o en un Drive enlazado desde el README.
- [ ] Video subido a YouTube/Drive y enlace verificado funcionando.
- [ ] Documento PDF con todos los diagramas obligatorios (arquitectura, flujo, secuencia, componentes).
- [ ] Matriz de confusión y métricas para ambos modelos.
- [ ] Tabla de latencias por etapa.
- [ ] Matriz de responsabilidades por integrante.
- [ ] Cada integrante puede explicar cualquier parte del código (no solo la suya).

---

## Apéndices

### A. Comandos rápidos

```bash
# Setup
conda env create -f environment.yml
conda activate voz-asistente

# Grabar corpus
python -m src.cli.record --speaker 03 --classes all

# Generar splits y augmentar
python scripts/generate_splits.py
python scripts/augment_offline.py

# Entrenar
python -m src.cli.train --config configs/training.yaml --model cnn
python -m src.cli.train --config configs/training.yaml --model lstm

# Evaluar
python -m src.cli.evaluate --model cnn --split test
python -m src.cli.evaluate --model lstm --split test

# Demo en vivo
python -m src.cli.live  # CLI puro
uvicorn src.api.main:app --port 8000  # con dashboard

# Tests
pytest tests/ -v
mypy src/
ruff check src/
```

### B. Variables de entorno

```env
# .env (gitignored)
ARDUINO_PORT=/dev/ttyUSB0          # o COM3 en Windows
ARDUINO_BAUDRATE=115200
MODEL_CNN_PATH=models/cnn_base/model.pt
MODEL_LSTM_PATH=models/bilstm/model.pt
CONFIDENCE_THRESHOLD=0.85
LOG_LEVEL=INFO
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=8000
```

### C. Estructura del README del repo

```markdown
# Asistente Robótico por Comandos de Voz
> Universidad Rafael Landívar · IA Primer Semestre 2026

## Demo
[Video de YouTube]

## Arquitectura
[Imagen del diagrama]

## Métricas
- CNN base: XX% accuracy, F1 macro 0.YY
- BiLSTM: XX% accuracy, F1 macro 0.YY
- Latencia end-to-end p95: XX ms

## Instalación
...

## Uso
...

## Estructura del proyecto
...

## Equipo
- [5 nombres con roles]
```

---

**Final del plan.** Cualquier desviación de este documento durante la implementación debe registrarse en un `CHANGELOG.md` para defenderla en oral.
