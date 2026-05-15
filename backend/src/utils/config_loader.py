from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.domain.exceptions import ConfigurationError


def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise ConfigurationError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ConfigurationError(f"Config file must be a YAML mapping: {path}")
    return data


def load_config(*paths: str | Path) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for p in paths:
        merged.update(load_yaml(p))
    return merged
