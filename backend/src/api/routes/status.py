from __future__ import annotations

import time

from fastapi import APIRouter

from src.api.schemas import HealthResponse, MetricsResponse, StatusResponse
from src.api.state import app_state

router = APIRouter()


@router.get("/api/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    runner = app_state.live_runner
    return StatusResponse(
        arduino_connected=app_state.actuator.is_connected() if app_state.actuator else False,
        models_loaded=app_state.models_loaded,
        pipeline_running=app_state.pipeline.is_running if app_state.pipeline else False,
        is_listening=app_state.is_listening,
        mic_device=runner._current_device if runner else None,
        mic_device_name=runner.current_device_name if runner else None,
        cnn_model=app_state.cnn_path or "not loaded",
        uptime_seconds=round(time.time() - app_state.start_time, 1),
    )


@router.get("/api/health", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthResponse(
        status="ok",
        models_loaded=app_state.models_loaded,
        arduino_connected=app_state.actuator.is_connected() if app_state.actuator else False,
    )


@router.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    stats = app_state.stats
    return MetricsResponse(
        total_predictions=stats.total,
        accepted_predictions=stats.accepted,
        rejected_predictions=stats.rejected,
        predictions_by_class=dict(stats.by_class),
        avg_latency_ms=round(stats.avg_latency_ms, 2),
        avg_confidence=round(stats.avg_confidence, 4),
    )
