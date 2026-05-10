from __future__ import annotations

import numpy as np


def compute_frame_energy(signal: np.ndarray, frame_len: int, hop: int) -> np.ndarray:
    n_frames = 1 + (len(signal) - frame_len) // hop
    energy = np.zeros(n_frames, dtype=np.float64)
    for i in range(n_frames):
        start = i * hop
        frame = signal[start : start + frame_len]
        energy[i] = np.sum(frame ** 2) / frame_len
    return energy


def compute_frame_zcr(signal: np.ndarray, frame_len: int, hop: int) -> np.ndarray:
    n_frames = 1 + (len(signal) - frame_len) // hop
    zcr = np.zeros(n_frames, dtype=np.float64)
    for i in range(n_frames):
        start = i * hop
        frame = signal[start : start + frame_len]
        zcr[i] = np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * frame_len)
    return zcr


def detect_speech(
    signal: np.ndarray,
    sr: int = 16000,
    frame_length_ms: float = 25.0,
    hop_length_ms: float = 10.0,
    noise_floor_duration_ms: float = 200.0,
    energy_threshold_multiplier: float = 5.0,
    zcr_threshold: float = 0.3,
) -> tuple[int, int]:
    frame_len = int(frame_length_ms / 1000 * sr)
    hop = int(hop_length_ms / 1000 * sr)

    energy = compute_frame_energy(signal, frame_len, hop)
    zcr = compute_frame_zcr(signal, frame_len, hop)

    noise_frames = int(noise_floor_duration_ms / 1000 * sr / hop)
    noise_frames = max(1, min(noise_frames, len(energy)))
    noise_floor = np.mean(energy[:noise_frames])

    threshold = noise_floor * energy_threshold_multiplier
    voiced = (energy > threshold) & (zcr < zcr_threshold)

    indices = np.where(voiced)[0]
    if len(indices) == 0:
        return 0, len(signal)

    start_frame = int(indices[0])
    end_frame = int(indices[-1])

    start_sample = start_frame * hop
    end_sample = min(end_frame * hop + frame_len, len(signal))

    return start_sample, end_sample


def is_speech(
    signal: np.ndarray,
    sr: int = 16000,
    min_speech_duration_ms: float = 100.0,
    **kwargs: object,
) -> bool:
    start, end = detect_speech(signal, sr, **kwargs)  # type: ignore[arg-type]
    duration_ms = (end - start) / sr * 1000
    return duration_ms >= min_speech_duration_ms
