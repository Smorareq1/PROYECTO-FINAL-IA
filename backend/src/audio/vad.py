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


class StreamingVADGate:
    """Detector de fin-de-voz para captura streaming.

    Acumula chunks (float32 mono a `sr` Hz). Mantiene un piso de ruido
    adaptativo y dispara `True` cuando detecta `silence_ms` consecutivos
    despues de al menos `min_speech_ms` de voz.

    El estado interno se reinicia al disparar; el llamador es responsable
    de extraer la ventana correspondiente del buffer circular.
    """

    def __init__(
        self,
        sr: int = 16000,
        silence_ms: int = 250,
        min_speech_ms: int = 300,
        frame_ms: int = 25,
        energy_threshold_mult: float = 5.0,
        noise_floor_alpha: float = 0.02,
    ) -> None:
        self._sr = int(sr)
        self._silence_frames_required = max(1, int(silence_ms / frame_ms))
        self._min_speech_frames = max(1, int(min_speech_ms / frame_ms))
        self._frame_len = max(1, int(frame_ms / 1000 * sr))
        self._threshold_mult = float(energy_threshold_mult)
        self._noise_floor_alpha = float(noise_floor_alpha)

        self._noise_floor: float | None = None
        self._speech_streak = 0
        self._silence_streak = 0
        self._in_speech = False
        self._partial: np.ndarray = np.zeros(0, dtype=np.float32)
        self._last_trigger_speech_frames = 0

    @property
    def noise_floor(self) -> float | None:
        return self._noise_floor

    @property
    def in_speech(self) -> bool:
        return self._in_speech

    def reset(self) -> None:
        self._speech_streak = 0
        self._silence_streak = 0
        self._in_speech = False
        self._partial = np.zeros(0, dtype=np.float32)

    def calibrate(self, ambient_audio: np.ndarray) -> None:
        """Inicializa el piso de ruido con una muestra ambiental (>= 1 frame)."""
        if ambient_audio.size < self._frame_len:
            return
        n_frames = max(1, len(ambient_audio) // self._frame_len)
        usable = ambient_audio[: n_frames * self._frame_len].astype(np.float64)
        frames = usable.reshape(n_frames, self._frame_len)
        energies = np.mean(frames ** 2, axis=1)
        self._noise_floor = float(np.median(energies)) + 1e-10

    def process_chunk(self, chunk: np.ndarray) -> bool:
        """Procesa un chunk y devuelve True si se acaba de cerrar un comando."""
        if chunk.size == 0:
            return False
        self._partial = np.concatenate([self._partial, chunk.astype(np.float32, copy=False)])
        n_frames = len(self._partial) // self._frame_len
        if n_frames == 0:
            return False

        frames = self._partial[: n_frames * self._frame_len].reshape(n_frames, self._frame_len)
        self._partial = self._partial[n_frames * self._frame_len :]
        energies = np.mean(frames.astype(np.float64) ** 2, axis=1)

        triggered = False
        for energy in energies:
            if self._noise_floor is None:
                self._noise_floor = float(energy) + 1e-10
                continue
            threshold = self._noise_floor * self._threshold_mult
            is_voice = energy > threshold
            if is_voice:
                self._speech_streak += 1
                self._silence_streak = 0
                if self._speech_streak >= self._min_speech_frames:
                    self._in_speech = True
            else:
                if not self._in_speech:
                    self._noise_floor = (
                        (1.0 - self._noise_floor_alpha) * self._noise_floor
                        + self._noise_floor_alpha * float(energy)
                    )
                self._silence_streak += 1
                if self._in_speech and self._silence_streak >= self._silence_frames_required:
                    self._last_trigger_speech_frames = self._speech_streak
                    self._in_speech = False
                    self._speech_streak = 0
                    self._silence_streak = 0
                    triggered = True
        return triggered

    @property
    def last_trigger_speech_ms(self) -> float:
        return 1000.0 * self._last_trigger_speech_frames * self._frame_len / self._sr
