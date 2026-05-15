from __future__ import annotations

from enum import Enum


class Command(Enum):
    # Simples (CNN) — acción inmediata sobre el hardware
    ENCIENDE = "enciende"
    APAGA = "apaga"
    DETENTE = "detente"
    ROJO = "rojo"
    VERDE = "verde"
    AZUL = "azul"

    # Compuestos (BiLSTM) — secuencias / efectos multipaso
    BLANCO = "blanco"
    PROCESANDO = "procesando"
    ALARMA = "alarma"
    TONO = "tono"

    # Clase de no-comando (entrena el modelo a rechazar)
    RUIDO_FONDO = "ruido_fondo"

    def is_compound(self) -> bool:
        return self in _COMPOUND_COMMANDS

    def is_simple(self) -> bool:
        return self in _SIMPLE_COMMANDS

    def is_noise(self) -> bool:
        return self is Command.RUIDO_FONDO

    def to_protocol_string(self) -> str:
        """String ASCII que el Arduino espera (terminado en '\\n' al enviarlo)."""
        return _COMMAND_TO_STRING[self]

    @staticmethod
    def from_protocol_string(text: str) -> Command:
        try:
            return _STRING_TO_COMMAND[text.strip().lower()]
        except KeyError:
            raise ValueError(f"Unknown protocol string: {text!r}")

    @staticmethod
    def simple_commands() -> list[Command]:
        return list(_SIMPLE_COMMANDS)

    @staticmethod
    def compound_commands() -> list[Command]:
        return list(_COMPOUND_COMMANDS)


_SIMPLE_COMMANDS: frozenset[Command] = frozenset({
    Command.ENCIENDE,
    Command.APAGA,
    Command.DETENTE,
    Command.ROJO,
    Command.VERDE,
    Command.AZUL,
})

_COMPOUND_COMMANDS: frozenset[Command] = frozenset({
    Command.BLANCO,
    Command.PROCESANDO,
    Command.ALARMA,
    Command.TONO,
})

# Mapeo a strings que el Arduino entiende (ver sketch .ino)
_COMMAND_TO_STRING: dict[Command, str] = {
    Command.ENCIENDE: "enciende",
    Command.APAGA: "apaga",
    Command.DETENTE: "detente",
    Command.ROJO: "rojo",
    Command.VERDE: "verde",
    Command.AZUL: "azul",
    Command.BLANCO: "blanco",
    Command.PROCESANDO: "procesando",
    Command.ALARMA: "alarma",
    Command.TONO: "tono",
    # RUIDO_FONDO no se envía a Arduino (se rechaza en el pipeline)
}

_STRING_TO_COMMAND: dict[str, Command] = {v: k for k, v in _COMMAND_TO_STRING.items()}

# Strings de sistema que NO son comandos de voz pero sí se envían al Arduino
SYSTEM_RECHAZO = "rechazo"   # confidence < threshold
SYSTEM_OFF = "off"           # apaga todo (reset)

SIMPLE_CLASS_NAMES: list[str] = [c.value for c in Command.simple_commands()]
COMPOUND_CLASS_NAMES: list[str] = [c.value for c in Command.compound_commands()]
ALL_CLASS_NAMES: list[str] = [c.value for c in Command]
