import torch
import pytest

from src.audio.features import MFCCExtractor


def test_mfcc_output_shape_1s():
    extractor = MFCCExtractor(sample_rate=16000, n_mfcc=13, hop_length=160)
    waveform = torch.randn(1, 16000)
    mfcc = extractor.extract(waveform)
    assert mfcc.shape[0] == 1
    assert mfcc.shape[1] == 13
    assert mfcc.shape[2] == 101


def test_mfcc_output_shape_1_5s():
    extractor = MFCCExtractor(sample_rate=16000, n_mfcc=13, hop_length=160)
    waveform = torch.randn(1, 24000)
    mfcc = extractor.extract(waveform)
    assert mfcc.shape[1] == 13
    assert mfcc.shape[2] == 151


def test_mfcc_batch():
    extractor = MFCCExtractor(sample_rate=16000, n_mfcc=13)
    waveform = torch.randn(4, 16000)
    mfcc = extractor.extract(waveform)
    assert mfcc.shape[0] == 4
    assert mfcc.shape[1] == 13


def test_mfcc_from_config():
    cfg = {
        "sample_rate": 16000,
        "n_mfcc": 13,
        "n_fft": 512,
        "n_mels": 40,
        "hop_length": 160,
        "f_min": 50,
        "f_max": 8000,
    }
    extractor = MFCCExtractor.from_config(cfg)
    waveform = torch.randn(1, 16000)
    mfcc = extractor.extract(waveform)
    assert mfcc.shape == (1, 13, 101)


def test_mfcc_deterministic():
    extractor = MFCCExtractor()
    waveform = torch.randn(1, 16000)
    mfcc1 = extractor.extract(waveform)
    mfcc2 = extractor.extract(waveform)
    assert torch.allclose(mfcc1, mfcc2)
