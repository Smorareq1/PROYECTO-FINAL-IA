"""Aumento de datos offline sobre el corpus.

Para cada clip de entrada genera `--variants` variantes aplicando
combinaciones aleatorias de: time-shift, pitch-shift, gaussian-noise y
mix-background. Por defecto las variantes se escriben en
backend/data/augmented/<clase>/<stem>_aug<idx>.wav.

`spec_augment` se aplica online en el Dataset (no aqui), porque opera
sobre MFCC y no sobre la senal.

Uso:
    python -m scripts.augment_offline                     # raw/ -> augmented/
    python -m scripts.augment_offline --variants 4 --seed 42
    python -m scripts.augment_offline --train-only        # solo splits train
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
import soundfile as sf

from src.audio.augmentation import (
    add_gaussian_noise,
    load_background_pool,
    mix_background,
    pitch_shift,
    time_shift,
)
from src.utils.config_loader import load_yaml
from src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_SR = 16_000


def list_clips_from_dir(input_dir: Path) -> list[Path]:
    return sorted(input_dir.rglob("*.wav"))


def list_clips_from_manifest(manifest_path: Path, data_root: Path, train_only: bool) -> list[Path]:
    if not manifest_path.exists():
        return []
    paths: list[Path] = []
    with manifest_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if train_only and row.get("split", "") != "train":
                continue
            if row.get("class") == "ruido_fondo":
                continue
            relpath = row.get("filepath", "")
            if not relpath:
                continue
            paths.append(data_root / relpath)
    return paths


def apply_random_transforms(
    audio: np.ndarray,
    sr: int,
    bg_pool: list[np.ndarray],
    rng: np.random.Generator,
    aug_cfg: dict,
) -> np.ndarray:
    out = audio.copy()
    if bool(rng.integers(0, 2)):
        out = time_shift(
            out, sr=sr, max_ms=int(aug_cfg.get("time_shift_ms", 200)), rng=rng,
        )
    if bool(rng.integers(0, 2)):
        ps = aug_cfg.get("pitch_shift_semitones", 2)
        out = pitch_shift(out, sr=sr, semitones_range=(-float(ps), float(ps)), rng=rng)
    if bool(rng.integers(0, 2)):
        snr_lo, snr_hi = aug_cfg.get("noise_snr_range", [15, 25])
        out = add_gaussian_noise(out, snr_db_range=(float(snr_lo), float(snr_hi)), rng=rng)
    if bg_pool and bool(rng.integers(0, 2)):
        bg_lo, bg_hi = aug_cfg.get("background_snr_range", [10, 20])
        out = mix_background(out, bg_pool, snr_db_range=(float(bg_lo), float(bg_hi)), rng=rng)

    peak = float(np.max(np.abs(out)))
    if peak > 0.99:
        out = out * (0.99 / peak)
    return out.astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-root", default="backend/data", help="Raiz del corpus")
    parser.add_argument("--input-dir", default=None, help="Override: directorio de entrada (default raw/)")
    parser.add_argument("--output-dir", default=None, help="Override: directorio de salida (default augmented/)")
    parser.add_argument("--manifest", default=None, help="CSV manifest; si se da, ignora --input-dir.")
    parser.add_argument("--train-only", action="store_true", help="Solo augmenta split=train (requiere manifest).")
    parser.add_argument("--variants", type=int, default=4, help="Variantes por clip (default 4).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--preproc-config",
        default="backend/configs/preprocessing.yaml",
        help="YAML con seccion augmentation.",
    )
    args = parser.parse_args()

    data_root = Path(args.data_root)
    input_dir = Path(args.input_dir) if args.input_dir else data_root / "raw"
    output_dir = Path(args.output_dir) if args.output_dir else data_root / "augmented"
    manifest_path = Path(args.manifest) if args.manifest else data_root / "manifests" / "corpus.csv"

    cfg = load_yaml(args.preproc_config)
    aug_cfg = cfg.get("augmentation", {})
    sr = int(cfg.get("sample_rate", DEFAULT_SR))

    if args.manifest or args.train_only:
        clips = list_clips_from_manifest(manifest_path, data_root, args.train_only)
        logger.info("Modo manifest: %d clips a procesar (train_only=%s)", len(clips), args.train_only)
    else:
        clips = list_clips_from_dir(input_dir)
        logger.info("Modo glob: %d clips en %s", len(clips), input_dir)

    bg_dir = data_root / "raw" / "ruido_fondo"
    bg_pool = load_background_pool(bg_dir, sr=sr) if bg_dir.exists() else []
    logger.info("Pool de ruido_fondo cargado: %d archivos", len(bg_pool))

    output_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    n_written = 0
    n_skipped = 0
    for clip_path in clips:
        if not clip_path.exists():
            logger.warning("Falta clip: %s", clip_path)
            n_skipped += 1
            continue
        audio, file_sr = sf.read(clip_path)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        audio = audio.astype(np.float32)
        if file_sr != sr:
            logger.warning("SR distinto en %s (%d != %d), saltando", clip_path, file_sr, sr)
            n_skipped += 1
            continue

        rel_class_dir = clip_path.parent.name
        out_class_dir = output_dir / rel_class_dir
        out_class_dir.mkdir(parents=True, exist_ok=True)

        for i in range(1, args.variants + 1):
            variant_rng = np.random.default_rng(rng.integers(0, 2**31 - 1))
            variant = apply_random_transforms(audio, sr, bg_pool, variant_rng, aug_cfg)
            out_path = out_class_dir / f"{clip_path.stem}_aug{i}.wav"
            sf.write(out_path, variant, sr, subtype="PCM_16")
            n_written += 1

    logger.info("Aumentos generados: %d (saltados: %d)", n_written, n_skipped)


if __name__ == "__main__":
    main()
