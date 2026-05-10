from __future__ import annotations

import torch
import torch.nn as nn
import torchaudio.transforms as T


class MFCCExtractor(nn.Module):
    def __init__(
        self,
        sample_rate: int = 16000,
        n_mfcc: int = 13,
        n_fft: int = 512,
        n_mels: int = 40,
        hop_length: int = 160,
        f_min: float = 50.0,
        f_max: float = 8000.0,
    ) -> None:
        super().__init__()
        self.mfcc = T.MFCC(
            sample_rate=sample_rate,
            n_mfcc=n_mfcc,
            melkwargs={
                "n_fft": n_fft,
                "n_mels": n_mels,
                "hop_length": hop_length,
                "f_min": f_min,
                "f_max": f_max,
            },
        )

    def forward(self, waveform: torch.Tensor) -> torch.Tensor:
        return self.mfcc(waveform)

    def extract(self, waveform: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            return self.forward(waveform)

    @staticmethod
    def from_config(cfg: dict[str, object]) -> MFCCExtractor:
        return MFCCExtractor(
            sample_rate=int(cfg.get("sample_rate", 16000)),  # type: ignore[arg-type]
            n_mfcc=int(cfg.get("n_mfcc", 13)),  # type: ignore[arg-type]
            n_fft=int(cfg.get("n_fft", 512)),  # type: ignore[arg-type]
            n_mels=int(cfg.get("n_mels", 40)),  # type: ignore[arg-type]
            hop_length=int(cfg.get("hop_length", 160)),  # type: ignore[arg-type]
            f_min=float(cfg.get("f_min", 50.0)),  # type: ignore[arg-type]
            f_max=float(cfg.get("f_max", 8000.0)),  # type: ignore[arg-type]
        )
