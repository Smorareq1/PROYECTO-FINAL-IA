"""Importador de audios existentes al corpus.

Pensado para cuando no se puede grabar directamente en esta computadora:
toma archivos de cualquier formato/sample-rate, los normaliza al formato
canonico (16 kHz mono WAV PCM16, 2.0 s exactos) y los anexa al manifest.

Dos modos de entrada:

  1) --from-dir DIR --layout class_subdirs
     Espera DIR/<clase>/<archivo>.wav   (las subcarpetas son los nombres de clase)
     Las clases deben coincidir con las de instrucciones.md.

  2) --from-csv FILE
     CSV con columnas requeridas:  filepath, class
     CSV con columnas opcionales:  speaker_id, speaker_gender, speaker_age_range,
                                   environment, device, language
     Cualquier columna ausente toma el valor pasado por flag (--speaker, etc.)
     Las filepath son relativas al directorio del CSV (o absolutas).

Ejemplos:
    # Carpeta organizada por clase (10 hablantes mezclados, mismos parametros para todos)
    python -m scripts.import_audios --from-dir audios_externos/ --layout class_subdirs \\
        --speaker spk07 --gender M --age 26-35 --environment salon_silencioso --device webcam_logitech

    # CSV con metadata por clip
    python -m scripts.import_audios --from-csv listing.csv --device webcam_logitech

    # Ver que pasaria sin escribir nada
    python -m scripts.import_audios --from-dir audios/ --layout class_subdirs \\
        --speaker spk07 --gender M --age 26-35 --environment salon_silencioso --dry-run
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf

try:
    import librosa
except Exception:  # pragma: no cover
    librosa = None  # type: ignore[assignment]

from src.audio.normalization import check_quality
from src.audio.vad import detect_speech
from src.cli.record import (
    ALL_CLASSES,
    MANIFEST_FIELDS,
    SAMPLE_RATE,
    append_manifest_row,
    estimate_snr_db,
    next_clip_id,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

TARGET_DURATION_S = 2.0
TARGET_SAMPLES = int(TARGET_DURATION_S * SAMPLE_RATE)
SUPPORTED_NATIVE = {".wav", ".flac", ".ogg"}
SUPPORTED_VIA_LIBROSA = {".mp3", ".m4a", ".aac", ".opus"}


def load_any(path: Path) -> tuple[np.ndarray, int]:
    """Carga un archivo de audio y lo devuelve como (mono float32, sr)."""
    ext = path.suffix.lower()
    if ext in SUPPORTED_NATIVE:
        audio, sr = sf.read(path, dtype="float32", always_2d=False)
    elif ext in SUPPORTED_VIA_LIBROSA:
        if librosa is None:
            raise RuntimeError(
                f"Formato {ext} requiere librosa+audioread+ffmpeg instalados"
            )
        audio, sr = librosa.load(str(path), sr=None, mono=False)
    else:
        raise ValueError(f"Extension no soportada: {ext}")
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=0 if audio.shape[0] < audio.shape[1] else 1)
    return audio, int(sr)


def resample_to_target(audio: np.ndarray, src_sr: int, target_sr: int = SAMPLE_RATE) -> np.ndarray:
    if src_sr == target_sr:
        return audio.astype(np.float32, copy=False)
    if librosa is None:
        raise RuntimeError(
            f"Necesito librosa para resamplear de {src_sr} a {target_sr}. Instalalo o "
            "convierte previamente con ffmpeg."
        )
    return librosa.resample(audio.astype(np.float32), orig_sr=src_sr, target_sr=target_sr)


def fit_to_target_length(
    audio: np.ndarray,
    target_samples: int = TARGET_SAMPLES,
    pad_strategy: str = "center",
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """Padea con ceros o recorta para llegar exactamente a target_samples.

    pad_strategy:
        center: para audio mas corto, padea simetrico. Para audio mas largo,
                detecta voz con VAD y centra. Si VAD falla, toma el centro.
        left:   audio queda al principio; padea/trimrea por la derecha.
        right:  audio queda al final; padea/trimrea por la izquierda.
    """
    n = len(audio)
    if n == target_samples:
        return audio.astype(np.float32, copy=False)

    if n < target_samples:
        pad_total = target_samples - n
        if pad_strategy == "center":
            pad_left = pad_total // 2
        elif pad_strategy == "left":
            pad_left = 0
        elif pad_strategy == "right":
            pad_left = pad_total
        else:
            pad_left = pad_total // 2
        pad_right = pad_total - pad_left
        return np.concatenate(
            [
                np.zeros(pad_left, dtype=np.float32),
                audio.astype(np.float32),
                np.zeros(pad_right, dtype=np.float32),
            ]
        )

    # n > target_samples → recortar
    if pad_strategy == "center":
        try:
            vad_s, vad_e = detect_speech(audio, sr)
            speech_mid = (vad_s + vad_e) // 2 if vad_e > vad_s else n // 2
        except Exception:
            speech_mid = n // 2
        start = max(0, min(speech_mid - target_samples // 2, n - target_samples))
    elif pad_strategy == "left":
        start = 0
    elif pad_strategy == "right":
        start = n - target_samples
    else:
        start = (n - target_samples) // 2
    return audio[start : start + target_samples].astype(np.float32, copy=False)


def iter_from_dir(root: Path) -> list[tuple[Path, str]]:
    """Devuelve [(filepath, class_name), ...] explorando DIR/<clase>/<archivo>.*."""
    items: list[tuple[Path, str]] = []
    for cls_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        cls = cls_dir.name
        if cls not in ALL_CLASSES:
            logger.warning(
                "Carpeta '%s' no es una clase conocida; saltando. Clases validas: %s",
                cls,
                ALL_CLASSES,
            )
            continue
        for f in sorted(cls_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in SUPPORTED_NATIVE | SUPPORTED_VIA_LIBROSA:
                items.append((f, cls))
    return items


def iter_from_csv(csv_path: Path) -> list[tuple[Path, str, dict[str, str]]]:
    rows: list[tuple[Path, str, dict[str, str]]] = []
    base = csv_path.parent
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            fp = r.get("filepath", "").strip()
            cls = r.get("class", "").strip()
            if not fp or not cls:
                continue
            p = (base / fp).resolve() if not Path(fp).is_absolute() else Path(fp)
            rows.append((p, cls, dict(r)))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-dir", type=Path, help="Directorio con subcarpetas por clase")
    src.add_argument("--from-csv", type=Path, help="CSV listando filepath,class[,metadata]")

    parser.add_argument(
        "--layout",
        choices=["class_subdirs"],
        default="class_subdirs",
        help="Solo aplica con --from-dir.",
    )

    # Metadata por defecto cuando no viene en el CSV
    parser.add_argument("--speaker", default="")
    parser.add_argument("--gender", choices=["M", "F", "X", ""], default="")
    parser.add_argument(
        "--age",
        choices=["18-25", "26-35", "36-50", "50+", ""],
        default="",
    )
    parser.add_argument(
        "--environment",
        choices=["salon_silencioso", "laboratorio", "pasillo_ruidoso", ""],
        default="",
    )
    parser.add_argument("--device", default="imported")
    parser.add_argument("--language", default="es")

    parser.add_argument("--data-root", default="backend/data")
    parser.add_argument(
        "--pad-strategy",
        choices=["center", "left", "right"],
        default="center",
        help="Como ajustar a 2.0 s cuando la duracion difiere",
    )
    parser.add_argument(
        "--peak-max", type=float, default=0.95, help="Rechaza si pico > este valor (clipping)"
    )
    parser.add_argument(
        "--rms-min", type=float, default=0.005, help="Rechaza si RMS < este valor"
    )
    parser.add_argument(
        "--normalize", action="store_true", help="Normaliza amplitud a pico 0.9 antes de guardar"
    )
    parser.add_argument(
        "--skip-bad", action="store_true",
        help="Saltar archivos que no pasan check_quality (default: warning solo)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="No escribe nada; solo reporta"
    )

    args = parser.parse_args()

    data_root = Path(args.data_root)
    manifest_path = data_root / "manifests" / "corpus.csv"

    # 1) Recolectar items a procesar
    if args.from_dir is not None:
        items = [(p, c, {}) for (p, c) in iter_from_dir(args.from_dir)]
        if not items:
            logger.error("Sin archivos validos bajo %s", args.from_dir)
            sys.exit(1)
    else:
        items = iter_from_csv(args.from_csv)
        if not items:
            logger.error("Sin filas validas en %s", args.from_csv)
            sys.exit(1)

    logger.info("Archivos detectados: %d", len(items))

    # 2) Procesar
    counter_offset = next_clip_id(manifest_path) - 1
    saved = 0
    skipped = 0
    failed: list[tuple[Path, str]] = []

    for idx, (src_path, cls, row_extra) in enumerate(items, start=1):
        if cls not in ALL_CLASSES:
            logger.warning("[%d/%d] Clase desconocida '%s' en %s; saltando", idx, len(items), cls, src_path)
            failed.append((src_path, f"clase desconocida: {cls}"))
            continue
        if not src_path.exists():
            logger.warning("[%d/%d] Falta archivo: %s", idx, len(items), src_path)
            failed.append((src_path, "archivo no existe"))
            continue

        try:
            audio, src_sr = load_any(src_path)
        except Exception as exc:
            logger.warning("[%d/%d] No se pudo leer %s: %s", idx, len(items), src_path, exc)
            failed.append((src_path, f"load error: {exc}"))
            continue

        try:
            audio = resample_to_target(audio, src_sr, SAMPLE_RATE)
        except Exception as exc:
            logger.warning("[%d/%d] Resample fallo en %s: %s", idx, len(items), src_path, exc)
            failed.append((src_path, f"resample error: {exc}"))
            continue

        audio = fit_to_target_length(audio, TARGET_SAMPLES, args.pad_strategy, SAMPLE_RATE)

        if args.normalize:
            peak = float(np.max(np.abs(audio)))
            if peak > 1e-9:
                audio = (audio * (0.9 / peak)).astype(np.float32)

        is_noise = cls == "ruido_fondo"
        if not is_noise:
            ok, msg = check_quality(audio, peak_max=args.peak_max, rms_min=args.rms_min)
            if not ok:
                if args.skip_bad:
                    logger.warning("[%d/%d] %s rechazado: %s", idx, len(items), src_path.name, msg)
                    skipped += 1
                    continue
                logger.warning("[%d/%d] %s con warning de calidad: %s (se importa igual)", idx, len(items), src_path.name, msg)

        # SNR
        try:
            vs, ve = (0, len(audio)) if is_noise else detect_speech(audio, SAMPLE_RATE)
            snr = estimate_snr_db(audio, vs, ve)
        except Exception:
            snr = 0.0

        # Metadata (CSV row override > flags > vacio)
        def pick(key: str, default: str) -> str:
            v = row_extra.get(key, "")
            return v if v else default

        clip_id = counter_offset + saved + 1
        out_name = f"{(pick('speaker_id', args.speaker) or 'imp')}_{int(time.time()*1000) % 100000:05d}_{clip_id:06d}.wav"
        clip_dir = data_root / "raw" / cls
        out_path = clip_dir / out_name

        if not args.dry_run:
            clip_dir.mkdir(parents=True, exist_ok=True)
            sf.write(out_path, audio, SAMPLE_RATE, subtype="PCM_16")

        manifest_row = {
            "clip_id": clip_id,
            "filepath": str(out_path.relative_to(data_root)).replace("\\", "/"),
            "class": cls,
            "speaker_id": pick("speaker_id", args.speaker) if not is_noise else "",
            "speaker_gender": pick("speaker_gender", args.gender) if not is_noise else "",
            "speaker_age_range": pick("speaker_age_range", args.age) if not is_noise else "",
            "environment": pick("environment", args.environment),
            "device": pick("device", args.device),
            "language": pick("language", args.language),
            "duration_s": round(len(audio) / SAMPLE_RATE, 3),
            "peak": round(float(np.max(np.abs(audio))), 4),
            "rms": round(float(np.sqrt(np.mean(audio.astype(np.float64) ** 2))), 4),
            "snr_db_est": round(snr, 2),
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "split": "",
        }
        if not args.dry_run:
            append_manifest_row(manifest_path, manifest_row)
        saved += 1

        if idx % 50 == 0 or idx == len(items):
            logger.info(
                "[%d/%d] saved=%d skipped=%d failed=%d", idx, len(items), saved, skipped, len(failed),
            )

    print()
    print(f"=== Importacion {'(DRY-RUN) ' if args.dry_run else ''}terminada ===")
    print(f"  Importados:  {saved}")
    print(f"  Saltados:    {skipped} (calidad fuera de rango con --skip-bad)")
    print(f"  Fallidos:    {len(failed)}")
    if failed[:5]:
        print("  Primeros fallos:")
        for p, reason in failed[:5]:
            print(f"    - {p}: {reason}")
    print(f"  Manifest:    {manifest_path}")


if __name__ == "__main__":
    main()
