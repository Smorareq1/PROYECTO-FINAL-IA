from __future__ import annotations

import asyncio
from typing import Any

import numpy as np
import torch

from src.audio.buffer import CircularAudioBuffer
from src.audio.features import MFCCExtractor
from src.audio.vad import detect_speech, is_speech
from src.audio.normalization import normalize_amplitude
from src.domain.commands import Command
from src.domain.interfaces import Actuator, EventBroadcaster
from src.domain.prediction import Prediction
from src.inference.decision import DecisionLayer
from src.inference.predictor import CNNPredictor, BiLSTMPredictor
from src.utils.logger import get_logger
from src.utils.timer import timer

logger = get_logger(__name__)


class InferencePipeline:
    def __init__(
        self,
        feature_extractor: MFCCExtractor,
        cnn_predictor: CNNPredictor,
        lstm_predictor: BiLSTMPredictor | None,
        decision: DecisionLayer,
        actuator: Actuator,
        broadcaster: EventBroadcaster | None = None,
        sample_rate: int = 16000,
        buffer_duration: float = 3.0,
    ) -> None:
        self._extractor = feature_extractor
        self._cnn = cnn_predictor
        self._lstm = lstm_predictor
        self._decision = decision
        self._actuator = actuator
        self._broadcaster = broadcaster
        self._sr = sample_rate
        self._buffer = CircularAudioBuffer(buffer_duration, sample_rate)
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def push_audio(self, chunk: np.ndarray) -> None:
        self._buffer.push(chunk)

    def process_buffer(self) -> dict[str, Any]:
        window = self._buffer.get_latest()

        if len(window) == 0 or not is_speech(window, self._sr):
            return {"rejected": True, "reason": "no_speech"}

        start, end = detect_speech(window, self._sr)
        speech = window[start:end]
        speech = normalize_amplitude(speech)

        with timer() as t:
            waveform = torch.from_numpy(speech).unsqueeze(0)
            mfcc = self._extractor.extract(waveform)
            mfcc_squeezed = mfcc.squeeze(0)

            cnn_pred = self._cnn.predict(mfcc_squeezed)
            prediction: Prediction

            if self._lstm and self._decision.should_use_lstm(cnn_pred):
                lstm_pred = self._lstm.predict(mfcc_squeezed)
                prediction = self._decision.combine(cnn_pred, lstm_pred)
            else:
                prediction = self._decision.from_cnn(cnn_pred)

        latency_ms = t.elapsed_ms

        if prediction.is_valid():
            self._actuator.execute(prediction.command)

        result = {
            "command": prediction.command.value,
            "confidence": round(prediction.confidence, 4),
            "latency_ms": round(latency_ms, 2),
            "rejected": prediction.rejected,
        }

        logger.info(
            "Prediction: %s (%.2f%%) in %.1f ms %s",
            prediction.command.value,
            prediction.confidence * 100,
            latency_ms,
            "[REJECTED]" if prediction.rejected else "[OK]",
        )

        return result

    async def process_and_broadcast(self) -> dict[str, Any]:
        result = self.process_buffer()
        if self._broadcaster:
            await self._broadcaster.publish(result)
        return result

    def start(self) -> None:
        self._running = True
        logger.info("Inference pipeline started")

    def stop(self) -> None:
        self._running = False
        self._buffer.clear()
        logger.info("Inference pipeline stopped")
