from __future__ import annotations

import time
from typing import Optional

import serial
import serial.tools.list_ports

from src.domain.commands import HEARTBEAT_BYTE, RESET_BYTE
from src.domain.exceptions import SerialConnectionError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SerialLink:
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

    def send_byte(self, byte: int) -> None:
        if not 0 <= byte <= 255:
            raise ValueError(f"Byte out of range: {byte}")
        if not self.is_open:
            raise SerialConnectionError("Serial port is not open")
        assert self._serial is not None
        self._serial.write(bytes([byte]))
        self._serial.flush()

    def read_byte(self, timeout: float | None = None) -> int | None:
        if not self.is_open:
            raise SerialConnectionError("Serial port is not open")
        assert self._serial is not None
        old_timeout = self._serial.timeout
        if timeout is not None:
            self._serial.timeout = timeout
        try:
            data = self._serial.read(1)
            return data[0] if data else None
        finally:
            self._serial.timeout = old_timeout

    def heartbeat(self) -> bool:
        try:
            self.send_byte(HEARTBEAT_BYTE)
            response = self.read_byte(timeout=1.0)
            return response == HEARTBEAT_BYTE
        except (SerialConnectionError, serial.SerialException):
            return False

    def reset(self) -> None:
        self.send_byte(RESET_BYTE)
        logger.info("Reset command sent to Arduino")


def find_arduino_port() -> str | None:
    for port_info in serial.tools.list_ports.comports():
        desc = (port_info.description or "").lower()
        manufacturer = (port_info.manufacturer or "").lower()
        if "arduino" in desc or "arduino" in manufacturer or "ch340" in desc or "cp210" in desc:
            logger.info("Arduino detected on %s (%s)", port_info.device, port_info.description)
            return port_info.device
    return None
