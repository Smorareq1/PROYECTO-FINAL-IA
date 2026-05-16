from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None,
    class_names: list[str],
    file_paths: list[str] | None = None,
) -> dict[str, Any]:
    n_classes = len(class_names)
    labels = list(range(n_classes))

    accuracy = float(np.mean(y_true == y_pred))
    f1_macro = float(f1_score(y_true, y_pred, average="macro", labels=labels, zero_division=0))
    f1_micro = float(f1_score(y_true, y_pred, average="micro", labels=labels, zero_division=0))

    precision_pc, recall_pc, f1_pc, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0,
    )

    cm = confusion_matrix(y_true, y_pred, labels=labels)
    report = classification_report(
        y_true, y_pred, labels=labels, target_names=class_names, zero_division=0, digits=4,
    )

    metrics: dict[str, Any] = {
        "accuracy": accuracy,
        "f1_macro": f1_macro,
        "f1_micro": f1_micro,
        "precision_per_class": {class_names[i]: float(precision_pc[i]) for i in range(n_classes)},
        "recall_per_class": {class_names[i]: float(recall_pc[i]) for i in range(n_classes)},
        "f1_per_class": {class_names[i]: float(f1_pc[i]) for i in range(n_classes)},
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }

    if y_proba is not None and file_paths is not None:
        wrong = np.where(y_true != y_pred)[0]
        if len(wrong):
            confidences = y_proba[wrong, y_pred[wrong]]
            order = np.argsort(-confidences)[:10]
            top_errors = []
            for k in order:
                i = int(wrong[k])
                top_errors.append({
                    "filepath": file_paths[i],
                    "true": class_names[int(y_true[i])],
                    "pred": class_names[int(y_pred[i])],
                    "confidence": float(y_proba[i, int(y_pred[i])]),
                })
            metrics["top_errors"] = top_errors
        else:
            metrics["top_errors"] = []

    return metrics


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: list[str],
    out_path: Path,
    normalize: bool = True,
    title: str = "Confusion Matrix",
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    cm = np.asarray(cm, dtype=np.float64)
    if normalize:
        row_sums = cm.sum(axis=1, keepdims=True)
        cm_display = np.divide(cm, row_sums, out=np.zeros_like(cm), where=row_sums > 0)
        fmt = ".2f"
    else:
        cm_display = cm
        fmt = ".0f"

    fig, ax = plt.subplots(figsize=(max(6, len(class_names)), max(5, len(class_names) * 0.8)))
    sns.heatmap(
        cm_display,
        annot=True,
        fmt=fmt,
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        cbar=True,
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    return obj


def save_metrics_json(metrics: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(_to_jsonable(metrics), f, indent=2, ensure_ascii=False)
