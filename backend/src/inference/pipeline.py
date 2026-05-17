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
from src.inference.predictor import CNNPredictor
from src.utils.logger import get_logger
from src.utils.timer import timer

try:  # pragma: no cover - optional runtime dependency
    import noisereduce as nr  # type: ignore[import-not-found]
except Exception:  # noqa: BLE001
    nr = None  # type: ignore[assignment]

logger = get_logger(__name__)


class InferencePipeline:
    def __init__(
        self,
        feature_extractor: MFCCExtractor,
        cnn_predictor: CNNPredictor,
        decision: DecisionLayer,
        actuator: Actuator,
        broadcaster: EventBroadcaster | None = None,
        sample_rate: int = 16000,
        buffer_duration: float = 3.0,
        enable_noise_suppression: bool = False,
        snr_reject_db: float = 8.0,
    ) -> None:
        self._extractor = feature_extractor
        self._cnn = cnn_predictor
        self._decision = decision
        self._actuator = actuator
        self._broadcaster = broadcaster
        self._sr = sample_rate
        self._buffer = CircularAudioBuffer(buffer_duration, sample_rate)
        self._running = False
        self._enable_noise_suppression = bool(enable_noise_suppression)
        self._snr_reject_db = float(snr_reject_db)
        self._noise_profile: np.ndarray | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    def push_audio(self, chunk: np.ndarray) -> None:
        self._buffer.push(chunk)

    def clear_buffer(self) -> None:
        self._buffer.clear()

    def set_noise_profile(self, ambient_audio: np.ndarray) -> None:
        """Guarda una muestra ambiental para alimentar a noisereduce."""
        if ambient_audio.size == 0:
            self._noise_profile = None
            return
        self._noise_profile = ambient_audio.astype(np.float32, copy=False)

    def _estimate_snr_db(self, speech: np.ndarray) -> float:
        speech_power = float(np.mean(speech.astype(np.float64) ** 2)) + 1e-12
        if self._noise_profile is not None and self._noise_profile.size > 0:
            noise_power = float(np.mean(self._noise_profile.astype(np.float64) ** 2)) + 1e-12
        else:
            tail = speech[: min(len(speech), int(0.05 * self._sr))]
            noise_power = float(np.mean(tail.astype(np.float64) ** 2)) + 1e-12
        return 10.0 * float(np.log10(speech_power / noise_power))

    def process_buffer(self, window_seconds: float | None = None) -> dict[str, Any]:
        window = self._buffer.get_latest(window_seconds)

        if len(window) == 0 or not is_speech(window, self._sr):
            return {"rejected": True, "reason": "no_speech", "command": Command.RUIDO_FONDO.value, "confidence": 0.0, "latency_ms": 0.0}

        start, end = detect_speech(window, self._sr)
        speech = window[start:end]

        if (
            self._enable_noise_suppression
            and nr is not None
            and self._noise_profile is not None
            and self._noise_profile.size > 0
        ):
            try:
                speech = nr.reduce_noise(
                    y=speech, sr=self._sr, y_noise=self._noise_profile, stationary=False,
                ).astype(np.float32)
            except Exception:  # pragma: no cover - defensivo
                logger.exception("noisereduce fallo; usando senal sin filtrar")

        speech = normalize_amplitude(speech)

        snr_db = self._estimate_snr_db(speech)
        if snr_db < self._snr_reject_db:
            return {
                "rejected": True,
                "reason": "low_snr",
                "command": Command.RUIDO_FONDO.value,
                "confidence": 0.0,
                "latency_ms": 0.0,
                "snr_db": round(snr_db, 2),
            }

        with timer() as t:
            waveform = torch.from_numpy(speech).unsqueeze(0)
            mfcc = self._extractor.extract(waveform)
            mfcc_squeezed = mfcc.squeeze(0)

            cnn_pred = self._cnn.predict(mfcc_squeezed)
            prediction: Prediction = self._decision.from_cnn(cnn_pred)

        latency_ms = t.elapsed_ms

        if prediction.is_valid():
            self._actuator.execute(prediction.command)

        result = {
            "command": prediction.command.value,
            "confidence": round(prediction.confidence, 4),
            "latency_ms": round(latency_ms, 2),
            "rejected": prediction.rejected,
            "snr_db": round(snr_db, 2),
        }

        logger.info(
            "Prediction: %s (%.2f%%) snr=%.1f dB in %.1f ms %s",
            prediction.command.value,
            prediction.confidence * 100,
            snr_db,
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
