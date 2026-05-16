from __future__ import annotations

from src.domain.commands import Command


PROTOCOL_DESCRIPTION: dict[str, str] = {
    "enciende": "Relé ON + RGB blanco + beep activo corto",
    "apaga": "Relé OFF + RGB apagado + beep activo corto",
    "detente": "Apaga todo + beep activo largo",
    "rojo": "RGB rojo",
    "verde": "RGB verde",
    "azul": "RGB azul",
    "blanco": "RGB blanco",
    "procesando": "LED amarillo + RGB ámbar (estado de procesamiento)",
    "rechazo": "LED rojo + RGB rojo + tono grave (estado de rechazo)",
    "alarma": "Parpadeo rojo + tono intermitente",
    "tono": "Melodía compuesta (3 tonos ascendentes)",
    "off": "Apaga todo y vuelve al estado de escucha",
}


def command_to_wire(command: Command) -> str:
    """Devuelve el token textual ASCII que se enviará por Serial al Arduino."""
    return command.to_wire()


def describe(command: Command) -> str:
    return PROTOCOL_DESCRIPTION.get(command.value, f"Comando sin descripción: {command.value}")
