import pytest

from src.domain.commands import (
    ACTUATION_CLASS_NAMES,
    ALL_CLASS_NAMES,
    Command,
    N_CLASSES,
)
from src.hardware.command_protocol import command_to_wire, describe


EXPECTED_ARDUINO_TOKENS = {
    "enciende",
    "apaga",
    "detente",
    "rojo",
    "verde",
    "azul",
    "blanco",
    "procesando",
    "rechazo",
    "alarma",
    "tono",
    "off",
}


def test_actuation_set_matches_arduino_firmware():
    assert set(ACTUATION_CLASS_NAMES) == EXPECTED_ARDUINO_TOKENS


def test_ruido_fondo_is_not_actuation():
    assert Command.RUIDO_FONDO.is_actuation() is False
    assert "ruido_fondo" not in ACTUATION_CLASS_NAMES
    assert "ruido_fondo" in ALL_CLASS_NAMES


def test_total_class_count_for_model():
    # 12 comandos para Arduino + ruido_fondo (rechazo)
    assert N_CLASSES == 13
    assert len(ALL_CLASS_NAMES) == 13


def test_to_wire_is_identity_token():
    for cmd in Command.actuation_commands():
        assert cmd.to_wire() == cmd.value
        assert command_to_wire(cmd) == cmd.value


def test_from_wire_roundtrip():
    for token in EXPECTED_ARDUINO_TOKENS:
        cmd = Command.from_wire(token)
        assert cmd.value == token


def test_from_wire_is_case_and_space_tolerant():
    assert Command.from_wire("  ENCIENDE\n") == Command.ENCIENDE
    assert Command.from_wire("Rojo") == Command.ROJO


def test_from_wire_rejects_unknown_token():
    with pytest.raises(ValueError):
        Command.from_wire("zzz_no_existe")


def test_describe_has_entries_for_all_actuation_commands():
    for cmd in Command.actuation_commands():
        msg = describe(cmd)
        assert msg and "sin descripción" not in msg.lower()
