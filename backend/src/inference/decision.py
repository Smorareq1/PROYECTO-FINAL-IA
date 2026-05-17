from __future__ import annotations

from src.domain.commands import Command
from src.domain.prediction import ModelOutput, Prediction
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DecisionLayer:
    """Acepta o rechaza la salida del CNN según un umbral de confianza.

    Si la etiqueta es RUIDO_FONDO o la confianza está por debajo del umbral,
    la predicción se marca como rechazada y no debe llegar al Arduino.
    """

    def __init__(self, confidence_threshold: float = 0.85) -> None:
        self._threshold = float(confidence_threshold)

    @property
    def confidence_threshold(self) -> float:
        return self._threshold

    def from_cnn(self, pred: ModelOutput) -> Prediction:
        if pred.confidence < self._threshold:
            logger.debug(
                "Rejected: low confidence %.3f < %.3f", pred.confidence, self._threshold
            )
            return Prediction.create_rejected(pred.label, pred.confidence)
        if pred.label == Command.RUIDO_FONDO:
            return Prediction.create_rejected(Command.RUIDO_FONDO, pred.confidence)
        return Prediction(command=pred.label, confidence=pred.confidence)
