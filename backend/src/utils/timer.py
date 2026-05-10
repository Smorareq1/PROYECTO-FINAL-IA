from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator


class TimerResult:
    __slots__ = ("_start", "_end")

    def __init__(self) -> None:
        self._start = 0.0
        self._end = 0.0

    @property
    def elapsed_ms(self) -> float:
        return (self._end - self._start) * 1000.0

    @property
    def elapsed_s(self) -> float:
        return self._end - self._start


@contextmanager
def timer() -> Generator[TimerResult, None, None]:
    result = TimerResult()
    result._start = time.perf_counter()
    try:
        yield result
    finally:
        result._end = time.perf_counter()
