from __future__ import annotations

from src.domain.commands import Command
from src.hardware.serial_link import SerialLink
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ArduinoActuator:
    def __init__(self, link: SerialLink) -> None:
        self._link = link

    def execute(self, command: Command) -> None:
        if not command.is_actuation():
            logger.debug("Comando %s no se envía al Arduino", command.value)
            return
        token = command.to_wire()
        self._link.send_line(token)
        logger.info("Sent command %r to Arduino", token)

    def stop_all(self) -> None:
        """Atajo: pone al Arduino en estado seguro (apaga todo y vuelve a escucha)."""
        self._link.send_line(Command.OFF.to_wire())

    def is_connected(self) -> bool:
        return self._link.is_open


class MockActuator:
    """Actuator que registra comandos sin hardware. Para tests y desarrollo."""

    def __init__(self) -> None:
        self._last_command: Command | None = None
        self._history: list[Command] = []

    def execute(self, command: Command) -> None:
        self._last_command = command
        self._history.append(command)
        if command.is_actuation():
            logger.info("[MOCK] Sent command %r", command.value)
        else:
            logger.info("[MOCK] Skipping non-actuation command %r", command.value)

    def stop_all(self) -> None:
        self._last_command = Command.OFF
        self._history.append(Command.OFF)
        logger.info("[MOCK] stop_all")

    def is_connected(self) -> bool:
        return True

    @property
    def last_command(self) -> Command | None:
        return self._last_command

    @property
    def history(self) -> list[Command]:
        return list(self._history)
