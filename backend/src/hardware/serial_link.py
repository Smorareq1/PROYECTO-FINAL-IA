from __future__ import annotations

import time
from typing import Optional

import serial
import serial.tools.list_ports

from src.domain.exceptions import SerialConnectionError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SerialLink:
    """Conexión serial texto/'\\n' a 115200 baudios, compatible con el firmware Arduino.

    Cada comando se envía como una cadena ASCII terminada en '\\n'.
    El firmware ignora tokens desconocidos y opcionalmente devuelve eco textual.
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
            time.sleep(2.0)
            try:
                self._serial.reset_input_buffer()
                self._serial.reset_output_buffer()
            except Exception:
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
        """Envía un token al Arduino terminado en '\\n' (lo que el firmware espera)."""
        if not self.is_open:
            raise SerialConnectionError("Serial port is not open")
        assert self._serial is not None
        line = text.strip() + "\n"
        self._serial.write(line.encode("ascii", errors="ignore"))
        self._serial.flush()

    def read_line(self, timeout: float | None = None) -> str | None:
        """Lee una línea de texto (eco/diagnóstico) del Arduino. None si timeout."""
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
            return raw.decode("ascii", errors="replace").strip()
        finally:
            self._serial.timeout = old_timeout


def find_arduino_port() -> str | None:
    for port_info in serial.tools.list_ports.comports():
        desc = (port_info.description or "").lower()
        manufacturer = (port_info.manufacturer or "").lower()
        if "arduino" in desc or "arduino" in manufacturer or "ch340" in desc or "cp210" in desc:
            logger.info("Arduino detected on %s (%s)", port_info.device, port_info.description)
            return port_info.device
    return None
