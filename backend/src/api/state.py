from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field

from src.api.websocket import ConnectionManager
from src.audio.live_runner import LiveAudioRunner
from src.domain.interfaces import Actuator
from src.inference.pipeline import InferencePipeline


@dataclass
class PredictionStats:
    total: int = 0
    accepted: int = 0
    rejected: int = 0
    by_class: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _latencies: list[float] = field(default_factory=list)
    _confidences: list[float] = field(default_factory=list)

    def record(self, command: str, confidence: float, latency_ms: float, rejected: bool) -> None:
        self.total += 1
        if rejected:
            self.rejected += 1
        else:
            self.accepted += 1
            self.by_class[command] += 1
        self._latencies.append(latency_ms)
        self._confidences.append(confidence)

    @property
    def avg_latency_ms(self) -> float:
        return sum(self._latencies) / len(self._latencies) if self._latencies else 0.0

    @property
    def avg_confidence(self) -> float:
        return sum(self._confidences) / len(self._confidences) if self._confidences else 0.0


class AppState:
    def __init__(self) -> None:
        self.ws_manager = ConnectionManager()
        self.pipeline: InferencePipeline | None = None
        self.actuator: Actuator | None = None
        self.models_loaded: bool = False
        self.cnn_path: str | None = None
        self.start_time: float = time.time()
        self.stats = PredictionStats()
        self.is_listening: bool = False
        self.live_runner: LiveAudioRunner | None = None


app_state = AppState()
