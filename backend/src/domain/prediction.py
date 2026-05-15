from __future__ import annotations

from dataclasses import dataclass

from src.domain.commands import Command


@dataclass(frozen=True, slots=True)
class Prediction:
    command: Command
    confidence: float
    rejected: bool = False

    def is_valid(self) -> bool:
        return not self.rejected and self.command != Command.RUIDO_FONDO

    @staticmethod
    def create_rejected(command: Command = Command.RUIDO_FONDO, confidence: float = 0.0) -> Prediction:
        return Prediction(command=command, confidence=confidence, rejected=True)


@dataclass(frozen=True, slots=True)
class ModelOutput:
    label: Command
    confidence: float
    logits: list[float]

    def is_compound_candidate(self) -> bool:
        # Comandos cuya forma acústica puede confundirse con un comando compuesto:
        #   - ENCIENDE puede iniciar "enciende_*" en versiones futuras
        #   - los compuestos reales son: blanco, procesando, alarma, tono
        return self.label in (
            Command.ENCIENDE,
            Command.BLANCO,
            Command.PROCESANDO,
            Command.ALARMA,
            Command.TONO,
        )
