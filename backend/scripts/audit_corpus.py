"""Auditoria del corpus de voz.

Verifica:
  1. Conteo por clase, hablante y entorno.
  2. Archivos del filesystem no listados en el manifest (huerfanos).
  3. Filas del manifest cuyo filepath no existe en disco.
  4. Clases por debajo del minimo de muestras (`--min-per-class`).
  5. Distribucion de SNR estimado y duracion.

Uso:
    python -m scripts.audit_corpus
    python -m scripts.audit_corpus --min-per-class 120
"""
from __future__ import annotations

import argparse
import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

# data root canonico, relativo al archivo del script (backend/data/), no al cwd
BACKEND_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_ROOT = BACKEND_ROOT / "data"


def read_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def find_disk_files(raw_dir: Path) -> list[Path]:
    return sorted(raw_dir.rglob("*.wav"))


def summarize(rows: list[dict], key: str) -> dict[str, int]:
    return dict(Counter(r.get(key, "") for r in rows))


def fmt_table(title: str, mapping: dict[str, int]) -> str:
    if not mapping:
        return f"{title}: (vacio)\n"
    width = max(len(k) for k in mapping)
    lines = [f"{title}:"]
    for k, v in sorted(mapping.items()):
        lines.append(f"  {k.ljust(width)}  {v}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--min-per-class", type=int, default=120)
    parser.add_argument("--min-snr-db", type=float, default=12.0)
    args = parser.parse_args()

    data_root = Path(args.data_root)
    raw_dir = data_root / "raw"
    manifest_path = Path(args.manifest) if args.manifest else data_root / "manifests" / "corpus.csv"

    rows = read_manifest(manifest_path)
    disk_files = find_disk_files(raw_dir)

    print(f"\n=== Auditoria del corpus ===")
    print(f"Manifest: {manifest_path}")
    print(f"Raw dir:  {raw_dir}")
    print(f"Filas en manifest: {len(rows)}")
    print(f"Archivos .wav en disco: {len(disk_files)}\n")

    if not rows and not disk_files:
        print("Corpus vacio (todavia no se grabo nada).")
        return

    # Conteos
    print(fmt_table("Conteo por clase", summarize(rows, "class")))
    print(fmt_table("Conteo por hablante", summarize(rows, "speaker_id")))
    print(fmt_table("Conteo por entorno", summarize(rows, "environment")))
    print(fmt_table("Conteo por genero", summarize(rows, "speaker_gender")))

    # Distribucion por (hablante, clase) — para detectar gaps
    by_spk_cls: dict[tuple[str, str], int] = defaultdict(int)
    for r in rows:
        if r.get("class") == "ruido_fondo":
            continue
        by_spk_cls[(r.get("speaker_id", ""), r.get("class", ""))] += 1

    speakers = sorted({k[0] for k in by_spk_cls})
    classes = sorted({k[1] for k in by_spk_cls})
    if speakers and classes:
        print("Matriz (hablante x clase):")
        header = "  " + "speaker".ljust(10) + "".join(c[:10].rjust(11) for c in classes)
        print(header)
        for spk in speakers:
            line = "  " + spk.ljust(10) + "".join(str(by_spk_cls.get((spk, c), 0)).rjust(11) for c in classes)
            print(line)
        print()

    # Huerfanos y faltantes
    manifest_paths = {data_root / r.get("filepath", "") for r in rows if r.get("filepath")}
    disk_set = set(disk_files)
    orphans = sorted(disk_set - manifest_paths)
    missing = sorted(manifest_paths - disk_set)
    if orphans:
        print(f"WARNING: {len(orphans)} archivos en disco NO listados en el manifest:")
        for p in orphans[:10]:
            print(f"  - {p.relative_to(data_root)}")
        if len(orphans) > 10:
            print(f"  (y {len(orphans) - 10} mas)")
        print()
    if missing:
        print(f"WARNING: {len(missing)} filas en el manifest sin archivo correspondiente:")
        for p in missing[:10]:
            print(f"  - {p.relative_to(data_root)}")
        if len(missing) > 10:
            print(f"  (y {len(missing) - 10} mas)")
        print()

    # Clases bajo minimo
    class_counts = summarize(rows, "class")
    under = {c: n for c, n in class_counts.items() if n < args.min_per_class}
    if under:
        print(f"WARNING: clases por debajo de min_per_class={args.min_per_class}:")
        for c, n in sorted(under.items()):
            print(f"  - {c}: {n}")
        print()

    # SNR / duraciones
    snrs = []
    durs = []
    low_snr = 0
    for r in rows:
        try:
            snr = float(r.get("snr_db_est", 0) or 0)
            snrs.append(snr)
            if snr < args.min_snr_db and r.get("class") != "ruido_fondo":
                low_snr += 1
        except ValueError:
            pass
        try:
            durs.append(float(r.get("duration_s", 0) or 0))
        except ValueError:
            pass
    if snrs:
        print(f"SNR (dB): n={len(snrs)} median={statistics.median(snrs):.1f} "
              f"p10={statistics.quantiles(snrs, n=10)[0]:.1f} max={max(snrs):.1f}")
        if low_snr:
            print(f"  (clips no-ruido con SNR<{args.min_snr_db}: {low_snr})")
    if durs:
        print(f"Duracion (s): n={len(durs)} median={statistics.median(durs):.2f} "
              f"min={min(durs):.2f} max={max(durs):.2f}")

    print("\n=== Fin auditoria ===\n")


if __name__ == "__main__":
    main()
