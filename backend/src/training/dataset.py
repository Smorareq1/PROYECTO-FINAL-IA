from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from torch.utils.data import Dataset

from src.audio.augmentation import spec_augment
from src.audio.features import MFCCExtractor
from src.audio.normalization import normalize_amplitude
from src.domain.commands import ALL_CLASS_NAMES
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class _Row:
    filepath: str
    class_name: str


def _pad_or_trim(audio: np.ndarray, target_samples: int) -> np.ndarray:
    n = audio.shape[0]
    if n == target_samples:
        return audio
    if n > target_samples:
        start = (n - target_samples) // 2
        return audio[start : start + target_samples]
    out = np.zeros(target_samples, dtype=np.float32)
    out[:n] = audio
    return out


def _load_wav(path: Path, sample_rate: int) -> np.ndarray:
    audio, sr = sf.read(path, dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    if sr != sample_rate:
        raise ValueError(f"Sample rate mismatch in {path}: got {sr}, expected {sample_rate}")
    return audio.astype(np.float32, copy=False)


class CommandDataset(Dataset):
    def __init__(
        self,
        split_csv: Path,
        data_root: Path,
        extractor: MFCCExtractor,
        sample_rate: int = 16_000,
        target_duration_s: float = 2.0,
        is_train: bool = False,
        include_augmented: bool = False,
        augmented_dir: Path | None = None,
        spec_augment_freq_param: int = 8,
        spec_augment_time_param: int = 25,
        spec_augment_n_freq_masks: int = 2,
        spec_augment_n_time_masks: int = 2,
        cache_in_memory: bool = True,
    ) -> None:
        self._class_names = list(ALL_CLASS_NAMES)
        self._class_to_idx = {c: i for i, c in enumerate(self._class_names)}
        self._data_root = Path(data_root)
        self._extractor = extractor
        self._sample_rate = int(sample_rate)
        self._target_samples = int(round(target_duration_s * sample_rate))
        self._is_train = bool(is_train)
        self._spec_freq_param = spec_augment_freq_param
        self._spec_time_param = spec_augment_time_param
        self._spec_n_freq = spec_augment_n_freq_masks
        self._spec_n_time = spec_augment_n_time_masks
        self._cache_in_memory = bool(cache_in_memory)
        self._mfcc_cache: dict[int, torch.Tensor] = {}

        self._rows: list[_Row] = self._load_split(Path(split_csv))
        if include_augmented and is_train and augmented_dir is not None:
            extra = self._scan_augmented(Path(augmented_dir))
            self._rows.extend(extra)
            logger.info(
                "Dataset[train]: %d base + %d augmented = %d total",
                len(self._rows) - len(extra), len(extra), len(self._rows),
            )
        else:
            logger.info("Dataset[%s]: %d clips", "train" if is_train else "eval", len(self._rows))

    @property
    def class_names(self) -> list[str]:
        return list(self._class_names)

    @property
    def class_to_idx(self) -> dict[str, int]:
        return dict(self._class_to_idx)

    @property
    def filepaths(self) -> list[str]:
        return [r.filepath for r in self._rows]

    @property
    def labels(self) -> list[int]:
        return [self._class_to_idx[r.class_name] for r in self._rows]

    def _load_split(self, csv_path: Path) -> list[_Row]:
        rows: list[_Row] = []
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                cls = r.get("class", "")
                if cls not in self._class_to_idx:
                    continue
                fp = r.get("filepath", "")
                if not fp:
                    continue
                rows.append(_Row(filepath=fp, class_name=cls))
        return rows

    def _scan_augmented(self, augmented_dir: Path) -> list[_Row]:
        extras: list[_Row] = []
        if not augmented_dir.exists():
            return extras
        root_abs = self._data_root.resolve()
        for cls in self._class_names:
            class_dir = augmented_dir / cls
            if not class_dir.exists():
                continue
            for wav in sorted(class_dir.rglob("*.wav")):
                wav_abs = wav.resolve()
                try:
                    rel = wav_abs.relative_to(root_abs)
                except ValueError:
                    rel = wav
                extras.append(_Row(filepath=str(rel), class_name=cls))
        return extras

    def __len__(self) -> int:
        return len(self._rows)

    def _compute_mfcc(self, audio: np.ndarray) -> torch.Tensor:
        waveform = torch.from_numpy(audio).unsqueeze(0)
        mfcc = self._extractor(waveform).squeeze(0)
        return mfcc

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        row = self._rows[idx]
        label = self._class_to_idx[row.class_name]

        if self._cache_in_memory and idx in self._mfcc_cache:
            mfcc = self._mfcc_cache[idx].clone()
        else:
            path = self._data_root / row.filepath
            audio = _load_wav(path, self._sample_rate)
            audio = _pad_or_trim(audio, self._target_samples)
            audio = normalize_amplitude(audio, target_peak=0.9)
            mfcc = self._compute_mfcc(audio)
            if self._cache_in_memory:
                self._mfcc_cache[idx] = mfcc.detach().clone()

        if self._is_train:
            mfcc = spec_augment(
                mfcc,
                freq_mask_param=self._spec_freq_param,
                time_mask_param=self._spec_time_param,
                n_freq_masks=self._spec_n_freq,
                n_time_masks=self._spec_n_time,
            )

        return mfcc, label
