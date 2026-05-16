from __future__ import annotations

from pathlib import Path

import torch
import torch.nn.functional as F

from src.domain.commands import ALL_CLASS_NAMES, Command, N_CLASSES
from src.domain.prediction import ModelOutput
from src.models.base import BaseModel
from src.models.factory import load_model
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CNNPredictor:
    def __init__(self, model: BaseModel, class_names: list[str], device: str = "cpu") -> None:
        self._model = model.to(device)
        self._model.eval()
        self._class_names = class_names
        self._device = device

    @staticmethod
    def from_checkpoint(
        path: str | Path,
        n_classes: int = N_CLASSES,
        device: str = "cpu",
    ) -> CNNPredictor:
        model = load_model("cnn", path, device=device, n_classes=n_classes, n_mfcc=13)
        return CNNPredictor(model, ALL_CLASS_NAMES, device)

    def predict(self, mfcc: torch.Tensor) -> ModelOutput:
        # mfcc: (n_mfcc, time) or (batch, n_mfcc, time)
        with torch.no_grad():
            if mfcc.dim() == 2:
                mfcc = mfcc.unsqueeze(0)
            x = mfcc.unsqueeze(1).to(self._device)  # (batch, 1, n_mfcc, time)
            logits = self._model(x)
            probs = F.softmax(logits, dim=1)
            confidence, idx = torch.max(probs, dim=1)

            label_str = self._class_names[idx.item()]
            return ModelOutput(
                label=Command(label_str),
                confidence=float(confidence.item()),
                logits=logits.squeeze(0).tolist(),
            )
