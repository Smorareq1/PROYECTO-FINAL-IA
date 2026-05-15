from __future__ import annotations

from src.domain.commands import Command, SYSTEM_OFF, SYSTEM_RECHAZO

# Mapeo Command → string ASCII (el Arduino hace Serial.readStringUntil('\n'))
PROTOCOL_MAP: dict[Command, str] = {
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
}

# Descripción humana del efecto físico que dispara cada comando
PROTOCOL_DESCRIPTION: dict[str, str] = {
    "enciende":   "Rele ON + RGB blanco + beep activo 100ms",
    "apaga":      "Rele OFF + RGB apagado + beep activo 100ms",
    "detente":    "Apaga todo (rele/RGB/LEDs) + beep activo 250ms",
    "rojo":       "RGB rojo (255, 0, 0)",
    "verde":      "RGB verde (0, 255, 0)",
    "azul":       "RGB azul (0, 0, 255)",
    "blanco":     "RGB blanco brillante (255, 255, 255)",
    "procesando": "LED amarillo + RGB naranja transitorio (procesando)",
    "alarma":     "4x parpadeo rojo + buzzer pasivo 1kHz + buzzer activo",
    "tono":       "Melodia 3 notas en buzzer pasivo (800-1200-1600 Hz)",
    SYSTEM_RECHAZO: "(sistema) LED rojo + buzzer 250Hz cuando la confianza < umbral",
    SYSTEM_OFF:    "(sistema) Apaga todo, deja LED verde de escucha",
}


def command_to_string(command: Command) -> str:
    return command.to_protocol_string()


def string_to_command(text: str) -> Command:
    return Command.from_protocol_string(text)


def describe(text: str) -> str:
    return PROTOCOL_DESCRIPTION.get(text.strip().lower(), f"Unknown command: {text!r}")
