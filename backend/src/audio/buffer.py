from __future__ import annotations

import threading

import numpy as np


class CircularAudioBuffer:
    def __init__(self, duration_seconds: float, sample_rate: int = 16000) -> None:
        self._sr = sample_rate
        self._capacity = int(duration_seconds * sample_rate)
        self._buffer = np.zeros(self._capacity, dtype=np.float32)
        self._write_pos = 0
        self._samples_written = 0
        self._lock = threading.Lock()

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def sample_rate(self) -> int:
        return self._sr

    @property
    def is_full(self) -> bool:
        return self._samples_written >= self._capacity

    def push(self, chunk: np.ndarray) -> None:
        chunk = chunk.astype(np.float32).ravel()
        n = len(chunk)
        with self._lock:
            if n >= self._capacity:
                self._buffer[:] = chunk[-self._capacity:]
                self._write_pos = 0
                self._samples_written = self._capacity
                return

            end = self._write_pos + n
            if end <= self._capacity:
                self._buffer[self._write_pos:end] = chunk
            else:
                first = self._capacity - self._write_pos
                self._buffer[self._write_pos:] = chunk[:first]
                self._buffer[:n - first] = chunk[first:]

            self._write_pos = end % self._capacity
            self._samples_written = min(self._samples_written + n, self._capacity)

    def get_latest(self, duration_seconds: float | None = None) -> np.ndarray:
        with self._lock:
            if duration_seconds is None:
                n = self._samples_written
            else:
                n = min(int(duration_seconds * self._sr), self._samples_written)

            if n == 0:
                return np.array([], dtype=np.float32)

            start = (self._write_pos - n) % self._capacity
            if start + n <= self._capacity:
                return self._buffer[start:start + n].copy()
            else:
                first = self._capacity - start
                return np.concatenate([
                    self._buffer[start:],
                    self._buffer[:n - first],
                ]).copy()

    def clear(self) -> None:
        with self._lock:
            self._buffer[:] = 0.0
            self._write_pos = 0
            self._samples_written = 0
