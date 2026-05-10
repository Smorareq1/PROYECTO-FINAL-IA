"""
Entry point for the live demo.

Usage:
    python -m src.cli.live                    # CLI-only mode (no dashboard)
    python -m src.cli.live --dashboard        # Start with FastAPI dashboard
    python -m src.cli.live --mock             # Use mock audio (no microphone)
    python -m src.cli.live --port COM3        # Specify Arduino port
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from src.audio.features import MFCCExtractor
from src.domain.commands import SIMPLE_CLASS_NAMES, COMPOUND_CLASS_NAMES
from src.hardware.arduino_actuator import ArduinoActuator, MockActuator
from src.hardware.serial_link import SerialLink, find_arduino_port
from src.inference.decision import DecisionLayer
from src.inference.pipeline import InferencePipeline
from src.inference.predictor import CNNPredictor, BiLSTMPredictor
from src.models.factory import create_model, load_model
from src.utils.config_loader import load_yaml
from src.utils.logger import get_logger
from src.utils.seed import set_global_seed

logger = get_logger(__name__)

CONFIGS_DIR = Path(__file__).parent.parent.parent / "configs"


def build_pipeline(
    arduino_port: str | None = None,
    cnn_path: str | None = None,
    lstm_path: str | None = None,
) -> InferencePipeline:
    set_global_seed(42)

    preproc_cfg = load_yaml(CONFIGS_DIR / "preprocessing.yaml")
    runtime_cfg = load_yaml(CONFIGS_DIR / "runtime.yaml")
    inference_cfg = runtime_cfg.get("inference", {})

    extractor = MFCCExtractor.from_config(preproc_cfg)

    cnn_path = cnn_path or "models/cnn_base/model.pt"
    lstm_path = lstm_path or "models/bilstm/model.pt"

    if Path(cnn_path).exists():
        cnn_model = load_model("cnn", cnn_path, n_classes=6, n_mfcc=13)
    else:
        logger.warning("CNN model not found at %s, using random weights", cnn_path)
        cnn_model = create_model("cnn", n_classes=6, n_mfcc=13)

    if Path(lstm_path).exists():
        lstm_model = load_model("bilstm", lstm_path, n_classes=4, n_mfcc=13)
    else:
        logger.warning("BiLSTM model not found at %s, using random weights", lstm_path)
        lstm_model = create_model("bilstm", n_classes=4, n_mfcc=13)

    cnn_predictor = CNNPredictor(cnn_model, SIMPLE_CLASS_NAMES)
    lstm_predictor = BiLSTMPredictor(lstm_model, COMPOUND_CLASS_NAMES)

    decision = DecisionLayer(
        confidence_threshold=inference_cfg.get("confidence_threshold", 0.85),
        compound_confidence_threshold=inference_cfg.get("compound_confidence_threshold", 0.80),
    )

    if arduino_port:
        port = arduino_port
    else:
        serial_cfg = runtime_cfg.get("serial", {})
        port_cfg = serial_cfg.get("port", "auto")
        port = find_arduino_port() if port_cfg == "auto" else port_cfg

    if port:
        try:
            link = SerialLink(port, baudrate=runtime_cfg.get("serial", {}).get("baudrate", 115200))
            link.open()
            actuator = ArduinoActuator(link)
            logger.info("Arduino connected on %s", port)
        except Exception as e:
            logger.warning("Could not connect to Arduino on %s: %s. Using mock.", port, e)
            actuator = MockActuator()
    else:
        logger.info("No Arduino detected, using mock actuator")
        actuator = MockActuator()

    pipeline = InferencePipeline(
        feature_extractor=extractor,
        cnn_predictor=cnn_predictor,
        lstm_predictor=lstm_predictor,
        decision=decision,
        actuator=actuator,
        buffer_duration=inference_cfg.get("buffer_duration_seconds", 3.0),
    )

    return pipeline


def run_mock_demo(pipeline: InferencePipeline, mock_dir: str = "data/raw_mock") -> None:
    mock_path = Path(mock_dir)
    if not mock_path.exists():
        logger.error("Mock data not found at %s. Run generate_mock_corpus.py first.", mock_dir)
        sys.exit(1)

    wav_files = sorted(mock_path.rglob("*.wav"))
    logger.info("Found %d mock audio files", len(wav_files))

    for wav_file in wav_files[:20]:
        audio, sr = sf.read(wav_file)
        audio = audio.astype(np.float32)

        pipeline.push_audio(audio)
        result = pipeline.process_buffer()

        expected_class = wav_file.parent.name
        logger.info(
            "[%s] expected=%s  predicted=%s  confidence=%.1f%%  latency=%.1f ms  %s",
            wav_file.name,
            expected_class,
            result["command"],
            result["confidence"] * 100,
            result["latency_ms"],
            "REJECTED" if result["rejected"] else "OK",
        )
        time.sleep(0.1)


def run_dashboard(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn
    logger.info("Starting dashboard on http://%s:%d", host, port)
    uvicorn.run("src.api.main:app", host=host, port=port, reload=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Live demo del Asistente Robotico")
    parser.add_argument("--dashboard", action="store_true", help="Start with FastAPI dashboard")
    parser.add_argument("--mock", action="store_true", help="Use mock audio files instead of microphone")
    parser.add_argument("--mock-dir", default="data/raw_mock", help="Directory with mock WAV files")
    parser.add_argument("--port", type=str, default=None, help="Arduino serial port (e.g., COM3)")
    parser.add_argument("--cnn-model", type=str, default=None, help="Path to CNN model .pt file")
    parser.add_argument("--lstm-model", type=str, default=None, help="Path to BiLSTM model .pt file")
    parser.add_argument("--host", default="127.0.0.1", help="Dashboard host")
    parser.add_argument("--http-port", type=int, default=8000, help="Dashboard port")

    args = parser.parse_args()

    if args.dashboard:
        run_dashboard(args.host, args.http_port)
    elif args.mock:
        pipeline = build_pipeline(args.port, args.cnn_model, args.lstm_model)
        run_mock_demo(pipeline, args.mock_dir)
    else:
        logger.info("Use --dashboard for web UI or --mock for mock audio demo")
        logger.info("Microphone capture not yet implemented (waiting for sounddevice integration)")
        pipeline = build_pipeline(args.port, args.cnn_model, args.lstm_model)
        run_mock_demo(pipeline, args.mock_dir)


if __name__ == "__main__":
    main()
