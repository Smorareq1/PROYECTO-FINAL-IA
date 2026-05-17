from __future__ import annotations

from typing import Literal

import torch
from torch.optim.lr_scheduler import CosineAnnealingLR, LRScheduler, OneCycleLR


SchedulerName = Literal["one_cycle", "cosine_annealing"]


def build_scheduler(
    name: SchedulerName,
    optimizer: torch.optim.Optimizer,
    *,
    total_steps: int | None = None,
    max_lr: float | None = None,
    epochs: int | None = None,
) -> LRScheduler:
    if name == "one_cycle":
        if total_steps is None or max_lr is None:
            raise ValueError("one_cycle requires total_steps and max_lr")
        return OneCycleLR(
            optimizer,
            max_lr=max_lr,
            total_steps=total_steps,
            pct_start=0.3,
            anneal_strategy="cos",
        )
    if name == "cosine_annealing":
        if epochs is None:
            raise ValueError("cosine_annealing requires epochs")
        return CosineAnnealingLR(optimizer, T_max=epochs)
    raise ValueError(f"Unknown scheduler: {name}")


def steps_per_batch(name: SchedulerName) -> bool:
    return name == "one_cycle"
