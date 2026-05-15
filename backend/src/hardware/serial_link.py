from __future__ import annotations

import time
from typing import Optional

import serial
import serial.tools.list_ports

from src.domain.exceptions import SerialConnectionError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SerialLink:
    """
    Enlace serial con el Arduino. El protocolo es texto ASCII en minúsculas
    terminado en '\\n' (lo que el sketch lee con Serial.readStringUntil('\\n')).
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1) -> None:
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._serial: Optional[serial.Serial] = None

    def open(self) -> None:
        try:
            self._serial = serial.Serial(
                self._port, self._baudrate, timeout=self._timeout
            )
            # El Arduino se reinicia al abrir el puerto; esperamos a que arranque.
            time.sleep(2.0)
            try:
                self._serial.reset_input_buffer()
            except Exception:  # noqa: BLE001
                pass
            logger.info("Serial port opened: %s @ %d", self._port, self._baudrate)
        except serial.SerialException as e:
            raise SerialConnectionError(f"Cannot open {self._port}: {e}") from e

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info("Serial port closed: %s", self._port)

    @property
    def is_open(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def send_line(self, text: str) -> None:
        """Envía un comando ASCII terminado en '\\n'."""
        if not self.is_open:
            raise SerialConnectionError("Serial port is not open")
        assert self._serial is not None

        payload = (text.strip().lower() + "\n").encode("ascii", errors="ignore")
        self._serial.write(payload)
        self._serial.flush()

    def read_line(self, timeout: float | None = None) -> str | None:
        """Lee una línea (hasta '\\n') del Arduino, o None si timeout."""
        if not self.is_open:
            raise SerialConnectionError("Serial port is not open")
        assert self._serial is not None

        old_timeout = self._serial.timeout
        if timeout is not None:
            self._serial.timeout = timeout
        try:
            raw = self._serial.readline()
            if not raw:
                return None
            return raw.decode("ascii", errors="ignore").strip()
        finally:
            self._serial.timeout = old_timeout

    def heartbeat(self) -> bool:
        """
        Envía 'off' (comando inocuo) y verifica que el Arduino contesta algo.
        El sketch responde con "Comando recibido: off" cuando lo recibe.
        """
        try:
            self.send_line("off")
            for _ in range(5):
                response = self.read_line(timeout=0.5)
                if response and "off" in response.lower():
                    return True
            return False
        except (SerialConnectionError, serial.SerialException):
            return False

    def reset(self) -> None:
        """Manda el comando 'off' que apaga todo y deja el LED verde encendido."""
        self.send_line("off")
        logger.info("Reset (off) command sent to Arduino")


def find_arduino_port() -> str | None:
    for port_info in serial.tools.list_ports.comports():
        desc = (port_info.description or "").lower()
        manufacturer = (port_info.manufacturer or "").lower()
        if (
            "arduino" in desc
            or "arduino" in manufacturer
            or "ch340" in desc
            or "cp210" in desc
            or "usb-serial" in desc
        ):
            logger.info("Arduino detected on %s (%s)", port_info.device, port_info.description)
            return port_info.device
    return None
