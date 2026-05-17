from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class StatusResponse(BaseModel):
    arduino_connected: bool
    models_loaded: bool
    pipeline_running: bool
    is_listening: bool
    mic_device: int | None = None
    mic_device_name: str | None = None
    cnn_model: str
    uptime_seconds: float


class ListeningStateResponse(BaseModel):
    is_listening: bool
    device: int | None = None
    device_name: str | None = None


class InferenceEvent(BaseModel):
    command: str
    confidence: float
    latency_ms: float
    rejected: bool
    timestamp: str = ""

    def with_timestamp(self) -> InferenceEvent:
        return self.model_copy(update={"timestamp": datetime.now().isoformat(timespec="milliseconds")})


class CommandRequest(BaseModel):
    command: str


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    arduino_connected: bool


class MetricsResponse(BaseModel):
    total_predictions: int
    accepted_predictions: int
    rejected_predictions: int
    predictions_by_class: dict[str, int]
    avg_latency_ms: float
    avg_confidence: float
