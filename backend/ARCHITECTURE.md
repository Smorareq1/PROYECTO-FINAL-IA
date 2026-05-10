# Arquitectura Backend — Asistente Robotico por Comandos de Voz

## Stack Tecnologico

| Tecnologia | Version | Proposito |
|---|---|---|
| Python | 3.11 | Lenguaje principal |
| PyTorch | 2.3.0 | Framework de deep learning (CNN 2D + BiLSTM) |
| torchaudio | 2.3.0 | Extraccion MFCC como capa de red |
| FastAPI | 0.110.0 | API REST + WebSocket para el dashboard |
| uvicorn | 0.29.0 | Servidor ASGI |
| pyserial | 3.5 | Comunicacion serial con Arduino UNO |
| sounddevice | 0.4.6 | Captura de audio en tiempo real |
| numpy | 1.26.4 | Operaciones numericas |
| scipy | 1.13.0 | Procesamiento de senales |
| scikit-learn | 1.4.2 | Metricas y splits estratificados |
| librosa | 0.10.2 | Data augmentation (pitch shifting) |
| pydantic | 2.6.4 | Validacion de configuracion y schemas |
| pyyaml | 6.0.1 | Carga de archivos de configuracion |
| websockets | 12.0 | Soporte WebSocket nativo |
| jinja2 | 3.1.3 | Templates HTML para dashboard fallback |
| matplotlib | 3.8.4 | Generacion de graficas en notebooks |
| seaborn | 0.13.2 | Matrices de confusion y heatmaps |
| pytest | 8.1.1 | Tests unitarios |
| mypy | 1.10.0 | Type checking estricto |
| black | 24.4.0 | Formateo de codigo |
| ruff | 0.4.1 | Linter rapido |

## Estructura de Carpetas

```
backend/
├── pyproject.toml
├── requirements.txt
├── environment.yml
├── .python-version                     # 3.11
│
├── configs/
│   ├── data.yaml                       # Rutas, tasas de muestreo, splits
│   ├── preprocessing.yaml              # Parametros MFCC, VAD, augmentation
│   ├── model_cnn.yaml                  # Arquitectura CNN base
│   ├── model_lstm.yaml                 # Arquitectura BiLSTM
│   ├── training.yaml                   # Hiperparametros, epochs, optimizer
│   └── runtime.yaml                    # Puerto serial, baudios, umbrales
│
├── data/
│   ├── raw/                            # Grabaciones originales sin procesar
│   │   ├── enciende/
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
│   ├── augmented/                      # Despues del data augmentation
│   ├── splits/                         # train.csv, val.csv, test.csv
│   └── speakers.csv                    # Metadata de hablantes
│
├── models/
│   ├── cnn_base/
│   │   ├── model.pt
│   │   ├── config.yaml
│   │   ├── metrics.json
│   │   └── confusion_matrix.png
│   └── bilstm/
│       ├── model.pt
│       ├── config.yaml
│       ├── metrics.json
│       └── confusion_matrix.png
│
├── src/
│   ├── __init__.py
│   │
│   ├── domain/                         # Logica de negocio pura
│   │   ├── __init__.py
│   │   ├── commands.py                 # Enum Command (ENCIENDE, APAGA...)
│   │   ├── prediction.py               # Dataclass Prediction (label, confidence)
│   │   ├── exceptions.py               # Excepciones de dominio
│   │   └── interfaces.py               # Protocols (Predictor, Actuator)
│   │
│   ├── audio/                          # Capa de audio
│   │   ├── __init__.py
│   │   ├── capture.py                  # Captura desde sounddevice
│   │   ├── buffer.py                   # Buffer circular
│   │   ├── vad.py                      # Voice Activity Detection
│   │   ├── normalization.py            # Normalizacion de amplitud
│   │   ├── features.py                 # MFCC con torchaudio
│   │   └── augmentation.py             # 5 tecnicas de data augmentation
│   │
│   ├── models/                         # Arquitecturas de red
│   │   ├── __init__.py
│   │   ├── base.py                     # Clase BaseModel abstracta
│   │   ├── cnn.py                      # CNN2DCommandClassifier
│   │   ├── lstm.py                     # BiLSTMSequentialClassifier
│   │   └── factory.py                  # Builder segun config
│   │
│   ├── training/                       # Entrenamiento
│   │   ├── __init__.py
│   │   ├── dataset.py                  # CommandDataset (PyTorch)
│   │   ├── dataloader.py               # Splits estratificados
│   │   ├── trainer.py                  # Bucle de entrenamiento
│   │   ├── callbacks.py                # EarlyStopping, ModelCheckpoint
│   │   ├── metrics.py                  # Accuracy, F1, matriz de confusion
│   │   └── scheduler.py                # OneCycleLR
│   │
│   ├── inference/                      # Inferencia en tiempo real
│   │   ├── __init__.py
│   │   ├── pipeline.py                 # InferencePipeline (orquestador)
│   │   ├── predictor.py                # Wrappa los modelos cargados
│   │   ├── decision.py                 # Logica de umbrales y rechazo
│   │   └── benchmark.py                # Medidor de latencia
│   │
│   ├── hardware/                       # Control del Arduino
│   │   ├── __init__.py
│   │   ├── serial_link.py              # Wrapper de pyserial
│   │   ├── command_protocol.py         # Mapeo Comando -> byte
│   │   └── arduino_actuator.py         # Implementa Actuator
│   │
│   ├── api/                            # FastAPI (API REST + WebSocket)
│   │   ├── __init__.py
│   │   ├── main.py                     # App FastAPI
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── status.py               # GET /api/status
│   │   │   ├── inference.py            # WS /ws/inference
│   │   │   └── manual.py               # POST /api/command/{cmd}
│   │   ├── websocket.py                # Manager de conexiones WS
│   │   └── schemas.py                  # Pydantic models
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── seed.py                     # Setea semillas reproducibles
│   │   ├── logger.py                   # Logging estructurado
│   │   ├── config_loader.py            # Carga YAML con Pydantic
│   │   └── timer.py                    # Context manager para latencias
│   │
│   └── cli/
│       ├── __init__.py
│       ├── record.py                   # python -m src.cli.record
│       ├── train.py                    # python -m src.cli.train
│       ├── evaluate.py                 # python -m src.cli.evaluate
│       └── live.py                     # python -m src.cli.live (demo)
│
├── notebooks/
│   ├── 01_exploracion_corpus.ipynb
│   ├── 02_pipeline_preprocesamiento.ipynb
│   ├── 03_visualizacion_mfcc.ipynb
│   ├── 04_entrenamiento_cnn.ipynb
│   ├── 05_entrenamiento_lstm.ipynb
│   ├── 06_evaluacion_metricas.ipynb
│   ├── 07_data_augmentation.ipynb
│   ├── 08_analisis_latencia.ipynb
│   └── 09_comparativa_modelos.ipynb
│
├── tests/
│   ├── __init__.py
│   ├── test_audio_features.py
│   ├── test_vad.py
│   ├── test_command_protocol.py
│   ├── test_decision.py
│   └── fixtures/
│       └── sample.wav
│
├── scripts/
│   ├── generate_splits.py
│   ├── augment_offline.py
│   ├── export_metrics_pdf.py
│   └── verify_offline.py
│
├── Dockerfile
└── .dockerignore
```

## Reglas de Arquitectura

### 1. Separacion estricta de capas (Clean Architecture)

- **`domain/` no importa nada externo**: ni PyTorch, ni audio, ni FastAPI. Solo contiene dataclasses, enums y protocolos (typing.Protocol). Es el nucleo inmutable del sistema.
- **`audio/`, `models/`, `hardware/` dependen de `domain/`** pero NUNCA entre si. El `Predictor` recibe un `Command` del dominio sin saber que hardware lo ejecutara.
- **`inference/` orquesta**: llama a `audio/`, `models/` y `hardware/`. Aqui esta la logica de negocio aplicada.
- **`api/` y `cli/` son fachadas**: solo construyen objetos de `inference/` y exponen entradas. No contienen logica de negocio.

### 2. Inversion de dependencias

Las capas externas dependen de interfaces definidas en `domain/interfaces.py` (Protocols), nunca de implementaciones concretas. Esto permite:
- Testear la pipeline sin Arduino conectado (mock del `Actuator`).
- Cambiar la implementacion de hardware sin tocar la logica de inferencia.

### 3. Reproducibilidad obligatoria

- Semilla fija en NumPy, PyTorch y Python random en todo entrenamiento.
- Determinismo activado en CUDA donde sea posible.
- Cada experimento se loggea con su `config.yaml` asociado.

### 4. Type hints estrictos

- `mypy --strict` debe pasar en todo el codigo de `src/`.
- Facilita la auditoria del codigo durante la defensa oral.

### 5. No modelos preentrenados

- Cada `nn.Module` se inicializa con pesos aleatorios.
- Prohibido importar desde `transformers`, `huggingface_hub`, o cualquier fuente de pesos preentrenados.
- Verificable con: `grep -r "from transformers" src/`

### 6. No internet en runtime

- Toda dependencia precargada en `models/` antes de la demo.
- Modo avion obligatorio durante la defensa.
- Verificar con: `grep -r "requests.get\|httpx" src/inference/ src/audio/`

### 7. Notebooks importan de src/, nunca redefinen

- Los notebooks usan `%load_ext autoreload` + `%autoreload 2`.
- Cada notebook fija semilla en su segunda celda.
- Toda logica reutilizable vive en `src/`, los notebooks solo la invocan.

### 8. Tests unitarios en funciones criticas

- Extraccion MFCC, VAD, parseo de protocolo serial, logica de decision.
- `pytest tests/ -v` debe pasar al 100%.

## Endpoints de la API

| Metodo | Ruta | Descripcion |
|---|---|---|
| GET | `/` | Dashboard HTML (servido al frontend o como fallback) |
| GET | `/api/status` | Estado del sistema (Arduino, modelos cargados) |
| WS | `/ws/inference` | Stream en vivo de predicciones |
| POST | `/api/command/{cmd}` | Envio manual de comando al Arduino |
| GET | `/api/metrics` | Metricas agregadas (predicciones, latencias) |
| GET | `/api/health` | Healthcheck (modo avion, GPU, modelos) |

## Protocolo Serial Arduino

| Byte (hex) | Comando | Accion |
|---|---|---|
| `0x01` | ENCIENDE | Cierra rele |
| `0x02` | APAGA | Abre rele |
| `0x03` | IZQUIERDA | Motor pasos: 512 antihorario |
| `0x04` | DERECHA | Motor pasos: 512 horario |
| `0x05` | DETENTE | Beep 200 ms y todo apagado |
| `0x10` | ENCIENDE_RAPIDO | Rele ON + LED RGB blanco |
| `0x11` | ENCIENDE_LENTO | Rele ON + LED RGB azul tenue |
| `0x12` | GIRA_IZQUIERDA | Motor: 1024 antihorario |
| `0x13` | GIRA_DERECHA | Motor: 1024 horario |
| `0xFE` | HEARTBEAT | Verificacion de conexion |
| `0xFF` | RESET | Estado inicial |
