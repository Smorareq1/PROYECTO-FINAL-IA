import pytest

from src.domain.commands import Command, SYSTEM_OFF, SYSTEM_RECHAZO
from src.hardware.command_protocol import command_to_string, string_to_command, describe


def test_all_voice_commands_have_protocol_string():
    for cmd in Command:
        if cmd.is_noise():
            continue
        text = cmd.to_protocol_string()
        assert isinstance(text, str) and text == text.lower()


def test_roundtrip_string_conversion():
    for cmd in Command:
        if cmd.is_noise():
            continue
        text = command_to_string(cmd)
        assert string_to_command(text) is cmd


def test_simple_vs_compound():
    simple = Command.simple_commands()
    compound = Command.compound_commands()
    assert len(simple) == 6
    assert len(compound) == 4
    assert Command.ENCIENDE in simple
    assert Command.BLANCO in compound


def test_is_compound():
    assert Command.BLANCO.is_compound() is True
    assert Command.ALARMA.is_compound() is True
    assert Command.ENCIENDE.is_compound() is False
    assert Command.DETENTE.is_compound() is False


def test_is_simple():
    assert Command.ENCIENDE.is_simple() is True
    assert Command.RUIDO_FONDO.is_simple() is False
    assert Command.BLANCO.is_simple() is False


def test_protocol_strings_match_arduino_sketch():
    # Estos strings deben coincidir EXACTAMENTE con los `if (cmd == "...")` del .ino
    assert Command.ENCIENDE.to_protocol_string() == "enciende"
    assert Command.APAGA.to_protocol_string() == "apaga"
    assert Command.DETENTE.to_protocol_string() == "detente"
    assert Command.ROJO.to_protocol_string() == "rojo"
    assert Command.VERDE.to_protocol_string() == "verde"
    assert Command.AZUL.to_protocol_string() == "azul"
    assert Command.BLANCO.to_protocol_string() == "blanco"
    assert Command.PROCESANDO.to_protocol_string() == "procesando"
    assert Command.ALARMA.to_protocol_string() == "alarma"
    assert Command.TONO.to_protocol_string() == "tono"


def test_system_signal_constants():
    assert SYSTEM_OFF == "off"
    assert SYSTEM_RECHAZO == "rechazo"


def test_describe_known_and_unknown():
    assert "rele" in describe("enciende").lower()
    assert "rgb" in describe("rojo").lower()
    assert "Unknown" in describe("xxxxx")


def test_from_protocol_string_invalid_raises():
    with pytest.raises(ValueError):
        Command.from_protocol_string("foo")


def test_from_protocol_string_is_case_insensitive():
    assert Command.from_protocol_string("ENCIENDE") is Command.ENCIENDE
    assert Command.from_protocol_string(" Rojo ") is Command.ROJO
