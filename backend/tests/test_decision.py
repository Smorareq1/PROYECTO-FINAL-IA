import pytest

from src.domain.commands import Command
from src.domain.prediction import ModelOutput, Prediction
from src.inference.decision import DecisionLayer


@pytest.fixture
def decision() -> DecisionLayer:
    return DecisionLayer(confidence_threshold=0.85)


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


def test_prediction_rejected_factory():
    pred = Prediction.create_rejected()
    assert pred.rejected
    assert not pred.is_valid()


def test_prediction_is_valid():
    pred = Prediction(command=Command.ENCIENDE, confidence=0.95)
    assert pred.is_valid()
