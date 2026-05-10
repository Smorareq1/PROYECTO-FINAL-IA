from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.state import app_state

router = APIRouter()


@router.websocket("/ws/inference")
async def inference_ws(ws: WebSocket) -> None:
    await app_state.ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        app_state.ws_manager.disconnect(ws)
