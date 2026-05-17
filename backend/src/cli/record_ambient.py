"""Graba audio ambiental continuo y lo trocea en clips de 2 s para `ruido_fondo`.

Uso:
    python -m src.cli.record_ambient \\
        --environment laboratorio \\
        --device dji_mic_mini \\
        --duration-seconds 120 \\
        --chunk-seconds 2

Recomendacion: correr 3-4 veces (uno por ambiente distinto: salon_silencioso,
laboratorio, pasillo_ruidoso, cocina) hasta acumular >=200 clips totales.

Durante la grabacion NADIE habla comandos. Es ruido ambiente puro
(HVAC, ventiladores, conversacion lejana, AC, trafico distante).
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

from src.cli.record import (
    MANIFEST_FIELDS,
    SAMPLE_RATE,
    append_manifest_row,
    next_clip_id,
    play_tone,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

CLASS_NAME = "ruido_fondo"

# data root canonico, relativo al archivo del script (backend/data/), no al cwd
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_ROOT = BACKEND_ROOT / "data"


def _record_continuous(duration_s: float) -> np.ndarray:
    n_samples = int(duration_s * SAMPLE_RATE)
    audio = sd.rec(n_samples, samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocking=True)
    return np.asarray(audio, dtype=np.float32).flatten()


def _chunk(signal: np.ndarray, chunk_seconds: float, overlap: float) -> list[np.ndarray]:
    chunk_samples = int(chunk_seconds * SAMPLE_RATE)
    if chunk_samples <= 0:
        raise ValueError("chunk_seconds debe ser > 0")
    stride = max(1, int(chunk_samples * (1.0 - overlap)))
    chunks: list[np.ndarray] = []
    i = 0
    while i + chunk_samples <= len(signal):
        chunks.append(signal[i : i + chunk_samples].astype(np.float32, copy=False))
        i += stride
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--environment",
        choices=["salon_silencioso", "laboratorio", "pasillo_ruidoso"],
        required=True,
    )
    parser.add_argument("--device", default="dji_mic_mini", help="Identificador del microfono.")
    parser.add_argument(
        "--duration-seconds",
        type=float,
        default=120.0,
        help="Duracion total de la grabacion continua (s). 120 s = ~60 clips de 2 s.",
    )
    parser.add_argument(
        "--chunk-seconds",
        type=float,
        default=2.0,
        help="Duracion de cada clip resultante (s).",
    )
    parser.add_argument(
        "--overlap",
        type=float,
        default=0.0,
        help="Overlap entre chunks consecutivos (0.0..0.5). 0 = sin solapar.",
    )
    parser.add_argument(
        "--clipping-peak",
        type=float,
        default=0.95,
        help="Clips con peak por encima de este umbral se descartan (default 0.95).",
    )
    parser.add_argument(
        "--data-root",
        default=str(DEFAULT_DATA_ROOT),
        help=f"Raiz del corpus. Default: {DEFAULT_DATA_ROOT}",
    )
    parser.add_argument("--language", default="es")
    parser.add_argument(
        "--countdown",
        type=int,
        default=5,
        help="Segundos de cuenta regresiva con beeps antes de empezar.",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="No pedir ENTER al inicio (modo no-interactivo para scripting).",
    )
    args = parser.parse_args()

    data_root = Path(args.data_root)
    manifest_path = data_root / "manifests" / "corpus.csv"

    devices = sd.query_devices()
    print("\nDispositivos de entrada detectados:")
    for i, d in enumerate(devices):
        if d.get("max_input_channels", 0) >= 1:
            print(
                f"  [{i}] {d['name']}  ({d['max_input_channels']} ch, "
                f"default sr={d.get('default_samplerate')})"
            )

    expected_chunks = max(0, int(args.duration_seconds // args.chunk_seconds))
    print()
    print("=" * 60)
    print(f"  GRABACION AMBIENTAL — clase '{CLASS_NAME}'")
    print(f"  Ambiente:    {args.environment}")
    print(f"  Dispositivo: {args.device}")
    print(f"  Duracion:    {args.duration_seconds:.0f} s continuos")
    print(f"  Chunks:      ~{expected_chunks} clips de {args.chunk_seconds:.1f} s")
    print("=" * 60)
    print()
    print("  IMPORTANTE: Durante la grabacion NADIE habla comandos.")
    print("  Solo ruido ambiente (HVAC, ventiladores, conversacion lejana ok).")
    print()

    if not args.no_confirm:
        try:
            input("  ENTER cuando esten listos (Ctrl+C aborta)... ")
        except (EOFError, KeyboardInterrupt):
            print("Abortado.")
            return

    # cuenta regresiva audible
    for n in range(args.countdown, 0, -1):
        sys.stdout.write(f"  {n}... ")
        sys.stdout.flush()
        play_tone(600.0, 0.08, volume=0.18)
        time.sleep(1.0 - 0.08)
    print(" GRABANDO")
    play_tone(900.0, 0.15)

    t0 = time.perf_counter()
    audio = _record_continuous(args.duration_seconds)
    elapsed = time.perf_counter() - t0
    play_tone(440.0, 0.12)
    print(f"  Grabacion completada en {elapsed:.1f} s (samples={audio.size}).")

    chunks = _chunk(audio, args.chunk_seconds, args.overlap)
    print(f"  Troceado: {len(chunks)} candidatos de {args.chunk_seconds:.1f} s.")

    clip_dir = data_root / "raw" / CLASS_NAME
    clip_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    discarded = 0
    discarded_reasons: dict[str, int] = {}

    def _bump(reason: str) -> None:
        discarded_reasons[reason] = discarded_reasons.get(reason, 0) + 1

    for idx, chunk in enumerate(chunks, start=1):
        peak = float(np.max(np.abs(chunk))) if chunk.size else 0.0
        rms = float(np.sqrt(np.mean(chunk.astype(np.float64) ** 2))) if chunk.size else 0.0

        if peak > args.clipping_peak:
            discarded += 1
            _bump("clipping")
            continue
        if rms < 1e-5:
            discarded += 1
            _bump("silencio_total")
            continue

        clip_id = next_clip_id(manifest_path)
        fname = f"amb_{args.environment}_{idx:03d}_{clip_id:06d}.wav"
        fpath = clip_dir / fname
        sf.write(fpath, chunk, SAMPLE_RATE, subtype="PCM_16")

        row = {
            "clip_id": clip_id,
            "filepath": str(fpath.relative_to(data_root)).replace("\\", "/"),
            "class": CLASS_NAME,
            "speaker_id": "",
            "speaker_gender": "",
            "speaker_age_range": "",
            "environment": args.environment,
            "device": args.device,
            "language": args.language,
            "duration_s": round(len(chunk) / SAMPLE_RATE, 3),
            "peak": round(peak, 4),
            "rms": round(rms, 4),
            "snr_db_est": 0.0,
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "split": "",
        }
        append_manifest_row(manifest_path, row)
        saved += 1

    print()
    print("=" * 60)
    print(f"  RESUMEN — '{args.environment}'")
    print(f"  Guardados:  {saved} clips de '{CLASS_NAME}'")
    print(f"  Descartados: {discarded}")
    for reason, count in discarded_reasons.items():
        print(f"    - {reason}: {count}")
    print(f"  Manifest:    {manifest_path}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - CLI defensivo
        logger.exception("Fallo en record_ambient.py: %s", exc)
        sys.exit(1)
