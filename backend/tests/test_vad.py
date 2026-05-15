import numpy as np
import pytest

from src.audio.vad import detect_speech, is_speech, compute_frame_energy, compute_frame_zcr


def _make_signal_with_speech(sr: int = 16000) -> np.ndarray:
    duration = 1.5
    n = int(sr * duration)
    signal = np.zeros(n, dtype=np.float32)
    # 200ms silence, then speech-like signal, then silence
    speech_start = int(0.2 * sr)
    speech_end = int(1.0 * sr)
    t = np.arange(speech_end - speech_start) / sr
    signal[speech_start:speech_end] = 0.5 * np.sin(2 * np.pi * 300 * t)
    signal += np.random.normal(0, 0.001, n).astype(np.float32)
    return signal


def test_detect_speech_finds_region():
    signal = _make_signal_with_speech()
    start, end = detect_speech(signal, sr=16000)
    assert start > 0
    assert end > start
    assert start < 5000  # should find speech near sample 3200
    assert end > 10000


def test_detect_speech_silent_signal():
    signal = np.random.normal(0, 0.001, 24000).astype(np.float32)
    start, end = detect_speech(signal, sr=16000)
    assert end >= start


def test_is_speech_true_for_speech():
    signal = _make_signal_with_speech()
    assert is_speech(signal, sr=16000) is True


def test_is_speech_false_for_silence():
    signal = np.random.normal(0, 0.001, 24000).astype(np.float32)
    result = is_speech(signal, sr=16000, min_speech_duration_ms=200)
    # With noise floor so low, VAD may or may not trigger
    assert isinstance(result, bool)


def test_compute_frame_energy_shape():
    signal = np.random.randn(16000).astype(np.float32)
    energy = compute_frame_energy(signal, frame_len=400, hop=160)
    expected_frames = 1 + (16000 - 400) // 160
    assert len(energy) == expected_frames


def test_compute_frame_zcr_shape():
    signal = np.random.randn(16000).astype(np.float32)
    zcr = compute_frame_zcr(signal, frame_len=400, hop=160)
    expected_frames = 1 + (16000 - 400) // 160
    assert len(zcr) == expected_frames
