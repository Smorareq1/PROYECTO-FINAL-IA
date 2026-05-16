from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from src.audio.features import MFCCExtractor
from src.training.dataset import CommandDataset
from src.utils.logger import get_logger

logger = get_logger(__name__)

CLASS_WEIGHT_IMBALANCE_THRESHOLD = 1.5


def _compute_class_weights(labels: list[int], n_classes: int) -> list[float] | None:
    counts = Counter(labels)
    if len(counts) < n_classes or min(counts.values()) == 0:
        per_class = [counts.get(i, 0) for i in range(n_classes)]
        logger.warning("Some classes are empty in train split: %s", per_class)
    counts_arr = np.array([max(counts.get(i, 0), 1) for i in range(n_classes)], dtype=np.float64)
    ratio = counts_arr.max() / counts_arr.min()
    if ratio < CLASS_WEIGHT_IMBALANCE_THRESHOLD:
        logger.info("Class imbalance ratio %.2f < %.2f; skipping weights", ratio, CLASS_WEIGHT_IMBALANCE_THRESHOLD)
        return None
    total = counts_arr.sum()
    weights = total / (n_classes * counts_arr)
    weights = weights / weights.mean()
    logger.info("Class weights (ratio %.2f): %s", ratio, [round(float(w), 3) for w in weights])
    return [float(w) for w in weights]


def _seed_worker(worker_id: int) -> None:
    seed = (torch.initial_seed() + worker_id) % (2**32)
    np.random.seed(seed)


def make_dataloaders(
    data_root: Path,
    splits_dir: Path,
    extractor: MFCCExtractor,
    *,
    batch_size: int = 32,
    num_workers: int = 0,
    include_augmented_train: bool = True,
    augmented_dir: Path | None = None,
    pin_memory: bool = False,
    sample_rate: int = 16_000,
    target_duration_s: float = 2.0,
    spec_augment_kwargs: dict | None = None,
    cache_in_memory: bool = True,
) -> tuple[DataLoader, DataLoader, DataLoader, list[float] | None]:
    splits_dir = Path(splits_dir)
    data_root = Path(data_root)
    aug_kwargs = spec_augment_kwargs or {}

    train_ds = CommandDataset(
        split_csv=splits_dir / "train.csv",
        data_root=data_root,
        extractor=extractor,
        sample_rate=sample_rate,
        target_duration_s=target_duration_s,
        is_train=True,
        include_augmented=include_augmented_train,
        augmented_dir=augmented_dir,
        cache_in_memory=cache_in_memory,
        **aug_kwargs,
    )
    val_ds = CommandDataset(
        split_csv=splits_dir / "val.csv",
        data_root=data_root,
        extractor=extractor,
        sample_rate=sample_rate,
        target_duration_s=target_duration_s,
        is_train=False,
        include_augmented=False,
        cache_in_memory=cache_in_memory,
    )
    test_ds = CommandDataset(
        split_csv=splits_dir / "test.csv",
        data_root=data_root,
        extractor=extractor,
        sample_rate=sample_rate,
        target_duration_s=target_duration_s,
        is_train=False,
        include_augmented=False,
        cache_in_memory=cache_in_memory,
    )

    class_weights = _compute_class_weights(train_ds.labels, len(train_ds.class_names))

    loader_kwargs = dict(
        num_workers=num_workers,
        pin_memory=pin_memory,
        worker_init_fn=_seed_worker if num_workers > 0 else None,
        persistent_workers=num_workers > 0,
    )

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=False, **loader_kwargs)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, drop_last=False, **loader_kwargs)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, drop_last=False, **loader_kwargs)

    return train_loader, val_loader, test_loader, class_weights
