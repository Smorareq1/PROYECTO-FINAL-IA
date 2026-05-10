from __future__ import annotations

from enum import Enum


class Command(Enum):
    ENCIENDE = "enciende"
    APAGA = "apaga"
    IZQUIERDA = "izquierda"
    DERECHA = "derecha"
    DETENTE = "detente"
    RUIDO_FONDO = "ruido_fondo"

    ENCIENDE_RAPIDO = "enciende_rapido"
    ENCIENDE_LENTO = "enciende_lento"
    GIRA_IZQUIERDA = "gira_izquierda"
    GIRA_DERECHA = "gira_derecha"

    def is_compound(self) -> bool:
        return self in _COMPOUND_COMMANDS

    def is_simple(self) -> bool:
        return self in _SIMPLE_COMMANDS

    def to_protocol_byte(self) -> int:
        return _COMMAND_TO_BYTE[self]

    @staticmethod
    def from_protocol_byte(byte: int) -> Command:
        try:
            return _BYTE_TO_COMMAND[byte]
        except KeyError:
            raise ValueError(f"Unknown protocol byte: 0x{byte:02X}")

    @staticmethod
    def simple_commands() -> list[Command]:
        return list(_SIMPLE_COMMANDS)

    @staticmethod
    def compound_commands() -> list[Command]:
        return list(_COMPOUND_COMMANDS)


_SIMPLE_COMMANDS: frozenset[Command] = frozenset({
    Command.ENCIENDE,
    Command.APAGA,
    Command.IZQUIERDA,
    Command.DERECHA,
    Command.DETENTE,
    Command.RUIDO_FONDO,
})

_COMPOUND_COMMANDS: frozenset[Command] = frozenset({
    Command.ENCIENDE_RAPIDO,
    Command.ENCIENDE_LENTO,
    Command.GIRA_IZQUIERDA,
    Command.GIRA_DERECHA,
})

_COMMAND_TO_BYTE: dict[Command, int] = {
    Command.ENCIENDE: 0x01,
    Command.APAGA: 0x02,
    Command.IZQUIERDA: 0x03,
    Command.DERECHA: 0x04,
    Command.DETENTE: 0x05,
    Command.ENCIENDE_RAPIDO: 0x10,
    Command.ENCIENDE_LENTO: 0x11,
    Command.GIRA_IZQUIERDA: 0x12,
    Command.GIRA_DERECHA: 0x13,
}

_BYTE_TO_COMMAND: dict[int, Command] = {v: k for k, v in _COMMAND_TO_BYTE.items()}

HEARTBEAT_BYTE = 0xFE
RESET_BYTE = 0xFF

SIMPLE_CLASS_NAMES: list[str] = [c.value for c in Command.simple_commands()]
COMPOUND_CLASS_NAMES: list[str] = [c.value for c in Command.compound_commands()]
ALL_CLASS_NAMES: list[str] = [c.value for c in Command]
