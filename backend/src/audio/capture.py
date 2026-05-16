"""Captura de audio en streaming continuo desde sounddevice.

Modelo: callback no-bloqueante escribe chunks float32 en una `queue.Queue`.
El consumidor (pipeline de inferencia) los drena con `iter_chunks()` o un loop
sobre `.chunks()`. Si la queue se satura, se descarta el chunk mas antiguo.

Uso:
    with MicrophoneCapture(sample_rate=16000, chunk_ms=32) as mic:
        for chunk in mic.chunks():
            do_something(chunk)
"""
from __future__ import annotations

import queue
from collections.abc import Iterator
from typing import Callable

import numpy as np
import sounddevice as sd

from src.utils.logger import get_logger

logger = get_logger(__name__)

ChunkCallback = Callable[[np.ndarray], None]


class MicrophoneCapture:
    def __init__(
        self,
        sample_rate: int = 16_000,
        chunk_ms: int = 32,
        device: int | str | None = None,
        on_chunk: ChunkCallback | None = None,
        max_queue: int = 200,
    ) -> None:
        self._sr = int(sample_rate)
        self._chunk_size = int(sample_rate * chunk_ms / 1000)
        self._device = device
        self._on_chunk = on_chunk
        self._q: queue.Queue[np.ndarray] = queue.Queue(maxsize=max_queue)
        self._stream: sd.InputStream | None = None
        self._running = False
        self._dropped = 0

    @property
    def sample_rate(self) -> int:
        return self._sr

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    @property
    def chunk_ms(self) -> float:
        return 1000.0 * self._chunk_size / self._sr

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def dropped(self) -> int:
        return self._dropped

    @staticmethod
    def list_input_devices() -> list[dict[str, object]]:
        return [d for d in sd.query_devices() if d.get("max_input_channels", 0) >= 1]

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:  # noqa: ARG002
        if status:
            logger.debug("sounddevice status: %s", status)
        chunk = np.asarray(indata[:, 0], dtype=np.float32).copy()
        try:
            self._q.put_nowait(chunk)
        except queue.Full:
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
            try:
                self._q.put_nowait(chunk)
            except queue.Full:
                self._dropped += 1
                return
            self._dropped += 1
        if self._on_chunk is not None:
            try:
                self._on_chunk(chunk)
            except Exception:  # pragma: no cover - defensivo
                logger.exception("on_chunk callback fallo")

    def start(self) -> None:
        if self._running:
            return
        self._stream = sd.InputStream(
            samplerate=self._sr,
            blocksize=self._chunk_size,
            channels=1,
            dtype="float32",
            callback=self._callback,
            device=self._device,
        )
        self._stream.start()
        self._running = True
        logger.info(
            "Microfono iniciado: sr=%d, chunk=%d muestras (%.1f ms), device=%s",
            self._sr,
            self._chunk_size,
            self.chunk_ms,
            self._device,
        )

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None
        logger.info("Microfono detenido (chunks descartados: %d)", self._dropped)

    def get(self, timeout: float | None = None) -> np.ndarray:
        return self._q.get(timeout=timeout)

    def chunks(self, timeout: float | None = None) -> Iterator[np.ndarray]:
        while self._running or not self._q.empty():
            try:
                yield self._q.get(timeout=timeout)
            except queue.Empty:
                if not self._running:
                    return
                continue

    def drain(self) -> np.ndarray:
        chunks: list[np.ndarray] = []
        while True:
            try:
                chunks.append(self._q.get_nowait())
            except queue.Empty:
                break
        if not chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(chunks)

    def __enter__(self) -> "MicrophoneCapture":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()
