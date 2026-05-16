"""Genera splits estratificados por hablante.

Reglas:
- TEST: `--test-speakers` hablantes completos held-out (no aparecen en train ni val).
- VAL: `--val-frac` de muestras de los hablantes restantes, estratificado por clase.
- TRAIN: el resto.
- ruido_fondo no tiene speaker_id; se reparte aleatoriamente 70/15/15 por archivo.

Salida:
- Reescribe la columna `split` del manifest.
- Escribe backend/data/splits/{train,val,test}.csv con las mismas columnas.

Uso:
    python -m scripts.generate_splits --test-speakers 2 --val-frac 0.15 --seed 42
"""
from __future__ import annotations

import argparse
import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


def read_manifest(path: Path) -> tuple[list[str], list[dict]]:
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    return fieldnames, rows


def write_manifest(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", default="backend/data/manifests/corpus.csv")
    parser.add_argument("--splits-dir", default="backend/data/splits")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-speakers", type=int, default=2)
    parser.add_argument("--val-frac", type=float, default=0.15)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    splits_dir = Path(args.splits_dir)
    splits_dir.mkdir(parents=True, exist_ok=True)

    fieldnames, rows = read_manifest(manifest_path)
    if "split" not in fieldnames:
        fieldnames = list(fieldnames) + ["split"]
    if not rows:
        logger.warning("Manifest vacio en %s, no hay nada que dividir", manifest_path)
        return

    rng = random.Random(args.seed)

    # 1) Elegir hablantes held-out (excluyendo ruido_fondo).
    voice_rows = [r for r in rows if r.get("class") != "ruido_fondo"]
    speakers = sorted({r.get("speaker_id", "") for r in voice_rows if r.get("speaker_id")})
    if len(speakers) <= args.test_speakers:
        logger.warning(
            "Solo %d hablantes; necesitan >%d para held-out. Asignando un solo speaker.",
            len(speakers), args.test_speakers,
        )
        held_out_speakers = set(speakers[: max(0, len(speakers) - 1)])
    else:
        shuffled = speakers[:]
        rng.shuffle(shuffled)
        held_out_speakers = set(shuffled[: args.test_speakers])
    logger.info("Hablantes held-out (test): %s", sorted(held_out_speakers))

    # 2) Asignar split.
    by_speaker_class: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in voice_rows:
        spk = r.get("speaker_id", "")
        cls = r.get("class", "")
        if spk in held_out_speakers:
            r["split"] = "test"
        else:
            by_speaker_class[(spk, cls)].append(r)
            r["split"] = ""

    for (spk, cls), group in by_speaker_class.items():
        rng.shuffle(group)
        n_val = max(1, int(round(len(group) * args.val_frac)))
        for i, r in enumerate(group):
            r["split"] = "val" if i < n_val else "train"

    # 3) ruido_fondo: split aleatorio 70/15/15.
    noise_rows = [r for r in rows if r.get("class") == "ruido_fondo"]
    for r in noise_rows:
        r["split"] = rng.choices(["train", "val", "test"], weights=[0.70, 0.15, 0.15], k=1)[0]

    # 4) Reescribir manifest.
    write_manifest(manifest_path, fieldnames, rows)

    # 5) CSVs por split.
    for sp in ("train", "val", "test"):
        out = splits_dir / f"{sp}.csv"
        sp_rows = [r for r in rows if r.get("split") == sp]
        write_manifest(out, fieldnames, sp_rows)
        counts = Counter(r.get("class", "") for r in sp_rows)
        logger.info("%s: %d clips | clases: %s", sp, len(sp_rows), dict(counts))


if __name__ == "__main__":
    main()
