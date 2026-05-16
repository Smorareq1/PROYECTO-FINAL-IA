from __future__ import annotations

from enum import Enum


class Command(Enum):
    ENCIENDE = "enciende"
    APAGA = "apaga"
    DETENTE = "detente"
    ROJO = "rojo"
    VERDE = "verde"
    AZUL = "azul"
    BLANCO = "blanco"
    PROCESANDO = "procesando"
    RECHAZO = "rechazo"
    ALARMA = "alarma"
    TONO = "tono"
    OFF = "off"
    RUIDO_FONDO = "ruido_fondo"

    def is_actuation(self) -> bool:
        """True si el comando se envía al Arduino. RUIDO_FONDO no se envía."""
        return self is not Command.RUIDO_FONDO

    def to_wire(self) -> str:
        """Token de texto que el firmware espera por Serial (sin '\\n')."""
        return self.value

    @staticmethod
    def from_wire(token: str) -> Command:
        try:
            return Command(token.strip().lower())
        except ValueError as e:
            raise ValueError(f"Unknown command token: {token!r}") from e

    @staticmethod
    def actuation_commands() -> list[Command]:
        return [c for c in Command if c.is_actuation()]


ACTUATION_CLASS_NAMES: list[str] = [c.value for c in Command.actuation_commands()]
ALL_CLASS_NAMES: list[str] = [c.value for c in Command]
N_CLASSES: int = len(ALL_CLASS_NAMES)
