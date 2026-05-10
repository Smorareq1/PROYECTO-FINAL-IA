from __future__ import annotations

import numpy as np


def normalize_amplitude(
    signal: np.ndarray,
    target_peak: float = 0.9,
) -> np.ndarray:
    peak = np.max(np.abs(signal))
    if peak < 1e-9:
        return signal
    return signal * (target_peak / peak)


def check_quality(
    signal: np.ndarray,
    peak_max: float = 0.95,
    rms_min: float = 0.01,
) -> tuple[bool, str]:
    peak = float(np.max(np.abs(signal)))
    rms = float(np.sqrt(np.mean(signal ** 2)))

    if peak > peak_max:
        return False, f"Signal clipping: peak={peak:.3f} > {peak_max}"
    if rms < rms_min:
        return False, f"Signal too weak: rms={rms:.4f} < {rms_min}"
    return True, "OK"
