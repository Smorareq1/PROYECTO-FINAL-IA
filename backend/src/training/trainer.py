from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from src.training.callbacks import Callback
from src.training.metrics import compute_metrics
from src.utils.logger import get_logger

logger = get_logger(__name__)

InputAdapter = Callable[[torch.Tensor], torch.Tensor]


@dataclass
class TrainerConfig:
    epochs: int = 60
    gradient_clip_norm: float = 1.0
    log_every_n_steps: int = 20
    scheduler_step_per_batch: bool = True
    mixup_alpha: float = 0.0
    mixup_prob: float = 0.5
    selection_metric: str = "val_f1_macro"
    device: str = "cpu"
    pin_memory: bool = False


@dataclass
class TrainerHistory:
    entries: list[dict] = field(default_factory=list)

    def append(self, entry: dict) -> None:
        self.entries.append(entry)

    def to_list(self) -> list[dict]:
        return list(self.entries)


def _mixup_batch(
    x: torch.Tensor,
    y: torch.Tensor,
    alpha: float,
    rng: np.random.Generator,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, float]:
    if alpha <= 0:
        return x, y, y, 1.0
    lam = float(rng.beta(alpha, alpha))
    idx = torch.randperm(x.size(0), device=x.device)
    x_mix = lam * x + (1.0 - lam) * x[idx]
    return x_mix, y, y[idx], lam


class Trainer:
    def __init__(
        self,
        model: nn.Module,
        input_adapter: InputAdapter,
        train_loader: DataLoader,
        val_loader: DataLoader,
        loss_fn: nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: torch.optim.lr_scheduler.LRScheduler | None,
        callbacks: list[Callback],
        class_names: list[str],
        config: TrainerConfig,
        seed: int = 42,
    ) -> None:
        self.model = model
        self.input_adapter = input_adapter
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.loss_fn = loss_fn
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.callbacks = list(callbacks)
        self.class_names = list(class_names)
        self.cfg = config
        self.device = torch.device(config.device)
        self.model.to(self.device)
        self._rng = np.random.default_rng(seed)

    def _move(self, t: torch.Tensor) -> torch.Tensor:
        return t.to(self.device, non_blocking=self.cfg.pin_memory)

    def _train_one_epoch(self, epoch: int) -> dict:
        self.model.train()
        loss_sum = 0.0
        n_samples = 0
        n_correct = 0

        for batch_idx, (x, y) in enumerate(self.train_loader):
            x = self._move(x)
            y = self._move(y)

            use_mixup = (
                self.cfg.mixup_alpha > 0.0
                and float(self._rng.random()) < self.cfg.mixup_prob
            )

            self.optimizer.zero_grad(set_to_none=True)

            if use_mixup:
                x_mix, y_a, y_b, lam = _mixup_batch(x, y, self.cfg.mixup_alpha, self._rng)
                logits = self.model(self.input_adapter(x_mix))
                loss = lam * self.loss_fn(logits, y_a) + (1.0 - lam) * self.loss_fn(logits, y_b)
            else:
                logits = self.model(self.input_adapter(x))
                loss = self.loss_fn(logits, y)

            loss.backward()
            if self.cfg.gradient_clip_norm and self.cfg.gradient_clip_norm > 0:
                nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.gradient_clip_norm)
            self.optimizer.step()
            if self.scheduler is not None and self.cfg.scheduler_step_per_batch:
                self.scheduler.step()

            bs = y.size(0)
            loss_sum += float(loss.detach()) * bs
            n_samples += bs
            with torch.no_grad():
                preds = logits.argmax(dim=1)
                n_correct += int((preds == y).sum().item())

            if self.cfg.log_every_n_steps and (batch_idx + 1) % self.cfg.log_every_n_steps == 0:
                logger.info(
                    "epoch %d step %d/%d loss=%.4f",
                    epoch, batch_idx + 1, len(self.train_loader), float(loss.detach()),
                )

        if self.scheduler is not None and not self.cfg.scheduler_step_per_batch:
            self.scheduler.step()

        return {
            "train_loss": loss_sum / max(n_samples, 1),
            "train_accuracy": n_correct / max(n_samples, 1),
        }

    @torch.no_grad()
    def validate(self) -> dict:
        self.model.eval()
        loss_sum = 0.0
        n_samples = 0
        all_true: list[np.ndarray] = []
        all_pred: list[np.ndarray] = []

        for x, y in self.val_loader:
            x = self._move(x)
            y = self._move(y)
            logits = self.model(self.input_adapter(x))
            loss = self.loss_fn(logits, y)
            bs = y.size(0)
            loss_sum += float(loss.detach()) * bs
            n_samples += bs
            preds = logits.argmax(dim=1)
            all_true.append(y.detach().cpu().numpy())
            all_pred.append(preds.detach().cpu().numpy())

        y_true = np.concatenate(all_true) if all_true else np.array([], dtype=np.int64)
        y_pred = np.concatenate(all_pred) if all_pred else np.array([], dtype=np.int64)
        m = compute_metrics(y_true, y_pred, y_proba=None, class_names=self.class_names)
        return {
            "val_loss": loss_sum / max(n_samples, 1),
            "val_accuracy": m["accuracy"],
            "val_f1_macro": m["f1_macro"],
            "val_f1_micro": m["f1_micro"],
        }

    def fit(self) -> TrainerHistory:
        history = TrainerHistory()
        for epoch in range(1, self.cfg.epochs + 1):
            train_m = self._train_one_epoch(epoch)
            val_m = self.validate()
            entry = {"epoch": epoch, **train_m, **val_m, "lr": self.optimizer.param_groups[0]["lr"]}
            history.append(entry)
            logger.info(
                "epoch %d/%d | train_loss=%.4f train_acc=%.4f | val_loss=%.4f val_acc=%.4f val_f1=%.4f",
                epoch, self.cfg.epochs,
                entry["train_loss"], entry["train_accuracy"],
                entry["val_loss"], entry["val_accuracy"], entry["val_f1_macro"],
            )

            stop = False
            metric_value = entry.get(self.cfg.selection_metric)
            if metric_value is None:
                raise KeyError(f"selection_metric {self.cfg.selection_metric!r} not in entry")
            for cb in self.callbacks:
                if cb.step(model=self.model, metric=float(metric_value), epoch=epoch):
                    stop = True
            if stop:
                logger.info("Stopping at epoch %d", epoch)
                break
        return history
