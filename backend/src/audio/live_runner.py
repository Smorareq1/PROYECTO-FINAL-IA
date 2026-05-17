"""Orquestador de captura en vivo: mic -> VAD -> pipeline -> WS.

Corre un thread que tira chunks del micrófono y los procesa. Los resultados se
publican de vuelta al loop principal de asyncio usando run_coroutine_threadsafe.
"""
from __future__ import annotations

import asyncio
import threading
import time
from typing import Any, Awaitable, Callable

import numpy as np

from src.audio.capture import MicrophoneCapture
from src.audio.vad import StreamingVADGate
from src.inference.pipeline import InferencePipeline
from src.utils.logger import get_logger

logger = get_logger(__name__)

PublishFn = Callable[[dict[str, Any]], Awaitable[None]]

SAMPLE_RATE = 16_000
CHUNK_MS = 32
CALIBRATION_S = 0.6
WINDOW_S = 2.0
AUDIO_REPORT_EVERY_S = 2.0

# Cooldown por comando: cuánto tiempo ignoramos audio nuevo tras la predicción.
# Los comandos que activan buzzer duran ~1-2s y se cuelan por el mic.
DEFAULT_COOLDOWN_S = 0.6
COMMAND_COOLDOWN_S: dict[str, float] = {
    "alarma": 2.2,       # alarma(): 4 * 360 ms ≈ 1.4s + margen
    "tono": 1.2,         # tonoCompuesto(): ~700 ms + margen
    "rechazo": 1.0,      # estadoRechazo(): ~500 ms + margen
    "procesando": 1.0,   # estadoProcesando(): ~500 ms + margen
}


class LiveAudioRunner:
    def __init__(self, pipeline: InferencePipeline, publish: PublishFn) -> None:
        self._pipeline = pipeline
        self._publish = publish

        self._mic: MicrophoneCapture | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None

        self._current_device: int | None = None
        self._current_device_name: str | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def current_device_name(self) -> str | None:
        return self._current_device_name

    @staticmethod
    def list_devices() -> list[dict[str, Any]]:
        try:
            import sounddevice as sd  # type: ignore[import-not-found]
        except Exception as e:  # noqa: BLE001
            logger.warning("sounddevice no disponible: %s", e)
            return []
        try:
            default_input = (
                sd.default.device[0]
                if isinstance(sd.default.device, (list, tuple))
                else sd.default.device
            )
        except Exception:
            default_input = None

        # Windows expone el mismo mic a través de varios host APIs (MME, WASAPI, DirectSound, ...).
        # Filtramos por el host API por defecto del SO para no mostrar duplicados.
        try:
            default_hostapi = sd.default.hostapi
        except Exception:
            default_hostapi = None

        devices: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        for idx, d in enumerate(sd.query_devices()):
            if d.get("max_input_channels", 0) < 1:
                continue

            hostapi = d.get("hostapi")
            # Si conocemos el host API por defecto, restringimos a ese.
            if default_hostapi is not None and hostapi != default_hostapi:
                continue

            name = str(d.get("name", f"device {idx}")).strip()
            if name in seen_names:
                continue
            seen_names.add(name)

            devices.append(
                {
                    "index": idx,
                    "name": name,
                    "channels": int(d.get("max_input_channels", 0)),
                    "default_sample_rate": float(d.get("default_samplerate", 0.0) or 0.0),
                    "is_default": (default_input == idx),
                }
            )
        return devices

    def start(self, device: int | None = None) -> dict[str, Any]:
        if self.is_running:
            return {"device": self._current_device, "device_name": self._current_device_name}

        self._loop = asyncio.get_running_loop()
        self._stop_event.clear()

        self._mic = MicrophoneCapture(
            sample_rate=SAMPLE_RATE, chunk_ms=CHUNK_MS, device=device
        )
        self._mic.start()
        self._current_device = device
        self._current_device_name = self._resolve_device_name(device)

        self._thread = threading.Thread(
            target=self._run, name="LiveAudioRunner", daemon=True
        )
        self._thread.start()
        logger.info(
            "LiveAudioRunner iniciado (device=%s, name=%r)",
            device,
            self._current_device_name,
        )
        return {"device": device, "device_name": self._current_device_name}

    def stop(self) -> None:
        if not self._thread:
            return
        self._stop_event.set()
        try:
            self._thread.join(timeout=3.0)
        finally:
            self._thread = None
        if self._mic is not None:
            self._mic.stop()
            self._mic = None
        self._loop = None
        logger.info("LiveAudioRunner detenido")

    def _resolve_device_name(self, device: int | None) -> str:
        try:
            import sounddevice as sd  # type: ignore[import-not-found]
        except Exception:
            return f"device {device}" if device is not None else "default"
        try:
            info = sd.query_devices(device if device is not None else sd.default.device[0])
            return str(info.get("name", f"device {device}"))
        except Exception:
            return f"device {device}" if device is not None else "default"

    def _publish_sync(self, payload: dict[str, Any]) -> None:
        if self._loop is None or not self._loop.is_running():
            return
        try:
            asyncio.run_coroutine_threadsafe(self._publish(payload), self._loop)
        except Exception:
            logger.exception("No se pudo publicar payload por WS")

    def _emit_system(self, event: str, message: str, **detail: Any) -> None:
        self._publish_sync(
            {"event": event, "origin": "back", "message": message, "detail": detail}
        )

    def _run(self) -> None:
        mic = self._mic
        if mic is None:
            return

        self._emit_system(
            "mic_start",
            f"Backend escuchando ({self._current_device_name})",
            device=self._current_device,
            device_name=self._current_device_name,
        )

        # Calibración del piso de ruido
        time.sleep(CALIBRATION_S)
        ambient = mic.drain()
        vad = StreamingVADGate(sr=SAMPLE_RATE, silence_ms=350, min_speech_ms=250, frame_ms=25)
        if ambient.size > 0:
            vad.calibrate(ambient)
            self._pipeline.set_noise_profile(
                ambient[-SAMPLE_RATE:] if ambient.size > SAMPLE_RATE else ambient
            )
            self._emit_system(
                "vad_calibrated",
                f"Piso de ruido calibrado ({CALIBRATION_S:.1f}s de ambiente)",
                noise_floor=vad.noise_floor,
            )
        else:
            logger.warning("Sin audio durante calibración")

        self._pipeline.start()

        last_report = time.monotonic()
        chunks_since = 0
        samples_since = 0
        cooldown_until = 0.0

        try:
            for chunk in mic.chunks(timeout=0.5):
                if self._stop_event.is_set():
                    break

                now = time.monotonic()

                # Tras un disparo, descartamos audio para evitar reanálisis
                if now < cooldown_until:
                    continue

                self._pipeline.push_audio(chunk)
                chunks_since += 1
                samples_since += chunk.size

                if now - last_report >= AUDIO_REPORT_EVERY_S:
                    rms = float(np.sqrt(np.mean(chunk.astype(np.float64) ** 2))) if chunk.size else 0.0
                    self._emit_system(
                        "audio_recv",
                        f"Backend capturó {chunks_since} chunks ({samples_since / SAMPLE_RATE:.1f}s · RMS={rms:.3f})",
                        chunks=chunks_since,
                        seconds=round(samples_since / SAMPLE_RATE, 2),
                        rms=round(rms, 4),
                    )
                    last_report = now
                    chunks_since = 0
                    samples_since = 0

                if vad.process_chunk(chunk):
                    self._emit_system(
                        "vad_trigger",
                        f"VAD detectó fin de voz ({vad.last_trigger_speech_ms:.0f} ms)",
                        speech_ms=round(vad.last_trigger_speech_ms, 0),
                    )
                    result = self._pipeline.process_buffer(window_seconds=WINDOW_S)
                    self._publish_sync(result)
                    # Limpiamos el buffer y arrancamos cooldown para no reanalizar lo mismo.
                    # Para comandos que activan el buzzer, el cooldown es más largo
                    # para evitar que el sonido del buzzer se re-clasifique.
                    cmd = str(result.get("command", ""))
                    rejected = bool(result.get("rejected", False))
                    cooldown_s = (
                        DEFAULT_COOLDOWN_S
                        if rejected
                        else COMMAND_COOLDOWN_S.get(cmd, DEFAULT_COOLDOWN_S)
                    )
                    self._pipeline.clear_buffer()
                    vad.reset()
                    cooldown_until = time.monotonic() + cooldown_s
        except Exception:
            logger.exception("Error en LiveAudioRunner loop")
        finally:
            self._pipeline.stop()
            self._emit_system("mic_stop", "Backend detuvo la captura")
