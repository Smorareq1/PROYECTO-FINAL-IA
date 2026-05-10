from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import torch

from src.audio.features import MFCCExtractor
from src.audio.vad import detect_speech
from src.audio.normalization import normalize_amplitude
from src.models.base import BaseModel
from src.utils.timer import timer
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BenchmarkResult:
    stage: str
    times_ms: list[float] = field(default_factory=list)

    @property
    def mean_ms(self) -> float:
        return statistics.mean(self.times_ms) if self.times_ms else 0.0

    @property
    def p95_ms(self) -> float:
        if not self.times_ms:
            return 0.0
        sorted_times = sorted(self.times_ms)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    @property
    def min_ms(self) -> float:
        return min(self.times_ms) if self.times_ms else 0.0

    @property
    def max_ms(self) -> float:
        return max(self.times_ms) if self.times_ms else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "mean_ms": round(self.mean_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "n_runs": len(self.times_ms),
        }


def benchmark_pipeline(
    waveforms: list[np.ndarray],
    extractor: MFCCExtractor,
    cnn_model: BaseModel,
    lstm_model: BaseModel | None = None,
    sample_rate: int = 16000,
    n_warmup: int = 3,
) -> list[BenchmarkResult]:
    vad_bench = BenchmarkResult(stage="vad")
    mfcc_bench = BenchmarkResult(stage="mfcc")
    cnn_bench = BenchmarkResult(stage="cnn_inference")
    lstm_bench = BenchmarkResult(stage="lstm_inference")
    total_bench = BenchmarkResult(stage="total")

    cnn_model.eval()
    if lstm_model:
        lstm_model.eval()

    all_waves = waveforms[:n_warmup] + waveforms

    for i, wav in enumerate(all_waves):
        is_warmup = i < n_warmup

        with timer() as t_total:
            with timer() as t_vad:
                start, end = detect_speech(wav, sample_rate)
                speech = normalize_amplitude(wav[start:end])

            with timer() as t_mfcc:
                waveform_t = torch.from_numpy(speech).unsqueeze(0)
                mfcc = extractor.extract(waveform_t)

            with timer() as t_cnn:
                with torch.no_grad():
                    x = mfcc.unsqueeze(1)
                    _ = cnn_model(x)

            if lstm_model:
                with timer() as t_lstm:
                    with torch.no_grad():
                        x_lstm = mfcc.permute(0, 2, 1)
                        _ = lstm_model(x_lstm)

        if not is_warmup:
            vad_bench.times_ms.append(t_vad.elapsed_ms)
            mfcc_bench.times_ms.append(t_mfcc.elapsed_ms)
            cnn_bench.times_ms.append(t_cnn.elapsed_ms)
            if lstm_model:
                lstm_bench.times_ms.append(t_lstm.elapsed_ms)
            total_bench.times_ms.append(t_total.elapsed_ms)

    results = [vad_bench, mfcc_bench, cnn_bench]
    if lstm_model and lstm_bench.times_ms:
        results.append(lstm_bench)
    results.append(total_bench)

    for r in results:
        logger.info(
            "%-20s mean=%.2f ms  p95=%.2f ms  [%d runs]",
            r.stage, r.mean_ms, r.p95_ms, len(r.times_ms),
        )

    return results
