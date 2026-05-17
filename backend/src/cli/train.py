"""Entrena CNN o BiLSTM sobre el vocabulario plano de 13 clases.

Uso:
    python -m src.cli.train --model cnn
    python -m src.cli.train --model bilstm --epochs 80
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Literal

import numpy as np
import torch
import torch.nn as nn

from src.audio.features import MFCCExtractor
from src.models.factory import create_model
from src.training.callbacks import EarlyStopping, ModelCheckpoint
from src.training.dataloader import make_dataloaders
from src.training.metrics import (
    compute_metrics,
    plot_confusion_matrix,
    save_metrics_json,
)
from src.training.scheduler import build_scheduler, steps_per_batch
from src.training.trainer import Trainer, TrainerConfig
from src.utils.config_loader import load_yaml
from src.utils.logger import get_logger
from src.utils.seed import set_global_seed

logger = get_logger(__name__)

# rutas canonicas relativas al archivo (no al cwd)
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIGS_DIR = BACKEND_ROOT / "configs"
DEFAULT_DATA_ROOT = BACKEND_ROOT / "data"
DEFAULT_MODELS_DIR = BACKEND_ROOT / "models"

ModelName = Literal["cnn", "bilstm"]

MODEL_TO_OUTDIR: dict[str, str] = {"cnn": "cnn_base", "bilstm": "bilstm"}


def _cnn_adapter(x: torch.Tensor) -> torch.Tensor:
    # (B, n_mfcc, T) -> (B, 1, n_mfcc, T)
    return x.unsqueeze(1)


def _lstm_adapter(x: torch.Tensor) -> torch.Tensor:
    # (B, n_mfcc, T) -> (B, T, n_mfcc)
    return x.permute(0, 2, 1).contiguous()


def _build_loss(model_name: str, cfg: dict, class_weights: list[float] | None, device: torch.device) -> nn.Module:
    weight_tensor = (
        torch.tensor(class_weights, dtype=torch.float32, device=device)
        if class_weights is not None else None
    )
    loss_name = str(cfg.get("loss", "cross_entropy"))
    label_smoothing = float(cfg.get("label_smoothing", 0.0)) if "label_smoothing" in loss_name else 0.0
    return nn.CrossEntropyLoss(weight=weight_tensor, label_smoothing=label_smoothing)


def _build_scheduler_from_cfg(
    cfg: dict,
    optimizer: torch.optim.Optimizer,
    epochs: int,
    steps_per_epoch: int,
) -> tuple[torch.optim.lr_scheduler.LRScheduler | None, bool]:
    name = cfg.get("scheduler")
    if not name:
        return None, False
    if name == "one_cycle":
        sched = build_scheduler(
            "one_cycle",
            optimizer,
            total_steps=epochs * steps_per_epoch,
            max_lr=float(cfg.get("scheduler_max_lr", 1e-2)),
        )
    elif name == "cosine_annealing":
        sched = build_scheduler("cosine_annealing", optimizer, epochs=epochs)
    else:
        raise ValueError(f"Unknown scheduler: {name}")
    return sched, steps_per_batch(name)


def _spec_augment_kwargs_from_cfg(prep_cfg: dict) -> dict:
    aug = prep_cfg.get("augmentation", {}) or {}
    sa = aug.get("spec_augment", {}) or {}
    return {
        "spec_augment_freq_param": int(sa.get("freq_mask_max_width", 8)),
        "spec_augment_time_param": int(sa.get("time_mask_max_width", 25)),
        "spec_augment_n_freq_masks": int(sa.get("freq_mask_bands", 2)),
        "spec_augment_n_time_masks": int(sa.get("time_mask_bands", 2)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", choices=["cnn", "bilstm"], required=True)
    parser.add_argument("--config", default=str(DEFAULT_CONFIGS_DIR / "training.yaml"))
    parser.add_argument("--data-config", default=str(DEFAULT_CONFIGS_DIR / "data.yaml"))
    parser.add_argument(
        "--preprocessing-config", default=str(DEFAULT_CONFIGS_DIR / "preprocessing.yaml")
    )
    parser.add_argument("--splits-dir", default=str(DEFAULT_DATA_ROOT / "splits"))
    parser.add_argument(
        "--data-root",
        default=str(DEFAULT_DATA_ROOT),
        help=f"Raiz del corpus (donde estan raw/, augmented/...). Default: {DEFAULT_DATA_ROOT}",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_MODELS_DIR))
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--mixup", action="store_true")
    parser.add_argument("--no-augmented", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    training_cfg = load_yaml(args.config)
    data_cfg = load_yaml(args.data_config)
    prep_cfg = load_yaml(args.preprocessing_config)

    model_key = "cnn" if args.model == "cnn" else "lstm"
    cfg = training_cfg.get(model_key)
    if cfg is None:
        raise KeyError(f"training config has no '{model_key}' block")

    seed = int(args.seed if args.seed is not None else cfg.get("seed", 42))
    set_global_seed(seed)

    batch_size = int(args.batch_size if args.batch_size is not None else cfg.get("batch_size", 32))
    epochs = int(args.epochs if args.epochs is not None else cfg.get("epochs", 60))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    extractor = MFCCExtractor.from_config(prep_cfg)
    data_root = Path(args.data_root)
    splits_dir = Path(args.splits_dir)
    # paths.augmented en data.yaml viene como "data/augmented" (project-rooted);
    # como data_root ya es backend/data, solo tomamos el ultimo segmento.
    augmented_relpath = (data_cfg.get("paths", {}) or {}).get("augmented", "data/augmented")
    augmented_dir = data_root / Path(augmented_relpath).name

    spec_kwargs = _spec_augment_kwargs_from_cfg(prep_cfg)

    train_loader, val_loader, test_loader, class_weights = make_dataloaders(
        data_root=data_root,
        splits_dir=splits_dir,
        extractor=extractor,
        batch_size=batch_size,
        num_workers=args.num_workers,
        include_augmented_train=not args.no_augmented,
        augmented_dir=augmented_dir,
        pin_memory=(device.type == "cuda"),
        sample_rate=int(data_cfg.get("sample_rate", 16_000)),
        target_duration_s=float(data_cfg.get("duration_seconds", 2.0)),
        spec_augment_kwargs=spec_kwargs,
        cache_in_memory=True,
    )

    n_classes = len(train_loader.dataset.class_names)
    n_mfcc = int(prep_cfg.get("n_mfcc", 13))
    model = create_model(args.model, n_classes=n_classes, n_mfcc=n_mfcc)
    input_adapter = _cnn_adapter if args.model == "cnn" else _lstm_adapter

    loss_fn = _build_loss(args.model, cfg, class_weights, device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(cfg.get("learning_rate", 1e-3)),
        weight_decay=float(cfg.get("weight_decay", 1e-4)),
    )
    scheduler, scheduler_per_batch = _build_scheduler_from_cfg(
        cfg, optimizer, epochs=epochs, steps_per_epoch=max(len(train_loader), 1),
    )

    out_dir = Path(args.output_dir) / MODEL_TO_OUTDIR[args.model]
    out_dir.mkdir(parents=True, exist_ok=True)
    patience = int(cfg.get("early_stopping_patience", 10))
    callbacks = [
        EarlyStopping(patience=patience, mode="max"),
        ModelCheckpoint(dir_path=out_dir, monitor="val_f1_macro", mode="max", filename="model.pt"),
    ]

    trainer_cfg = TrainerConfig(
        epochs=epochs,
        gradient_clip_norm=float(cfg.get("gradient_clip_norm", 1.0)),
        log_every_n_steps=20,
        scheduler_step_per_batch=scheduler_per_batch,
        mixup_alpha=0.2 if args.mixup else 0.0,
        mixup_prob=0.5,
        selection_metric="val_f1_macro",
        device=str(device),
        pin_memory=(device.type == "cuda"),
    )
    trainer = Trainer(
        model=model,
        input_adapter=input_adapter,
        train_loader=train_loader,
        val_loader=val_loader,
        loss_fn=loss_fn,
        optimizer=optimizer,
        scheduler=scheduler,
        callbacks=callbacks,
        class_names=train_loader.dataset.class_names,
        config=trainer_cfg,
        seed=seed,
    )

    history = trainer.fit()

    history_path = out_dir / "history.json"
    with history_path.open("w", encoding="utf-8") as f:
        json.dump(history.to_list(), f, indent=2, ensure_ascii=False)
    logger.info("Saved history -> %s", history_path)

    shutil.copy2(args.config, out_dir / "config.yaml")

    ckpt = out_dir / "model.pt"
    if ckpt.exists():
        state = torch.load(ckpt, map_location=device, weights_only=True)
        model.load_state_dict(state)
        logger.info("Loaded best checkpoint from %s", ckpt)

    val_metrics = _evaluate_loader(
        model=model,
        loader=val_loader,
        input_adapter=input_adapter,
        device=device,
        class_names=train_loader.dataset.class_names,
    )
    save_metrics_json(val_metrics, out_dir / "val_metrics.json")
    plot_confusion_matrix(
        np.asarray(val_metrics["confusion_matrix"]),
        train_loader.dataset.class_names,
        out_dir / "confusion_matrix_val.png",
        title=f"{args.model} - val",
    )
    logger.info(
        "Final val: acc=%.4f f1_macro=%.4f",
        val_metrics["accuracy"], val_metrics["f1_macro"],
    )


@torch.no_grad()
def _evaluate_loader(
    model: nn.Module,
    loader,
    input_adapter,
    device: torch.device,
    class_names: list[str],
) -> dict:
    model.eval()
    all_true: list[np.ndarray] = []
    all_pred: list[np.ndarray] = []
    all_proba: list[np.ndarray] = []
    file_paths: list[str] = list(loader.dataset.filepaths)
    for x, y in loader:
        x = x.to(device)
        logits = model(input_adapter(x))
        proba = torch.softmax(logits, dim=1)
        preds = proba.argmax(dim=1)
        all_true.append(y.numpy())
        all_pred.append(preds.cpu().numpy())
        all_proba.append(proba.cpu().numpy())
    y_true = np.concatenate(all_true)
    y_pred = np.concatenate(all_pred)
    y_proba = np.concatenate(all_proba)
    return compute_metrics(y_true, y_pred, y_proba, class_names, file_paths=file_paths)


if __name__ == "__main__":
    main()
