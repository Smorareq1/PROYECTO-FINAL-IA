"""Checklist pre-demo.

Ejecuta 6 chequeos antes de la defensa. El script termina con codigo de salida
no-cero si algun chequeo falla. Cada chequeo imprime su estado en stdout.

Uso:
    python -m scripts.predemo_checklist
    python -m scripts.predemo_checklist --skip-arduino --skip-network
"""
from __future__ import annotations

import argparse
import socket
import sys
import time
from pathlib import Path

import numpy as np

from src.audio.capture import MicrophoneCapture
from src.audio.features import MFCCExtractor
from src.audio.vad import is_speech
from src.domain.commands import N_CLASSES
from src.hardware.serial_link import SerialLink, find_arduino_port
from src.inference.predictor import CNNPredictor
from src.models.factory import load_model, create_model
from src.utils.config_loader import load_yaml
from src.utils.logger import get_logger

logger = get_logger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIGS_DIR = REPO_ROOT / "configs"
MODELS_DIR = REPO_ROOT / "models"


class Check:
    def __init__(self, name: str) -> None:
        self.name = name
        self.passed = False
        self.message = ""

    def ok(self, msg: str) -> None:
        self.passed = True
        self.message = msg

    def fail(self, msg: str) -> None:
        self.passed = False
        self.message = msg


def has_internet(timeout_s: float = 1.0) -> bool:
    for host, port in (("1.1.1.1", 53), ("8.8.8.8", 53)):
        try:
            with socket.create_connection((host, port), timeout=timeout_s):
                return True
        except OSError:
            continue
    return False


def check_offline_mode() -> Check:
    c = Check("Modo offline / sin red")
    if has_internet():
        c.fail("Hay conexion a internet. Activa modo avion antes de la defensa.")
    else:
        c.ok("Sin conectividad de red — OK")
    return c


def check_microphone() -> Check:
    c = Check("Microfono disponible")
    try:
        devices = MicrophoneCapture.list_input_devices()
    except Exception as exc:  # pragma: no cover
        c.fail(f"sounddevice error: {exc}")
        return c
    if not devices:
        c.fail("No se detectan dispositivos de entrada.")
        return c
    names = [str(d.get("name", "?")) for d in devices[:3]]
    c.ok(f"{len(devices)} dispositivos: {names}")
    return c


def check_ambient_rms(rms_max: float = 0.04, duration_s: float = 1.0) -> Check:
    c = Check("Piso de ruido ambiente")
    try:
        with MicrophoneCapture(sample_rate=16_000, chunk_ms=32) as mic:
            time.sleep(duration_s + 0.2)
            audio = mic.drain()
    except Exception as exc:  # pragma: no cover
        c.fail(f"No se pudo capturar audio: {exc}")
        return c

    if audio.size == 0:
        c.fail("Captura vacia.")
        return c
    rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
    if rms > rms_max:
        c.fail(f"Ambiente ruidoso: RMS={rms:.4f} > {rms_max:.4f}")
    else:
        c.ok(f"RMS ambiente = {rms:.4f} (< {rms_max:.4f})")
    return c


def check_arduino() -> Check:
    c = Check("Arduino conectado")
    port = find_arduino_port()
    if not port:
        c.fail("No se detecta Arduino en puertos serie.")
        return c
    link = SerialLink(port)
    try:
        link.open()
    except Exception as exc:
        c.fail(f"Error al abrir {port}: {exc}")
        return c
    finally:
        try:
            link.close()
        except Exception:  # pragma: no cover
            pass
    c.ok(f"Puerto serial abierto en {port} @ 115200")
    return c


def check_models() -> Check:
    c = Check("Modelo entrenado")
    cnn_path = MODELS_DIR / "cnn_base" / "model.pt"
    if not cnn_path.exists():
        c.fail(f"Falta: {cnn_path}")
    else:
        c.ok(f"CNN={cnn_path.stat().st_size} B")
    return c


def check_latency(target_p95_ms: float = 250.0, n_iter: int = 20) -> Check:
    c = Check(f"Latencia p95 < {target_p95_ms:.0f} ms")
    preproc_cfg = load_yaml(CONFIGS_DIR / "preprocessing.yaml")
    extractor = MFCCExtractor.from_config(preproc_cfg)

    cnn_path = MODELS_DIR / "cnn_base" / "model.pt"
    try:
        if cnn_path.exists():
            cnn = load_model("cnn", cnn_path, n_classes=N_CLASSES, n_mfcc=13)
        else:
            cnn = create_model("cnn", n_classes=N_CLASSES, n_mfcc=13)
    except Exception as exc:  # pragma: no cover
        c.fail(f"No se pudo cargar el modelo: {exc}")
        return c

    from src.domain.commands import ALL_CLASS_NAMES
    cnn_pred = CNNPredictor(cnn, ALL_CLASS_NAMES)

    import torch

    rng = np.random.default_rng(0)
    sr = int(preproc_cfg.get("sample_rate", 16_000))
    duration = 2.0
    latencies: list[float] = []
    # warm-up
    for _ in range(2):
        wav = torch.from_numpy(rng.standard_normal(int(duration * sr)).astype(np.float32)).unsqueeze(0)
        mfcc = extractor.extract(wav).squeeze(0)
        _ = cnn_pred.predict(mfcc)

    for _ in range(n_iter):
        wav = torch.from_numpy(rng.standard_normal(int(duration * sr)).astype(np.float32)).unsqueeze(0)
        t0 = time.perf_counter()
        mfcc = extractor.extract(wav).squeeze(0)
        _ = cnn_pred.predict(mfcc)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    arr = np.asarray(latencies)
    p50 = float(np.percentile(arr, 50))
    p95 = float(np.percentile(arr, 95))
    msg = f"p50={p50:.1f} ms, p95={p95:.1f} ms (objetivo {target_p95_ms:.0f} ms)"
    if p95 > target_p95_ms:
        c.fail(msg)
    else:
        c.ok(msg)
    return c


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-network", action="store_true", help="No verificar modo offline")
    parser.add_argument("--skip-arduino", action="store_true", help="No verificar Arduino")
    parser.add_argument("--skip-ambient", action="store_true", help="No medir ruido ambiente")
    parser.add_argument("--skip-latency", action="store_true", help="No medir latencia")
    parser.add_argument("--target-p95-ms", type=float, default=250.0)
    parser.add_argument("--rms-max", type=float, default=0.04)
    args = parser.parse_args()

    print("\n=== Pre-demo checklist ===\n")

    checks: list[Check] = []
    if not args.skip_network:
        checks.append(check_offline_mode())
    checks.append(check_microphone())
    if not args.skip_ambient:
        checks.append(check_ambient_rms(rms_max=args.rms_max))
    if not args.skip_arduino:
        checks.append(check_arduino())
    checks.append(check_models())
    if not args.skip_latency:
        checks.append(check_latency(target_p95_ms=args.target_p95_ms))

    failed = 0
    for c in checks:
        marker = "OK " if c.passed else "FAIL"
        print(f"  [{marker}] {c.name}: {c.message}")
        if not c.passed:
            failed += 1

    print()
    if failed == 0:
        print("Sistema listo para la demo.")
        sys.exit(0)
    else:
        print(f"{failed} chequeo(s) fallaron. Revisa antes de empezar.")
        sys.exit(1)


if __name__ == "__main__":
    main()
