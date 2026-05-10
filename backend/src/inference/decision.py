from __future__ import annotations

from src.domain.commands import Command
from src.domain.prediction import ModelOutput, Prediction
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DecisionLayer:
    def __init__(
        self,
        confidence_threshold: float = 0.85,
        compound_confidence_threshold: float = 0.80,
    ) -> None:
        self._threshold = confidence_threshold
        self._compound_threshold = compound_confidence_threshold

    def from_cnn(self, pred: ModelOutput) -> Prediction:
        if pred.confidence < self._threshold:
            logger.debug("Rejected: low confidence %.3f < %.3f", pred.confidence, self._threshold)
            return Prediction.create_rejected(pred.label, pred.confidence)
        if pred.label == Command.RUIDO_FONDO:
            return Prediction.create_rejected(Command.RUIDO_FONDO, pred.confidence)
        return Prediction(command=pred.label, confidence=pred.confidence)

    def from_lstm(self, pred: ModelOutput) -> Prediction:
        if pred.confidence < self._compound_threshold:
            return Prediction.create_rejected(pred.label, pred.confidence)
        return Prediction(command=pred.label, confidence=pred.confidence)

    def combine(self, cnn_pred: ModelOutput, lstm_pred: ModelOutput) -> Prediction:
        if lstm_pred.confidence > self._compound_threshold:
            return Prediction(command=lstm_pred.label, confidence=lstm_pred.confidence)
        return self.from_cnn(cnn_pred)

    def should_use_lstm(self, cnn_pred: ModelOutput) -> bool:
        return cnn_pred.is_compound_candidate() and cnn_pred.confidence > self._threshold * 0.7
