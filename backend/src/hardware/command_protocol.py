from __future__ import annotations

from src.domain.commands import Command, HEARTBEAT_BYTE, RESET_BYTE


PROTOCOL_MAP: dict[Command, int] = {
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

PROTOCOL_DESCRIPTION: dict[int, str] = {
    0x01: "Cierra rele",
    0x02: "Abre rele",
    0x03: "Motor pasos: 512 antihorario",
    0x04: "Motor pasos: 512 horario",
    0x05: "Beep 200ms y todo apagado",
    0x10: "Rele ON + LED RGB blanco brillante",
    0x11: "Rele ON + LED RGB azul tenue con fade",
    0x12: "Motor pasos: 1024 antihorario",
    0x13: "Motor pasos: 1024 horario",
    HEARTBEAT_BYTE: "Heartbeat (Arduino responde 0xFE)",
    RESET_BYTE: "Reset a estado inicial",
}


def command_to_byte(command: Command) -> int:
    return command.to_protocol_byte()


def byte_to_command(byte: int) -> Command:
    return Command.from_protocol_byte(byte)


def describe_byte(byte: int) -> str:
    return PROTOCOL_DESCRIPTION.get(byte, f"Unknown byte: 0x{byte:02X}")
