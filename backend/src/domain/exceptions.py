from __future__ import annotations


class DomainError(Exception):
    pass


class AudioCaptureError(DomainError):
    pass


class VADError(DomainError):
    pass


class ModelLoadError(DomainError):
    pass


class InferenceError(DomainError):
    pass


class SerialConnectionError(DomainError):
    pass


class CommandProtocolError(DomainError):
    pass


class ConfigurationError(DomainError):
    pass
