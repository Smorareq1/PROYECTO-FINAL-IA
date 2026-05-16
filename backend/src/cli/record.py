"""Recolección guiada del corpus de voz.

Uso:
    python -m src.cli.record \\
        --speaker spk03 --gender F --age 18-25 \\
        --environment salon_silencioso --device fifine_k669 \\
        --classes all --repeats 15

Cada muestra se valida con `check_quality` y `is_speech` antes de guardarse.
La fila correspondiente se anexa a backend/data/manifests/corpus.csv.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

from src.audio.normalization import check_quality
from src.audio.vad import detect_speech, is_speech
from src.utils.logger import get_logger

logger = get_logger(__name__)

CLASSES_ARDUINO: list[str] = [
    "enciende",
    "apaga",
    "detente",
    "rojo",
    "verde",
    "azul",
    "blanco",
    "procesando",
    "rechazo",
    "alarma",
    "tono",
    "off",
]
CLASSES_NOISE: list[str] = ["ruido_fondo"]
ALL_CLASSES: list[str] = CLASSES_ARDUINO + CLASSES_NOISE

SAMPLE_RATE = 16_000
DURATION_S = 2.0
NOISE_FLOOR_SAMPLES = int(0.030 * SAMPLE_RATE)  # 30 ms al inicio como estimación de ruido


MANIFEST_FIELDS: tuple[str, ...] = (
    "clip_id",
    "filepath",
    "class",
    "speaker_id",
    "speaker_gender",
    "speaker_age_range",
    "environment",
    "device",
    "language",
    "duration_s",
    "peak",
    "rms",
    "snr_db_est",
    "recorded_at",
    "split",
)


def play_tone(freq_hz: float, duration_s: float = 0.12, volume: float = 0.25) -> None:
    n = int(SAMPLE_RATE * duration_s)
    t = np.linspace(0.0, duration_s, n, endpoint=False, dtype=np.float32)
    tone = (volume * np.sin(2.0 * np.pi * freq_hz * t)).astype(np.float32)
    try:
        sd.play(tone, SAMPLE_RATE, blocking=True)
    except Exception:
        pass


def record_clip(duration_s: float = DURATION_S, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    n_samples = int(duration_s * sample_rate)
    audio = sd.rec(n_samples, samplerate=sample_rate, channels=1, dtype="float32", blocking=True)
    return np.asarray(audio, dtype=np.float32).flatten()


def estimate_snr_db(signal: np.ndarray, vad_start: int, vad_end: int) -> float:
    if vad_end <= vad_start:
        return 0.0
    noise_samples = signal[:NOISE_FLOOR_SAMPLES] if vad_start >= NOISE_FLOOR_SAMPLES else signal[:max(1, vad_start)]
    noise_power = float(np.mean(noise_samples.astype(np.float64) ** 2)) + 1e-12
    speech_power = float(np.mean(signal[vad_start:vad_end].astype(np.float64) ** 2)) + 1e-12
    return 10.0 * float(np.log10(speech_power / noise_power))


def next_clip_id(manifest_path: Path) -> int:
    if not manifest_path.exists():
        return 1
    last = 0
    with manifest_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                last = max(last, int(row["clip_id"]))
            except (KeyError, ValueError):
                continue
    return last + 1


def append_manifest_row(manifest_path: Path, row: dict[str, object]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not manifest_path.exists() or manifest_path.stat().st_size == 0
    with manifest_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(MANIFEST_FIELDS))
        if write_header:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in MANIFEST_FIELDS})


def prompt_and_record(class_name: str, idx: int, total: int) -> np.ndarray | None:
    is_noise = class_name == "ruido_fondo"
    print()
    print(f"[{idx}/{total}]  Clase: {class_name.upper()}")
    if is_noise:
        print("  Mantenga silencio o produzca ruido ambiente (NO hable comandos).")
    else:
        print(f"  Diga claramente: \"{class_name.replace('_', ' ')}\"")
    try:
        input("  Presione ENTER para iniciar la grabacion (Ctrl+C para abortar)... ")
    except (EOFError, KeyboardInterrupt):
        return None

    time.sleep(0.4)
    play_tone(880.0, 0.10)
    audio = record_clip()
    play_tone(440.0, 0.06)

    if is_noise:
        ok = True
        msg = "ruido_fondo aceptado sin chequeo de voz"
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak > 0.95:
            ok, msg = False, f"clipping: peak={peak:.3f} > 0.95"
    else:
        ok, msg = check_quality(audio, peak_max=0.95, rms_min=0.01)
        if ok and not is_speech(audio, SAMPLE_RATE):
            ok, msg = False, "VAD no detecto voz"

    if not ok:
        print(f"  RECHAZADO: {msg}. Repita.")
        return None

    print("  OK")
    return audio


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--speaker", required=True, help="ID anonimo del hablante (ej. spk03)")
    parser.add_argument("--gender", choices=["M", "F", "X"], required=True)
    parser.add_argument("--age", choices=["18-25", "26-35", "36-50", "50+"], required=True)
    parser.add_argument(
        "--environment",
        choices=["salon_silencioso", "laboratorio", "pasillo_ruidoso"],
        required=True,
    )
    parser.add_argument("--device", default="fifine_k669", help="Identificador del microfono")
    parser.add_argument(
        "--classes",
        default="all",
        help="'all', 'arduino', 'noise' o lista CSV de clases.",
    )
    parser.add_argument("--repeats", type=int, default=15, help="Repeticiones por clase.")
    parser.add_argument("--shuffle", action="store_true", help="Aleatoriza el orden de las clases.")
    parser.add_argument("--data-root", default="backend/data", help="Raiz del corpus.")
    parser.add_argument(
        "--language",
        default="es",
        help="Idioma del corpus (default es).",
    )
    parser.add_argument("--seed", type=int, default=None, help="Semilla para barajar (opcional).")
    args = parser.parse_args()

    if args.classes == "all":
        classes = list(ALL_CLASSES)
    elif args.classes == "arduino":
        classes = list(CLASSES_ARDUINO)
    elif args.classes == "noise":
        classes = list(CLASSES_NOISE)
    else:
        classes = [c.strip() for c in args.classes.split(",") if c.strip()]
        unknown = set(classes) - set(ALL_CLASSES)
        if unknown:
            parser.error(f"Clases desconocidas: {sorted(unknown)}")

    if args.shuffle:
        rng = random.Random(args.seed)
        rng.shuffle(classes)

    data_root = Path(args.data_root)
    manifest_path = data_root / "manifests" / "corpus.csv"

    devices = sd.query_devices()
    print("\nDispositivos de entrada detectados:")
    for i, d in enumerate(devices):
        if d.get("max_input_channels", 0) >= 1:
            print(f"  [{i}] {d['name']}  ({d['max_input_channels']} ch, default sr={d.get('default_samplerate')})")
    default_in = sd.default.device
    print(f"\nDispositivo de entrada por defecto: {default_in}")
    print(f"Hablante: {args.speaker} | Genero: {args.gender} | Edad: {args.age} | Entorno: {args.environment}")
    print(f"Clases: {len(classes)}  |  Repeticiones: {args.repeats}  |  Total: {len(classes) * args.repeats}\n")

    counter_offset = next_clip_id(manifest_path) - 1
    counter = 0
    saved = 0
    total = len(classes) * args.repeats

    try:
        for cls in classes:
            clip_dir = data_root / "raw" / cls
            clip_dir.mkdir(parents=True, exist_ok=True)
            for rep in range(1, args.repeats + 1):
                counter += 1
                audio: np.ndarray | None = None
                attempts = 0
                while audio is None and attempts < 5:
                    attempts += 1
                    audio = prompt_and_record(cls, counter, total)
                if audio is None:
                    print(f"  Saltando {cls} repeticion {rep} despues de 5 intentos fallidos.")
                    continue

                clip_id = counter_offset + saved + 1
                fname = f"{args.speaker}_s{rep:02d}_{clip_id:06d}.wav"
                fpath = clip_dir / fname
                sf.write(fpath, audio, SAMPLE_RATE, subtype="PCM_16")

                if cls == "ruido_fondo":
                    vad_s, vad_e = 0, len(audio)
                else:
                    vad_s, vad_e = detect_speech(audio, SAMPLE_RATE)

                row = {
                    "clip_id": clip_id,
                    "filepath": str(fpath.relative_to(data_root)).replace("\\", "/"),
                    "class": cls,
                    "speaker_id": args.speaker if cls != "ruido_fondo" else "",
                    "speaker_gender": args.gender if cls != "ruido_fondo" else "",
                    "speaker_age_range": args.age if cls != "ruido_fondo" else "",
                    "environment": args.environment,
                    "device": args.device,
                    "language": args.language,
                    "duration_s": round(len(audio) / SAMPLE_RATE, 3),
                    "peak": round(float(np.max(np.abs(audio))), 4),
                    "rms": round(float(np.sqrt(np.mean(audio.astype(np.float64) ** 2))), 4),
                    "snr_db_est": round(estimate_snr_db(audio, vad_s, vad_e), 2),
                    "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "split": "",
                }
                append_manifest_row(manifest_path, row)
                saved += 1
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")

    print(f"\nGuardados {saved} clips en {data_root / 'raw'}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - CLI defensivo
        logger.exception("Fallo en record.py: %s", exc)
        sys.exit(1)
