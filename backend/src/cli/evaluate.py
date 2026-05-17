"""Evalua un modelo entrenado sobre val o test y persiste metricas.

Uso:
    python -m src.cli.evaluate --model cnn --split test
    python -m src.cli.evaluate --model bilstm --split test --tta
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from src.audio.features import MFCCExtractor
from src.models.factory import load_model
from src.training.dataset import CommandDataset
from src.training.metrics import (
    compute_metrics,
    plot_confusion_matrix,
    save_metrics_json,
)
from src.utils.config_loader import load_yaml
from src.utils.logger import get_logger
from src.utils.seed import set_global_seed

logger = get_logger(__name__)

# rutas canonicas relativas al archivo (no al cwd)
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIGS_DIR = BACKEND_ROOT / "configs"
DEFAULT_DATA_ROOT = BACKEND_ROOT / "data"
DEFAULT_MODELS_DIR = BACKEND_ROOT / "models"

MODEL_TO_OUTDIR: dict[str, str] = {"cnn": "cnn_base", "bilstm": "bilstm"}


def _cnn_adapter(x: torch.Tensor) -> torch.Tensor:
    return x.unsqueeze(1)


def _lstm_adapter(x: torch.Tensor) -> torch.Tensor:
    return x.permute(0, 2, 1).contiguous()


@torch.no_grad()
def _forward_logits(model, x: torch.Tensor, adapter) -> torch.Tensor:
    return model(adapter(x))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", choices=["cnn", "bilstm"], required=True)
    parser.add_argument("--split", choices=["val", "test"], default="test")
    parser.add_argument("--weights", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--data-config", default=str(DEFAULT_CONFIGS_DIR / "data.yaml"))
    parser.add_argument(
        "--preprocessing-config", default=str(DEFAULT_CONFIGS_DIR / "preprocessing.yaml")
    )
    parser.add_argument("--splits-dir", default=str(DEFAULT_DATA_ROOT / "splits"))
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--tta", action="store_true", help="Test-Time Augmentation (3 SpecAugment passes)")
    args = parser.parse_args()

    set_global_seed(args.seed)

    data_cfg = load_yaml(args.data_config)
    prep_cfg = load_yaml(args.preprocessing_config)

    out_dir = Path(args.output_dir or DEFAULT_MODELS_DIR / MODEL_TO_OUTDIR[args.model])
    weights = Path(args.weights or out_dir / "model.pt")
    if not weights.exists():
        raise FileNotFoundError(f"Weights not found: {weights}")

    extractor = MFCCExtractor.from_config(prep_cfg)
    data_root = Path(args.data_root)
    splits_dir = Path(args.splits_dir)

    eval_ds = CommandDataset(
        split_csv=splits_dir / f"{args.split}.csv",
        data_root=data_root,
        extractor=extractor,
        sample_rate=int(data_cfg.get("sample_rate", 16_000)),
        target_duration_s=float(data_cfg.get("duration_seconds", 2.0)),
        is_train=False,
        include_augmented=False,
        cache_in_memory=True,
    )
    tta_ds = None
    if args.tta:
        tta_ds = CommandDataset(
            split_csv=splits_dir / f"{args.split}.csv",
            data_root=data_root,
            extractor=extractor,
            sample_rate=int(data_cfg.get("sample_rate", 16_000)),
            target_duration_s=float(data_cfg.get("duration_seconds", 2.0)),
            is_train=True,
            include_augmented=False,
            cache_in_memory=True,
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    n_classes = len(eval_ds.class_names)
    n_mfcc = int(prep_cfg.get("n_mfcc", 13))
    model = load_model(args.model, weights, device=str(device), n_classes=n_classes, n_mfcc=n_mfcc)
    model.to(device).eval()

    adapter = _cnn_adapter if args.model == "cnn" else _lstm_adapter

    file_paths = list(eval_ds.filepaths)

    def _predict_dataset(ds) -> tuple[np.ndarray, np.ndarray]:
        dl = torch.utils.data.DataLoader(ds, batch_size=args.batch_size, shuffle=False)
        true_chunks: list[np.ndarray] = []
        proba_chunks: list[np.ndarray] = []
        with torch.no_grad():
            for x, y in dl:
                x = x.to(device)
                logits = _forward_logits(model, x, adapter)
                proba_chunks.append(torch.softmax(logits, dim=1).cpu().numpy())
                true_chunks.append(y.numpy())
        return np.concatenate(true_chunks), np.concatenate(proba_chunks)

    y_true, y_proba = _predict_dataset(eval_ds)
    if args.tta and tta_ds is not None:
        proba_sum = y_proba.copy()
        n_passes = 1
        for _ in range(3):
            _, proba_aug = _predict_dataset(tta_ds)
            proba_sum = proba_sum + proba_aug
            n_passes += 1
        y_proba = proba_sum / n_passes

    y_pred = y_proba.argmax(axis=1)

    metrics = compute_metrics(y_true, y_pred, y_proba, eval_ds.class_names, file_paths=file_paths)

    out_dir.mkdir(parents=True, exist_ok=True)
    save_metrics_json(metrics, out_dir / f"{args.split}_metrics.json")
    plot_confusion_matrix(
        np.asarray(metrics["confusion_matrix"]),
        eval_ds.class_names,
        out_dir / f"confusion_matrix_{args.split}.png",
        title=f"{args.model} - {args.split}",
    )

    top_errors_path = out_dir / f"top_errors_{args.split}.json"
    with top_errors_path.open("w", encoding="utf-8") as f:
        json.dump(metrics.get("top_errors", []), f, indent=2, ensure_ascii=False)

    print(metrics["classification_report"])
    logger.info(
        "%s/%s: acc=%.4f f1_macro=%.4f",
        args.model, args.split, metrics["accuracy"], metrics["f1_macro"],
    )


if __name__ == "__main__":
    main()
