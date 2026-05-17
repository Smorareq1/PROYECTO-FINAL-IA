"""Sesion multi-hablante con cadencia automatica para los 12 comandos del Arduino.

Una sola corrida ejecuta TODOS los hablantes en serie, sin presionar ENTER por clip.
Para `ruido_fondo` usar `record_ambient.py`.

Uso tipico (3 integrantes en una tarde):
    python -m src.cli.record_session \\
        --speakers "spk01:F:18-25,spk02:M:18-25,spk03:M:18-25" \\
        --environment salon_silencioso \\
        --device dji_mic_mini \\
        --reps 40 --shuffle --seed 42

Atajos:
    --reps 5           # smoke test rapido (3 voces x 12 clases x 5 = 180 clips)
    --countdown 2      # cuenta regresiva mas corta entre reps
    --no-calibration   # saltar las 2 tomas de prueba al inicio de cada hablante
"""
from __future__ import annotations

import argparse
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
from src.cli.record import (
    CLASSES_ARDUINO,
    DURATION_S,
    MANIFEST_FIELDS,
    NOISE_FLOOR_SAMPLES,
    SAMPLE_RATE,
    append_manifest_row,
    estimate_snr_db,
    next_clip_id,
    play_tone,
    record_clip,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# data root canonico, relativo al archivo del script (backend/data/), no al cwd
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_ROOT = BACKEND_ROOT / "data"


def _parse_speakers(raw: str) -> list[tuple[str, str, str]]:
    """Parsea 'spk01:F:18-25,spk02:M:26-35' -> [(spk01, F, 18-25), ...]."""
    speakers: list[tuple[str, str, str]] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        parts = [p.strip() for p in token.split(":")]
        if len(parts) != 3:
            raise argparse.ArgumentTypeError(
                f"Hablante invalido {token!r}: formato esperado 'id:gender:age_range'"
            )
        spk_id, gender, age = parts
        if gender not in {"M", "F", "X"}:
            raise argparse.ArgumentTypeError(f"Gender invalido {gender!r}: usar M/F/X")
        if age not in {"18-25", "26-35", "36-50", "50+"}:
            raise argparse.ArgumentTypeError(
                f"Age range invalido {age!r}: usar 18-25 / 26-35 / 36-50 / 50+"
            )
        speakers.append((spk_id, gender, age))
    if not speakers:
        raise argparse.ArgumentTypeError("--speakers no puede estar vacio")
    return speakers


def _print_box(lines: list[str]) -> None:
    width = max(len(line) for line in lines) + 4
    print()
    print("=" * width)
    for line in lines:
        print(f"  {line}")
    print("=" * width)


def _countdown(seconds: int) -> None:
    """Imprime '3... 2... 1...' inline, una linea actualizada."""
    for n in range(seconds, 0, -1):
        sys.stdout.write(f"{n}... ")
        sys.stdout.flush()
        time.sleep(1.0)


def _calibrate(spk_id: str) -> None:
    print(f"\n  Calibracion: 2 tomas de prueba para {spk_id} (NO se guardan).")
    for k in range(1, 3):
        print(f"  Toma {k}/2 — diga 'enciende' al beep.")
        _countdown(2)
        play_tone(880.0, 0.10)
        audio = record_clip()
        play_tone(440.0, 0.06)
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2))) if audio.size else 0.0
        warn = ""
        if peak > 0.95:
            warn = " <-- CLIPPING, baje ganancia"
        elif rms < 0.02:
            warn = " <-- senal debil, suba ganancia o acerque el mic"
        print(f"    peak={peak:.3f}  rms={rms:.3f}{warn}")
        time.sleep(0.5)


def auto_record_one(
    class_name: str, rep: int, total_reps: int, countdown: int
) -> tuple[np.ndarray | None, str]:
    """Cadencia automatica: countdown + beep + grabar + beep + validar."""
    label = class_name.replace("_", " ")
    sys.stdout.write(f"  [{rep:>3}/{total_reps}] {label!r} en ")
    sys.stdout.flush()
    _countdown(countdown)
    play_tone(880.0, 0.08)
    audio = record_clip()
    play_tone(440.0, 0.05)

    ok, msg = check_quality(audio, peak_max=0.95, rms_min=0.01)
    if ok and not is_speech(audio, SAMPLE_RATE):
        ok, msg = False, "sin voz (VAD)"
    if not ok:
        print(f" X  {msg}")
        return None, msg
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
    print(f" OK  peak={peak:.2f} rms={rms:.2f}")
    return audio, "ok"


def _persist(
    audio: np.ndarray,
    cls: str,
    rep: int,
    speaker: tuple[str, str, str],
    environment: str,
    device: str,
    language: str,
    data_root: Path,
    manifest_path: Path,
) -> None:
    spk_id, gender, age = speaker
    clip_dir = data_root / "raw" / cls
    clip_dir.mkdir(parents=True, exist_ok=True)
    clip_id = next_clip_id(manifest_path)
    fname = f"{spk_id}_s{rep:02d}_{clip_id:06d}.wav"
    fpath = clip_dir / fname
    sf.write(fpath, audio, SAMPLE_RATE, subtype="PCM_16")

    vad_s, vad_e = detect_speech(audio, SAMPLE_RATE)
    row = {
        "clip_id": clip_id,
        "filepath": str(fpath.relative_to(data_root)).replace("\\", "/"),
        "class": cls,
        "speaker_id": spk_id,
        "speaker_gender": gender,
        "speaker_age_range": age,
        "environment": environment,
        "device": device,
        "language": language,
        "duration_s": round(len(audio) / SAMPLE_RATE, 3),
        "peak": round(float(np.max(np.abs(audio))), 4),
        "rms": round(float(np.sqrt(np.mean(audio.astype(np.float64) ** 2))), 4),
        "snr_db_est": round(estimate_snr_db(audio, vad_s, vad_e), 2),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "split": "",
    }
    append_manifest_row(manifest_path, row)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--speakers",
        required=True,
        type=_parse_speakers,
        help='CSV de "id:gender:age_range" (ej. "spk01:F:18-25,spk02:M:18-25,spk03:M:26-35").',
    )
    parser.add_argument(
        "--environment",
        choices=["salon_silencioso", "laboratorio", "pasillo_ruidoso"],
        required=True,
    )
    parser.add_argument("--device", default="dji_mic_mini", help="Identificador del microfono.")
    parser.add_argument("--reps", type=int, default=40, help="Repeticiones por clase por hablante.")
    parser.add_argument(
        "--countdown", type=int, default=3, help="Segundos de cuenta regresiva antes de cada clip."
    )
    parser.add_argument(
        "--inter-rep-sleep",
        type=float,
        default=0.8,
        help="Pausa (s) despues de guardar un clip antes del siguiente.",
    )
    parser.add_argument(
        "--inter-class-sleep",
        type=float,
        default=5.0,
        help="Pausa (s) entre clases (para tomar agua).",
    )
    parser.add_argument("--shuffle", action="store_true", help="Baraja el orden de clases por hablante.")
    parser.add_argument("--seed", type=int, default=None, help="Semilla del shuffle.")
    parser.add_argument(
        "--data-root",
        default=str(DEFAULT_DATA_ROOT),
        help=f"Raiz del corpus. Default: {DEFAULT_DATA_ROOT}",
    )
    parser.add_argument("--language", default="es")
    parser.add_argument(
        "--no-calibration",
        action="store_true",
        help="No hacer las 2 tomas de prueba al inicio de cada hablante.",
    )
    args = parser.parse_args()

    speakers: list[tuple[str, str, str]] = args.speakers
    data_root = Path(args.data_root)
    manifest_path = data_root / "manifests" / "corpus.csv"

    classes_base = list(CLASSES_ARDUINO)
    total_reps = args.reps
    n_speakers = len(speakers)
    n_classes = len(classes_base)
    total_clips = n_speakers * n_classes * total_reps
    estimated_seconds = total_clips * (args.countdown + DURATION_S + args.inter_rep_sleep + 0.4)
    estimated_min = estimated_seconds / 60.0

    devices = sd.query_devices()
    print("\nDispositivos de entrada detectados:")
    for i, d in enumerate(devices):
        if d.get("max_input_channels", 0) >= 1:
            marker = "  <- default" if sd.default.device and i == sd.default.device[0] else ""
            print(
                f"  [{i}] {d['name']}  ({d['max_input_channels']} ch, "
                f"default sr={d.get('default_samplerate')}){marker}"
            )

    _print_box(
        [
            "SESION DE GRABACION - PROYECTO-FINAL-IA",
            f"Hablantes:      {n_speakers}  -> {', '.join(s[0] for s in speakers)}",
            f"Clases:         {n_classes} comandos Arduino",
            f"Repeticiones:   {total_reps} por clase por hablante",
            f"Total clips:    {total_clips}",
            f"Tiempo estim.:  ~{estimated_min:.0f} min ({estimated_min / 60:.1f} h)",
            f"Ambiente:       {args.environment}",
            f"Dispositivo:    {args.device}",
        ]
    )
    try:
        input("\nENTER para empezar (Ctrl+C para abortar)... ")
    except (EOFError, KeyboardInterrupt):
        print("Abortado antes de empezar.")
        return

    saved = 0
    rejected = 0
    skipped = 0

    try:
        for spk_idx, speaker in enumerate(speakers, start=1):
            spk_id, gender, age = speaker
            _print_box(
                [
                    f"HABLANTE {spk_idx} / {n_speakers}",
                    f"ID: {spk_id}   genero: {gender}   edad: {age}",
                    "Ajuste el lavalier, vaso de agua listo.",
                    "ENTER para empezar (Ctrl+C aborta).",
                ]
            )
            try:
                input("> ")
            except (EOFError, KeyboardInterrupt):
                print("Sesion abortada.")
                break

            if not args.no_calibration:
                _calibrate(spk_id)
                try:
                    input("\n  ENTER para arrancar la grabacion real de este hablante... ")
                except (EOFError, KeyboardInterrupt):
                    print("Sesion abortada.")
                    break

            # orden de clases por hablante (shuffled si --shuffle)
            classes = list(classes_base)
            if args.shuffle:
                seed = args.seed if args.seed is None else args.seed + spk_idx
                random.Random(seed).shuffle(classes)

            for c_idx, cls in enumerate(classes, start=1):
                print(
                    f"\n--- Clase {c_idx}/{n_classes}: {cls.upper()}  "
                    f"({total_reps} reps) — hablante {spk_id} ---"
                )
                print(f"  Lea la palabra mentalmente. Empieza en 3 s...")
                time.sleep(3.0)

                for rep in range(1, total_reps + 1):
                    audio, reason = auto_record_one(cls, rep, total_reps, args.countdown)
                    if audio is None:
                        # reintento UNICO
                        print(f"      reintento 1/1 ...")
                        time.sleep(0.4)
                        audio, reason = auto_record_one(cls, rep, total_reps, args.countdown)

                    if audio is None:
                        rejected += 1
                        logger.warning(
                            "Rep rechazada %s/%s clase=%s rep=%d reason=%s",
                            spk_id, args.environment, cls, rep, reason,
                        )
                    else:
                        _persist(
                            audio, cls, rep, speaker, args.environment, args.device,
                            args.language, data_root, manifest_path,
                        )
                        saved += 1

                    time.sleep(args.inter_rep_sleep)

                if c_idx < n_classes:
                    print(
                        f"  Clase '{cls}' terminada. Tome agua. "
                        f"Siguiente clase en {args.inter_class_sleep:.0f} s..."
                    )
                    time.sleep(args.inter_class_sleep)

            print(f"\n  HABLANTE {spk_id} TERMINADO.")
            if spk_idx < n_speakers:
                try:
                    input("  ENTER para pasar al siguiente hablante... ")
                except (EOFError, KeyboardInterrupt):
                    print("Sesion abortada por el usuario.")
                    break

    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")

    print()
    _print_box(
        [
            "RESUMEN DE SESION",
            f"Clips guardados: {saved}",
            f"Reps rechazadas: {rejected}",
            f"Reps saltadas:   {skipped}",
            f"Total esperado:  {total_clips}",
            f"Manifest:        {manifest_path}",
            f"Raw dir:         {data_root / 'raw'}",
        ]
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - CLI defensivo
        logger.exception("Fallo en record_session.py: %s", exc)
        sys.exit(1)
