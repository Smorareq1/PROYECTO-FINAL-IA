"""Captura de audio nativa por el backend.

El backend usa sounddevice (a través de MicrophoneCapture) para escuchar el
micrófono del host. Los endpoints exponen lista de dispositivos y start/stop.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.schemas import ListeningStateResponse
from src.api.state import app_state
from src.audio.live_runner import LiveAudioRunner
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class DeviceInfo(BaseModel):
    index: int
    name: str
    channels: int
    default_sample_rate: float
    is_default: bool


class DevicesResponse(BaseModel):
    devices: list[DeviceInfo]
    current: int | None
    current_name: str | None


class StartRequest(BaseModel):
    device: int | None = None


async def _publish(payload: dict[str, object]) -> None:
    await app_state.ws_manager.publish(payload)


def _get_runner() -> LiveAudioRunner:
    if app_state.live_runner is None:
        if app_state.pipeline is None:
            raise HTTPException(503, "Pipeline no inicializado")
        app_state.live_runner = LiveAudioRunner(app_state.pipeline, _publish)
    return app_state.live_runner


@router.get("/api/listening/devices", response_model=DevicesResponse)
async def list_devices() -> DevicesResponse:
    devices = LiveAudioRunner.list_devices()
    runner = app_state.live_runner
    return DevicesResponse(
        devices=[DeviceInfo(**d) for d in devices],
        current=runner._current_device if runner else None,
        current_name=runner.current_device_name if runner else None,
    )


@router.post("/api/listening/start", response_model=ListeningStateResponse)
async def start_listening(req: StartRequest | None = None) -> ListeningStateResponse:
    runner = _get_runner()
    device = req.device if req else None
    info = runner.start(device)
    app_state.is_listening = True
    logger.info("Listening iniciado en %r", info.get("device_name"))
    return ListeningStateResponse(
        is_listening=True,
        device=info.get("device"),
        device_name=info.get("device_name"),
    )


@router.post("/api/listening/stop", response_model=ListeningStateResponse)
async def stop_listening() -> ListeningStateResponse:
    runner = app_state.live_runner
    if runner:
        runner.stop()
    app_state.is_listening = False
    logger.info("Listening detenido")
    return ListeningStateResponse(is_listening=False, device=None, device_name=None)
