from __future__ import annotations

from pathlib import Path
from typing import Any

from src.domain.exceptions import ModelLoadError
from src.models.base import BaseModel
from src.models.cnn import CNN2DCommandClassifier
from src.models.lstm import BiLSTMSequentialClassifier
from src.utils.logger import get_logger

logger = get_logger(__name__)

_REGISTRY: dict[str, type[BaseModel]] = {
    "cnn": CNN2DCommandClassifier,
    "CNN2DCommandClassifier": CNN2DCommandClassifier,
    "lstm": BiLSTMSequentialClassifier,
    "bilstm": BiLSTMSequentialClassifier,
    "BiLSTMSequentialClassifier": BiLSTMSequentialClassifier,
}


def create_model(name: str, **kwargs: Any) -> BaseModel:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ModelLoadError(f"Unknown model: {name}. Available: {list(_REGISTRY.keys())}")
    model = cls(**kwargs)
    logger.info("Created %s with %d parameters", name, model.count_parameters())
    return model


def load_model(name: str, path: str | Path, device: str = "cpu", **kwargs: Any) -> BaseModel:
    path = Path(path)
    if not path.exists():
        raise ModelLoadError(f"Model file not found: {path}")
    model = create_model(name, **kwargs)
    model.load(path, device=device)
    logger.info("Loaded %s from %s", name, path)
    return model
