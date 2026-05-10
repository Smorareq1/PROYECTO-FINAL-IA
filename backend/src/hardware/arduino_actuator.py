from __future__ import annotations

from src.domain.commands import Command
from src.domain.exceptions import SerialConnectionError
from src.hardware.serial_link import SerialLink
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ArduinoActuator:
    def __init__(self, link: SerialLink) -> None:
        self._link = link

    def execute(self, command: Command) -> None:
        byte = command.to_protocol_byte()
        self._link.send_byte(byte)
        logger.info("Sent command %s (0x%02X) to Arduino", command.value, byte)

    def reset(self) -> None:
        self._link.reset()

    def is_connected(self) -> bool:
        return self._link.heartbeat()


class MockActuator:
    """Actuator that logs commands without real hardware. Used for testing and development."""

    def __init__(self) -> None:
        self._last_command: Command | None = None
        self._history: list[Command] = []

    def execute(self, command: Command) -> None:
        self._last_command = command
        self._history.append(command)
        logger.info("[MOCK] Command executed: %s (0x%02X)", command.value, command.to_protocol_byte())

    def reset(self) -> None:
        self._last_command = None
        logger.info("[MOCK] Reset")

    def is_connected(self) -> bool:
        return True

    @property
    def last_command(self) -> Command | None:
        return self._last_command

    @property
    def history(self) -> list[Command]:
        return list(self._history)
