from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.state import app_state
from src.domain.commands import Command

router = APIRouter()


@router.post("/api/command/{cmd}")
async def send_manual_command(cmd: str) -> dict[str, str]:
    try:
        command = Command(cmd)
    except ValueError:
        valid = [c.value for c in Command]
        raise HTTPException(400, f"Unknown command: {cmd}. Valid: {valid}")

    if not app_state.actuator:
        raise HTTPException(503, "No actuator configured")

    app_state.actuator.execute(command)

    event = {
        "command": command.value,
        "confidence": 1.0,
        "latency_ms": 0.0,
        "rejected": False,
        "manual": True,
    }
    await app_state.ws_manager.publish(event)
    app_state.stats.record(command.value, 1.0, 0.0, rejected=False)

    return {"status": "ok", "command": command.value}
