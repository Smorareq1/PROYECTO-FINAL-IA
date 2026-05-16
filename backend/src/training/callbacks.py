from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol

import torch
import torch.nn as nn

from src.utils.logger import get_logger

logger = get_logger(__name__)


class Callback(Protocol):
    def step(
        self,
        *,
        model: nn.Module,
        metric: float,
        epoch: int,
    ) -> bool: ...


class EarlyStopping:
    def __init__(
        self,
        patience: int = 10,
        mode: Literal["min", "max"] = "min",
        min_delta: float = 1e-4,
    ) -> None:
        self.patience = patience
        self.mode = mode
        self.min_delta = min_delta
        self._best: float | None = None
        self._bad_epochs = 0

    def _is_better(self, current: float) -> bool:
        if self._best is None:
            return True
        if self.mode == "min":
            return current < self._best - self.min_delta
        return current > self._best + self.min_delta

    def step(self, *, model: nn.Module, metric: float, epoch: int) -> bool:
        del model, epoch
        if self._is_better(metric):
            self._best = metric
            self._bad_epochs = 0
            return False
        self._bad_epochs += 1
        if self._bad_epochs >= self.patience:
            logger.info("EarlyStopping: no improvement for %d epochs", self.patience)
            return True
        return False


class ModelCheckpoint:
    def __init__(
        self,
        dir_path: Path,
        monitor: str = "val_f1_macro",
        mode: Literal["min", "max"] = "max",
        filename: str = "model.pt",
    ) -> None:
        self.dir_path = Path(dir_path)
        self.dir_path.mkdir(parents=True, exist_ok=True)
        self.monitor = monitor
        self.mode = mode
        self.path = self.dir_path / filename
        self._best: float | None = None
        self.best_epoch: int = -1

    def _is_better(self, current: float) -> bool:
        if self._best is None:
            return True
        return current > self._best if self.mode == "max" else current < self._best

    def step(self, *, model: nn.Module, metric: float, epoch: int) -> bool:
        if self._is_better(metric):
            self._best = metric
            self.best_epoch = epoch
            torch.save(model.state_dict(), self.path)
            logger.info(
                "ModelCheckpoint: %s=%.4f at epoch %d -> %s",
                self.monitor, metric, epoch, self.path,
            )
        return False

    @property
    def best_metric(self) -> float | None:
        return self._best
