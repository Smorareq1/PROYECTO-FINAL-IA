"""Entry point para la demo en vivo.

Modos:
    python -m src.cli.live                     # captura por microfono (default)
    python -m src.cli.live --dashboard         # dashboard FastAPI
    python -m src.cli.live --mock              # corre con corpus sintetico
    python -m src.cli.live --port COM3         # puerto Arduino explicito
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from src.audio.capture import MicrophoneCapture
from src.audio.features import MFCCExtractor
from src.audio.vad import StreamingVADGate
from src.domain.commands import ALL_CLASS_NAMES, N_CLASSES
from src.hardware.arduino_actuator import ArduinoActuator, MockActuator
from src.hardware.serial_link import SerialLink, find_arduino_port
from src.inference.decision import DecisionLayer
from src.inference.pipeline import InferencePipeline
from src.inference.predictor import CNNPredictor
from src.models.factory import create_model, load_model
from src.utils.config_loader import load_yaml
from src.utils.logger import get_logger
from src.utils.seed import set_global_seed

logger = get_logger(__name__)

CONFIGS_DIR = Path(__file__).parent.parent.parent / "configs"


def build_pipeline(
    arduino_port: str | None = None,
    cnn_path: str | None = None,
    enable_noise_suppression: bool = False,
) -> InferencePipeline:
    set_global_seed(42)

    preproc_cfg = load_yaml(CONFIGS_DIR / "preprocessing.yaml")
    runtime_cfg = load_yaml(CONFIGS_DIR / "runtime.yaml")
    inference_cfg = runtime_cfg.get("inference", {})

    extractor = MFCCExtractor.from_config(preproc_cfg)

    cnn_path = cnn_path or "models/cnn_base/model.pt"

    if Path(cnn_path).exists():
        cnn_model = load_model("cnn", cnn_path, n_classes=N_CLASSES, n_mfcc=13)
    else:
        logger.warning("CNN model not found at %s, using random weights", cnn_path)
        cnn_model = create_model("cnn", n_classes=N_CLASSES, n_mfcc=13)

    cnn_predictor = CNNPredictor(cnn_model, ALL_CLASS_NAMES)

    decision = DecisionLayer(
        confidence_threshold=inference_cfg.get("confidence_threshold", 0.85),
    )

    if arduino_port:
        port = arduino_port
    else:
        serial_cfg = runtime_cfg.get("serial", {})
        port_cfg = serial_cfg.get("port", "auto")
        port = find_arduino_port() if port_cfg == "auto" else port_cfg

    actuator: ArduinoActuator | MockActuator
    if port:
        try:
            link = SerialLink(
                port,
                baudrate=runtime_cfg.get("serial", {}).get("baudrate", 115200),
            )
            link.open()
            actuator = ArduinoActuator(link)
            logger.info("Arduino conectado en %s", port)
        except Exception as e:
            logger.warning("No se pudo conectar al Arduino en %s: %s. Usando mock.", port, e)
            actuator = MockActuator()
    else:
        logger.info("Sin Arduino detectado; usando mock actuator")
        actuator = MockActuator()

    pipeline = InferencePipeline(
        feature_extractor=extractor,
        cnn_predictor=cnn_predictor,
        decision=decision,
        actuator=actuator,
        buffer_duration=inference_cfg.get("buffer_duration_seconds", 3.0),
        enable_noise_suppression=enable_noise_suppression,
    )

    return pipeline


def run_mock_demo(pipeline: InferencePipeline, mock_dir: str = "data/raw_mock") -> None:
    mock_path = Path(mock_dir)
    if not mock_path.exists():
        logger.error(
            "Mock data no encontrado en %s. Corre primero generate_mock_corpus.py.", mock_dir
        )
        sys.exit(1)

    wav_files = sorted(mock_path.rglob("*.wav"))
    logger.info("Encontrados %d clips mock", len(wav_files))

    for wav_file in wav_files[:20]:
        audio, _sr = sf.read(wav_file)
        audio = audio.astype(np.float32)

        pipeline.push_audio(audio)
        result = pipeline.process_buffer()

        expected_class = wav_file.parent.name
        logger.info(
            "[%s] esperado=%s  predicho=%s  conf=%.1f%%  lat=%.1f ms  %s",
            wav_file.name,
            expected_class,
            result.get("command", "?"),
            result.get("confidence", 0.0) * 100,
            result.get("latency_ms", 0.0),
            "REJECTED" if result.get("rejected") else "OK",
        )
        time.sleep(0.05)


def run_live_demo(
    pipeline: InferencePipeline,
    mic_device: int | str | None = None,
    calibration_s: float = 1.0,
    window_seconds: float = 2.0,
    chunk_ms: int = 32,
) -> None:
    sr = 16_000
    mic = MicrophoneCapture(sample_rate=sr, chunk_ms=chunk_ms, device=mic_device)
    vad_gate = StreamingVADGate(sr=sr, silence_ms=250, min_speech_ms=300, frame_ms=25)

    logger.info(
        "Iniciando demo en vivo. Calibrando ruido ambiente por %.1f s — silencio por favor.",
        calibration_s,
    )
    with mic:
        time.sleep(calibration_s + 0.2)
        ambient = mic.drain()
        if ambient.size > 0:
            vad_gate.calibrate(ambient)
            pipeline.set_noise_profile(ambient[-sr:] if ambient.size > sr else ambient)
            logger.info("Piso de ruido calibrado (noise_floor=%.2e)", vad_gate.noise_floor)
        else:
            logger.warning("Sin audio durante calibracion; usando defaults")

        logger.info("Listo. Hablá un comando. Ctrl+C para salir.")
        pipeline.start()
        try:
            for chunk in mic.chunks(timeout=1.0):
                pipeline.push_audio(chunk)
                if vad_gate.process_chunk(chunk):
                    result = pipeline.process_buffer(window_seconds=window_seconds)
                    cmd = result.get("command", "?")
                    conf = result.get("confidence", 0.0)
                    lat = result.get("latency_ms", 0.0)
                    snr = result.get("snr_db", 0.0)
                    tag = result.get("reason", "OK") if result.get("rejected") else "OK"
                    print(
                        f"  -> {cmd:<18} conf={conf*100:5.1f}%  snr={snr:5.1f} dB  "
                        f"lat={lat:6.1f} ms  [{tag}]"
                    )
        except KeyboardInterrupt:
            logger.info("Demo finalizada por el usuario.")
        finally:
            pipeline.stop()


def run_dashboard(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    logger.info("Iniciando dashboard en http://%s:%d", host, port)
    uvicorn.run("src.api.main:app", host=host, port=port, reload=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo en vivo del Asistente Robotico")
    parser.add_argument("--dashboard", action="store_true", help="Lanza el dashboard FastAPI")
    parser.add_argument("--mock", action="store_true", help="Usa corpus sintetico en vez de microfono")
    parser.add_argument("--mock-dir", default="data/raw_mock", help="Directorio del corpus mock")
    parser.add_argument("--port", type=str, default=None, help="Puerto Arduino (ej. COM3, /dev/ttyUSB0)")
    parser.add_argument("--cnn-model", type=str, default=None, help="Ruta del .pt de la CNN")
    parser.add_argument("--host", default="127.0.0.1", help="Host del dashboard")
    parser.add_argument("--http-port", type=int, default=8000, help="Puerto del dashboard")
    parser.add_argument("--mic", type=str, default=None, help="ID/nombre del microfono (sounddevice)")
    parser.add_argument("--calibration-s", type=float, default=1.0)
    parser.add_argument("--window-s", type=float, default=2.0, help="Ventana enviada al modelo")
    parser.add_argument("--chunk-ms", type=int, default=32)
    parser.add_argument(
        "--noise-suppression",
        action="store_true",
        help="Activa noisereduce (requiere paquete instalado)",
    )

    args = parser.parse_args()

    if args.dashboard:
        run_dashboard(args.host, args.http_port)
        return

    pipeline = build_pipeline(
        args.port,
        args.cnn_model,
        enable_noise_suppression=args.noise_suppression,
    )

    if args.mock:
        run_mock_demo(pipeline, args.mock_dir)
        return

    mic_device: int | str | None = args.mic
    if mic_device is not None and mic_device.isdigit():
        mic_device = int(mic_device)
    run_live_demo(
        pipeline,
        mic_device=mic_device,
        calibration_s=args.calibration_s,
        window_seconds=args.window_s,
        chunk_ms=args.chunk_ms,
    )


if __name__ == "__main__":
    main()
