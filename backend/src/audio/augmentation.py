"""Aumento de datos para audio: 5 tecnicas.

Convencion:
- Las cuatro funciones sobre waveform reciben `np.ndarray` float32 mono.
- `spec_augment` opera sobre tensores MFCC (batch o no) usando
  torchaudio.transforms.FrequencyMasking / TimeMasking.
- Todas aceptan un `np.random.Generator` para reproducibilidad.

Las cuatro primeras se aplican offline por `scripts/augment_offline.py`.
`spec_augment` se aplica online en el Dataset porque opera sobre MFCC.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

try:  # librosa.effects.pitch_shift produce mejor calidad que un resample manual.
    import librosa
except Exception:  # pragma: no cover - libreria opcional al testear
    librosa = None  # type: ignore[assignment]

import torch
import torchaudio.transforms as T


def time_shift(
    audio: np.ndarray,
    sr: int = 16_000,
    max_ms: int = 200,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Desplaza la senal +/- `max_ms` con padding de ceros."""
    rng = rng or np.random.default_rng()
    max_shift = int(sr * max_ms / 1000)
    if max_shift <= 0 or audio.size == 0:
        return audio.copy()
    shift = int(rng.integers(-max_shift, max_shift + 1))
    out = np.zeros_like(audio)
    if shift > 0:
        out[shift:] = audio[: len(audio) - shift]
    elif shift < 0:
        out[: len(audio) + shift] = audio[-shift:]
    else:
        out[:] = audio
    return out


def pitch_shift(
    audio: np.ndarray,
    sr: int = 16_000,
    semitones_range: tuple[float, float] = (-2.0, 2.0),
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Pitch shift por +/- semitonos. Usa librosa.effects.pitch_shift."""
    rng = rng or np.random.default_rng()
    lo, hi = semitones_range
    n_steps = float(rng.uniform(lo, hi))
    if abs(n_steps) < 1e-3 or librosa is None:
        return audio.copy()
    shifted = librosa.effects.pitch_shift(audio.astype(np.float32), sr=sr, n_steps=n_steps)
    return shifted.astype(np.float32)


def add_gaussian_noise(
    audio: np.ndarray,
    snr_db_range: tuple[float, float] = (15.0, 25.0),
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Anade ruido gaussiano con SNR uniforme en el rango dado."""
    rng = rng or np.random.default_rng()
    snr_db = float(rng.uniform(*snr_db_range))
    signal_power = float(np.mean(audio.astype(np.float64) ** 2)) + 1e-12
    noise_power = signal_power / (10.0 ** (snr_db / 10.0))
    noise = rng.normal(0.0, np.sqrt(noise_power), size=audio.shape).astype(np.float32)
    return (audio + noise).astype(np.float32)


def mix_background(
    audio: np.ndarray,
    bg_pool: list[np.ndarray],
    snr_db_range: tuple[float, float] = (10.0, 20.0),
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Mezcla la senal con un fondo elegido al azar del pool con SNR objetivo."""
    rng = rng or np.random.default_rng()
    if not bg_pool:
        return audio.copy()
    bg_full = bg_pool[int(rng.integers(0, len(bg_pool)))]
    if bg_full.size == 0:
        return audio.copy()
    if len(bg_full) >= len(audio):
        start = int(rng.integers(0, len(bg_full) - len(audio) + 1))
        bg = bg_full[start : start + len(audio)]
    else:
        reps = int(np.ceil(len(audio) / len(bg_full)))
        bg = np.tile(bg_full, reps)[: len(audio)]

    signal_power = float(np.mean(audio.astype(np.float64) ** 2)) + 1e-12
    bg_power = float(np.mean(bg.astype(np.float64) ** 2)) + 1e-12
    snr_db = float(rng.uniform(*snr_db_range))
    target_bg_power = signal_power / (10.0 ** (snr_db / 10.0))
    scale = float(np.sqrt(target_bg_power / bg_power))
    return (audio + scale * bg).astype(np.float32)


def spec_augment(
    mfcc: torch.Tensor,
    freq_mask_param: int = 8,
    time_mask_param: int = 25,
    n_freq_masks: int = 2,
    n_time_masks: int = 2,
) -> torch.Tensor:
    """Aplica SpecAugment a un tensor MFCC.

    Forma esperada: (n_mfcc, time) o (batch, n_mfcc, time).
    Devuelve un tensor de la misma forma con bandas enmascaradas.
    """
    if mfcc.ndim == 2:
        mfcc = mfcc.unsqueeze(0)
        squeeze_out = True
    else:
        squeeze_out = False

    freq_mask = T.FrequencyMasking(freq_mask_param=freq_mask_param)
    time_mask = T.TimeMasking(time_mask_param=time_mask_param)
    out = mfcc
    for _ in range(n_freq_masks):
        out = freq_mask(out)
    for _ in range(n_time_masks):
        out = time_mask(out)

    return out.squeeze(0) if squeeze_out else out


def load_background_pool(noise_dir: Path, sr: int = 16_000, max_files: int | None = None) -> list[np.ndarray]:
    """Carga los WAV de `noise_dir` (ej. data/processed/ruido_fondo) como pool de fondos.

    Importado aqui para mantener `augmentation.py` libre de dependencias I/O salvo cuando se requiere.
    """
    import soundfile as sf  # local para evitar overhead al importar el modulo

    files = sorted(noise_dir.rglob("*.wav"))
    if max_files is not None:
        files = files[:max_files]
    pool: list[np.ndarray] = []
    for path in files:
        audio, file_sr = sf.read(path)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        if file_sr != sr:
            if librosa is None:
                continue
            audio = librosa.resample(audio.astype(np.float32), orig_sr=file_sr, target_sr=sr)
        pool.append(audio.astype(np.float32))
    return pool
