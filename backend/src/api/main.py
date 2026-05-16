from __future__ import annotations

import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import inference, manual, status
from src.api.state import app_state
from src.audio.features import MFCCExtractor
from src.domain.commands import ALL_CLASS_NAMES, N_CLASSES
from src.hardware.arduino_actuator import MockActuator
from src.inference.decision import DecisionLayer
from src.inference.pipeline import InferencePipeline
from src.inference.predictor import CNNPredictor
from src.models.factory import create_model
from src.utils.config_loader import load_yaml
from src.utils.logger import get_logger
from src.utils.seed import set_global_seed

logger = get_logger(__name__)

CONFIGS_DIR = Path(__file__).parent.parent.parent / "configs"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    set_global_seed(42)
    app_state.start_time = time.time()

    preproc_cfg = load_yaml(CONFIGS_DIR / "preprocessing.yaml")
    runtime_cfg = load_yaml(CONFIGS_DIR / "runtime.yaml")

    extractor = MFCCExtractor.from_config(preproc_cfg)

    cnn_model = create_model("cnn", n_classes=N_CLASSES, n_mfcc=13)

    cnn_path = Path("models/cnn_base/model.pt")
    if cnn_path.exists():
        cnn_model.load(cnn_path)
        app_state.cnn_path = str(cnn_path)

    cnn_predictor = CNNPredictor(cnn_model, ALL_CLASS_NAMES)

    inference_cfg = runtime_cfg.get("inference", {})
    decision = DecisionLayer(
        confidence_threshold=inference_cfg.get("confidence_threshold", 0.85),
    )

    actuator = MockActuator()
    app_state.actuator = actuator
    app_state.models_loaded = True

    pipeline = InferencePipeline(
        feature_extractor=extractor,
        cnn_predictor=cnn_predictor,
        decision=decision,
        actuator=actuator,
        broadcaster=app_state.ws_manager,
        buffer_duration=inference_cfg.get("buffer_duration_seconds", 3.0),
    )
    app_state.pipeline = pipeline

    logger.info("Application started. CNN: %d params", cnn_model.count_parameters())

    yield

    if app_state.pipeline:
        app_state.pipeline.stop()
    logger.info("Application shutdown")


app = FastAPI(
    title="Asistente Robotico - API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status.router)
app.include_router(inference.router)
app.include_router(manual.router)
