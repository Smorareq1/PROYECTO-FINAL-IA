import pytest

from src.domain.commands import Command, HEARTBEAT_BYTE, RESET_BYTE
from src.hardware.command_protocol import command_to_byte, byte_to_command, describe_byte


def test_all_commands_have_protocol_byte():
    for cmd in Command:
        if cmd == Command.RUIDO_FONDO:
            continue
        byte = cmd.to_protocol_byte()
        assert 0 < byte < 0xFE


def test_roundtrip_byte_conversion():
    for cmd in Command:
        if cmd == Command.RUIDO_FONDO:
            continue
        byte = command_to_byte(cmd)
        recovered = byte_to_command(byte)
        assert recovered == cmd


def test_simple_vs_compound():
    simple = Command.simple_commands()
    compound = Command.compound_commands()
    assert len(simple) == 6
    assert len(compound) == 4
    assert Command.ENCIENDE in simple
    assert Command.ENCIENDE_RAPIDO in compound


def test_is_compound():
    assert Command.ENCIENDE_RAPIDO.is_compound() is True
    assert Command.GIRA_IZQUIERDA.is_compound() is True
    assert Command.ENCIENDE.is_compound() is False
    assert Command.DETENTE.is_compound() is False


def test_is_simple():
    assert Command.ENCIENDE.is_simple() is True
    assert Command.RUIDO_FONDO.is_simple() is True
    assert Command.ENCIENDE_RAPIDO.is_simple() is False


def test_protocol_bytes_match_plan():
    assert Command.ENCIENDE.to_protocol_byte() == 0x01
    assert Command.APAGA.to_protocol_byte() == 0x02
    assert Command.IZQUIERDA.to_protocol_byte() == 0x03
    assert Command.DERECHA.to_protocol_byte() == 0x04
    assert Command.DETENTE.to_protocol_byte() == 0x05
    assert Command.ENCIENDE_RAPIDO.to_protocol_byte() == 0x10
    assert Command.ENCIENDE_LENTO.to_protocol_byte() == 0x11
    assert Command.GIRA_IZQUIERDA.to_protocol_byte() == 0x12
    assert Command.GIRA_DERECHA.to_protocol_byte() == 0x13


def test_heartbeat_and_reset_bytes():
    assert HEARTBEAT_BYTE == 0xFE
    assert RESET_BYTE == 0xFF


def test_describe_byte():
    assert "rele" in describe_byte(0x01).lower()
    assert "heartbeat" in describe_byte(0xFE).lower()
    assert "Unknown" in describe_byte(0xAA)


def test_invalid_byte_raises():
    with pytest.raises(ValueError):
        Command.from_protocol_byte(0xAA)
