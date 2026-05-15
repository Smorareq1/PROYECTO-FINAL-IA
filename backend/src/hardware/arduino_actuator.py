from __future__ import annotations

from src.domain.commands import Command, SYSTEM_OFF, SYSTEM_RECHAZO
from src.hardware.serial_link import SerialLink
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ArduinoActuator:
    """Envía comandos al Arduino físico vía serial (protocolo ASCII + '\\n')."""

    def __init__(self, link: SerialLink) -> None:
        self._link = link

    def execute(self, command: Command) -> None:
        if command.is_noise():
            # ruido_fondo no se envía: el modelo lo usa para distinguir voz vs no-voz
            logger.debug("Skipping send: %s is a noise class", command.value)
            return
        text = command.to_protocol_string()
        self._link.send_line(text)
        logger.info("Sent command '%s' to Arduino", text)

    def signal_rejected(self) -> None:
        """Notifica al Arduino que se rechazó una predicción (low confidence)."""
        self._link.send_line(SYSTEM_RECHAZO)
        logger.info("Sent system signal '%s' to Arduino", SYSTEM_RECHAZO)

    def reset(self) -> None:
        """Apaga todo en el Arduino (LED verde de escucha encendido)."""
        self._link.send_line(SYSTEM_OFF)
        logger.info("Sent system signal '%s' to Arduino", SYSTEM_OFF)

    def is_connected(self) -> bool:
        return self._link.heartbeat()


class MockActuator:
    """Actuador que registra comandos sin hardware. Para tests y desarrollo."""

    def __init__(self) -> None:
        self._last_command: Command | None = None
        self._history: list[Command] = []

    def execute(self, command: Command) -> None:
        if command.is_noise():
            logger.debug("[MOCK] Skipping noise class: %s", command.value)
            return
        self._last_command = command
        self._history.append(command)
        logger.info("[MOCK] Command executed: '%s'", command.value)

    def signal_rejected(self) -> None:
        logger.info("[MOCK] System signal: 'rechazo'")

    def reset(self) -> None:
        self._last_command = None
        logger.info("[MOCK] Reset (off)")

    def is_connected(self) -> bool:
        return True

    @property
    def last_command(self) -> Command | None:
        return self._last_command

    @property
    def history(self) -> list[Command]:
        return list(self._history)
