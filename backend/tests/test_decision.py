import pytest

from src.domain.commands import Command
from src.domain.prediction import ModelOutput, Prediction
from src.inference.decision import DecisionLayer


@pytest.fixture
def decision() -> DecisionLayer:
    return DecisionLayer(confidence_threshold=0.85, compound_confidence_threshold=0.80)


def _make_output(label: Command, confidence: float) -> ModelOutput:
    return ModelOutput(label=label, confidence=confidence, logits=[0.0])


def test_from_cnn_high_confidence_accepts(decision: DecisionLayer):
    pred = decision.from_cnn(_make_output(Command.ENCIENDE, 0.95))
    assert pred.is_valid()
    assert pred.command == Command.ENCIENDE
    assert not pred.rejected


def test_from_cnn_low_confidence_rejects(decision: DecisionLayer):
    pred = decision.from_cnn(_make_output(Command.ENCIENDE, 0.50))
    assert not pred.is_valid()
    assert pred.rejected


def test_from_cnn_ruido_fondo_always_rejects(decision: DecisionLayer):
    pred = decision.from_cnn(_make_output(Command.RUIDO_FONDO, 0.99))
    assert not pred.is_valid()
    assert pred.rejected


def test_combine_prefers_lstm_high_confidence(decision: DecisionLayer):
    cnn = _make_output(Command.ENCIENDE, 0.90)
    lstm = _make_output(Command.BLANCO, 0.92)
    pred = decision.combine(cnn, lstm)
    assert pred.command == Command.BLANCO
    assert pred.confidence == 0.92


def test_combine_falls_back_to_cnn_when_lstm_low(decision: DecisionLayer):
    cnn = _make_output(Command.ENCIENDE, 0.90)
    lstm = _make_output(Command.BLANCO, 0.50)
    pred = decision.combine(cnn, lstm)
    assert pred.command == Command.ENCIENDE


def test_should_use_lstm_for_compound_candidates(decision: DecisionLayer):
    assert decision.should_use_lstm(_make_output(Command.ENCIENDE, 0.70))
    assert decision.should_use_lstm(_make_output(Command.ALARMA, 0.70))


def test_should_not_use_lstm_for_simple_commands(decision: DecisionLayer):
    assert not decision.should_use_lstm(_make_output(Command.APAGA, 0.95))
    assert not decision.should_use_lstm(_make_output(Command.DETENTE, 0.95))


def test_prediction_rejected_factory():
    pred = Prediction.create_rejected()
    assert pred.rejected
    assert not pred.is_valid()


def test_prediction_is_valid():
    pred = Prediction(command=Command.ENCIENDE, confidence=0.95)
    assert pred.is_valid()


def test_model_output_compound_candidate():
    out = _make_output(Command.ENCIENDE, 0.9)
    assert out.is_compound_candidate()

    out2 = _make_output(Command.APAGA, 0.9)
    assert not out2.is_compound_candidate()
