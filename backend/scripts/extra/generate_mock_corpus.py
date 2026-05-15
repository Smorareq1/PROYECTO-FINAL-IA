"""
scripts/generate_mock_corpus.py

Genera un corpus sintético de audio con la misma estructura que el corpus real,
para que SW2 pueda avanzar el pipeline de inferencia sin esperar las grabaciones.

Cada "comando" se simula con:
  - Una serie de tonos con frecuencias diferenciables por clase (formantes simulados)
  - Modulación de amplitud (envolvente que imita el habla)
  - Ruido de fondo controlado
  - Variabilidad por hablante (pitch shifting)

Uso:
    python scripts/generate_mock_corpus.py --output data/raw_mock --speakers 10 --per-class 30

Esto produce ~1800 muestras (10 clases × 10 hablantes × 18 muestras) en pocos segundos.

IMPORTANTE: estas muestras NO son habla real. Sirven exclusivamente para validar
que el pipeline (carga, MFCC, modelo, predicción, serial) corre sin errores y
que las latencias son las esperadas. Las métricas con este corpus serán artificialmente
altas (>99%) porque cada clase tiene una firma espectral muy distinta.
"""

from __future__ import annotations

import argparse
import logging
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

# ───────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ───────────────────────────────────────────────────────────────────

SAMPLE_RATE = 16_000  # Misma tasa que el corpus real
DURATION_SEC = 1.5    # Duración media de una muestra

# Cada clase tiene una "firma" de frecuencias (formantes simulados).
# Esto imita que cada palabra tiene resonancias vocálicas distintas.
# Los valores son tripletas (F1, F2, F3) en Hz que se asemejan a vocales reales.
CLASS_FORMANTS: dict[str, tuple[int, int, int]] = {
    # Comandos simples (modelo CNN base) — vocablos cortos
    "enciende":         (450, 1800, 2500),   # /e/ + /i/ dominante
    "apaga":            (700, 1200, 2400),   # /a/ dominante
    "detente":          (500, 1900, 2600),   # /e/ + /e/
    "rojo":             (600, 1100, 2300),   # /o/ + /o/
    "verde":            (500, 1700, 2400),   # /e/ + /e/ con /r/
    "azul":             (350, 900, 2200),    # /a/ + /u/ (cierre)
    "ruido_fondo":      (0, 0, 0),           # sin formantes, solo ruido

    # Comandos compuestos (modelo BiLSTM) — duración doble / multipaso
    "blanco":           (400, 1500, 2400),   # /a/ + /o/ con nasal
    "procesando":       (520, 1600, 2500),   # /o/ + /e/ + /a/ + /o/
    "alarma":           (700, 1300, 2300),   # /a/ + /a/ + /a/ dominante
    "tono":             (500, 1100, 2400),   # /o/ + /o/ con /t/ ataque
}

COMPOUND_CLASSES = {
    "blanco", "procesando", "alarma", "tono"
}


@dataclass
class GeneratorConfig:
    output_dir: Path
    n_speakers: int = 10
    samples_per_class_per_speaker: int = 18
    seed: int = 42


# ───────────────────────────────────────────────────────────────────
# GENERACIÓN DE SEÑALES
# ───────────────────────────────────────────────────────────────────

def generate_envelope(duration_sec: float, sr: int, rng: np.random.Generator) -> np.ndarray:
    """
    Envolvente de amplitud que simula el ataque, sostenido y caída del habla.
    Forma: subida rápida (~50ms), sostenido con leve modulación, caída suave.
    """
    n_samples = int(duration_sec * sr)
    t = np.linspace(0, duration_sec, n_samples)

    attack_sec = rng.uniform(0.04, 0.08)
    release_sec = rng.uniform(0.10, 0.20)

    envelope = np.ones(n_samples)
    attack_samples = int(attack_sec * sr)
    release_samples = int(release_sec * sr)

    # Ataque (sigmoide)
    envelope[:attack_samples] = 1 / (1 + np.exp(-10 * np.linspace(-3, 3, attack_samples)))

    # Caída (exponencial)
    envelope[-release_samples:] = np.exp(-3 * np.linspace(0, 1, release_samples))

    # Modulación de amplitud durante el sostenido (~5 Hz, simula prosodia)
    am = 1 + 0.15 * np.sin(2 * np.pi * 5 * t + rng.uniform(0, 2 * np.pi))
    envelope *= am

    return envelope


def generate_speech_like_signal(
    formants: tuple[int, int, int],
    duration_sec: float,
    sr: int,
    speaker_pitch_shift: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Genera una señal con tres formantes y una frecuencia fundamental (pitch).
    No es habla real, pero tiene una firma espectral consistente por clase.
    """
    n_samples = int(duration_sec * sr)
    t = np.linspace(0, duration_sec, n_samples)

    # Frecuencia fundamental con leve vibrato; ajustada por hablante
    f0_base = 150.0 * (2 ** (speaker_pitch_shift / 12))  # semitonos
    vibrato = 5 * np.sin(2 * np.pi * 6 * t)
    f0 = f0_base + vibrato

    # Suma armónica (simula la fuente glótica)
    signal = np.zeros(n_samples)
    for harmonic in range(1, 8):
        amp = 1.0 / harmonic
        signal += amp * np.sin(2 * np.pi * harmonic * f0 * t)

    # Aplicar formantes como filtros resonantes simples (suma de senoides moduladas)
    for formant_freq in formants:
        if formant_freq == 0:
            continue
        # Bandwidth aleatorio simula el ancho de banda del formante
        bandwidth = rng.uniform(80, 150)
        formant_signal = np.sin(2 * np.pi * formant_freq * t)
        # Modular con la fundamental para que suene "vocálico"
        formant_signal *= np.exp(-bandwidth * 1e-4 * np.abs(np.sin(2 * np.pi * f0 * t)))
        signal += 0.4 * formant_signal

    # Aplicar envolvente
    envelope = generate_envelope(duration_sec, sr, rng)
    signal *= envelope

    # Normalizar a [-0.7, 0.7] para evitar clipping
    signal = signal / (np.max(np.abs(signal)) + 1e-9) * 0.7

    return signal


def generate_background_noise(duration_sec: float, sr: int, rng: np.random.Generator) -> np.ndarray:
    """
    Genera ruido representativo de la clase RUIDO_FONDO.
    Mezcla de ruido rosa, ráfagas de ruido blanco y silencios.
    """
    n_samples = int(duration_sec * sr)

    # Tipo de ruido elegido aleatoriamente
    noise_type = rng.choice(["pink", "white", "silent_with_clicks", "low_hum"])

    if noise_type == "white":
        signal = rng.normal(0, 0.05, n_samples)
    elif noise_type == "pink":
        white = rng.normal(0, 1, n_samples)
        # Aproximación de ruido rosa con filtrado
        signal = np.cumsum(white) / np.sqrt(np.arange(1, n_samples + 1))
        signal = signal / (np.max(np.abs(signal)) + 1e-9) * 0.05
    elif noise_type == "silent_with_clicks":
        signal = rng.normal(0, 0.005, n_samples)
        # Insertar 1-3 clicks aleatorios
        for _ in range(rng.integers(1, 4)):
            click_pos = rng.integers(0, n_samples - 100)
            signal[click_pos:click_pos + 50] += rng.uniform(-0.2, 0.2)
    else:  # low_hum
        t = np.linspace(0, duration_sec, n_samples)
        signal = 0.03 * np.sin(2 * np.pi * 60 * t) + rng.normal(0, 0.01, n_samples)

    return signal.astype(np.float32)


def add_recording_noise(signal: np.ndarray, snr_db: float, rng: np.random.Generator) -> np.ndarray:
    """Agrega ruido gaussiano con relación señal-ruido controlada."""
    signal_power = np.mean(signal ** 2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = rng.normal(0, np.sqrt(noise_power), len(signal))
    return signal + noise


# ───────────────────────────────────────────────────────────────────
# ORQUESTACIÓN
# ───────────────────────────────────────────────────────────────────

def generate_sample(
    class_name: str,
    speaker_id: int,
    sample_id: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Genera una sola muestra para una (clase, hablante, repetición)."""
    # Variabilidad por hablante: pitch shift estable entre -3 y +5 semitonos
    speaker_rng = np.random.default_rng(seed=speaker_id * 1000)
    pitch_shift = speaker_rng.uniform(-3, 5)

    # Duración: compuestos son más largos
    if class_name in COMPOUND_CLASSES:
        duration = rng.uniform(1.6, 2.0)
    elif class_name == "ruido_fondo":
        duration = rng.uniform(1.0, 2.0)
    else:
        duration = rng.uniform(1.0, 1.4)

    # Generar la señal base
    if class_name == "ruido_fondo":
        signal = generate_background_noise(duration, SAMPLE_RATE, rng)
    else:
        formants = CLASS_FORMANTS[class_name]
        signal = generate_speech_like_signal(
            formants=formants,
            duration_sec=duration,
            sr=SAMPLE_RATE,
            speaker_pitch_shift=pitch_shift,
            rng=rng,
        )

        # Añadir ruido de grabación (SNR entre 20 y 35 dB)
        snr = rng.uniform(20, 35)
        signal = add_recording_noise(signal, snr, rng)

    # Padding o recorte para llegar a una duración consistente
    target_samples = int(DURATION_SEC * SAMPLE_RATE)
    if len(signal) < target_samples:
        # Pad con silencio (o ruido bajo) y posición aleatoria
        pad_total = target_samples - len(signal)
        pad_left = rng.integers(0, pad_total + 1)
        pad_right = pad_total - pad_left
        silence_left = rng.normal(0, 0.005, pad_left)
        silence_right = rng.normal(0, 0.005, pad_right)
        signal = np.concatenate([silence_left, signal, silence_right])
    else:
        signal = signal[:target_samples]

    return signal.astype(np.float32)


def generate_corpus(cfg: GeneratorConfig) -> dict[str, int]:
    """Genera el corpus completo y devuelve el conteo por clase."""
    rng_master = np.random.default_rng(cfg.seed)
    counts: dict[str, int] = {}

    # Crear estructura de carpetas
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    for class_name in CLASS_FORMANTS.keys():
        class_dir = cfg.output_dir / class_name
        class_dir.mkdir(exist_ok=True)
        counts[class_name] = 0

        # RUIDO_FONDO tiene menos muestras (~250)
        if class_name == "ruido_fondo":
            samples_per_speaker = max(1, cfg.samples_per_class_per_speaker // 2)
        else:
            samples_per_speaker = cfg.samples_per_class_per_speaker

        for speaker_id in range(1, cfg.n_speakers + 1):
            for sample_id in range(1, samples_per_speaker + 1):
                # Cada muestra usa su propio RNG derivado
                sample_seed = rng_master.integers(0, 2**31 - 1)
                rng_sample = np.random.default_rng(sample_seed)

                signal = generate_sample(class_name, speaker_id, sample_id, rng_sample)

                filename = f"speaker{speaker_id:02d}_{sample_id:03d}.wav"
                filepath = class_dir / filename

                sf.write(filepath, signal, SAMPLE_RATE, subtype="PCM_16")
                counts[class_name] += 1

    return counts


def write_speakers_csv(cfg: GeneratorConfig) -> None:
    """Escribe metadata de hablantes simulados."""
    csv_path = cfg.output_dir.parent / "speakers_mock.csv"
    rng = np.random.default_rng(cfg.seed)

    with csv_path.open("w", encoding="utf-8") as f:
        f.write("speaker_id,gender,environment\n")
        for sid in range(1, cfg.n_speakers + 1):
            gender = rng.choice(["M", "F"])
            env = rng.choice(["silencioso", "ruido_moderado"])
            f.write(f"speaker{sid:02d},{gender},{env}\n")


# ───────────────────────────────────────────────────────────────────
# CLI
# ───────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera corpus sintético para desarrollo del pipeline de inferencia."
    )
    parser.add_argument("--output", type=Path, default=Path("data/raw_mock"),
                        help="Directorio de salida (default: data/raw_mock)")
    parser.add_argument("--speakers", type=int, default=10,
                        help="Número de hablantes simulados (default: 10)")
    parser.add_argument("--per-class", type=int, default=18,
                        help="Muestras por clase por hablante (default: 18 → ~180 por clase)")
    parser.add_argument("--seed", type=int, default=42, help="Semilla del RNG")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger(__name__)

    cfg = GeneratorConfig(
        output_dir=args.output,
        n_speakers=args.speakers,
        samples_per_class_per_speaker=args.per_class,
        seed=args.seed,
    )

    logger.info("Generando corpus sintético en %s", cfg.output_dir)
    logger.info("Hablantes: %d · Muestras por clase por hablante: %d",
                cfg.n_speakers, cfg.samples_per_class_per_speaker)

    counts = generate_corpus(cfg)
    write_speakers_csv(cfg)

    logger.info("\n=== Corpus generado ===")
    total = 0
    for cls, n in counts.items():
        logger.info("  %-22s %d muestras", cls, n)
        total += n
    logger.info("  TOTAL: %d muestras", total)
    logger.info("\nPath: %s", cfg.output_dir.resolve())
    logger.info("\nADVERTENCIA: este corpus es sintético. Usar SOLO para desarrollo.")
    logger.info("Reemplazar por data/raw/ (corpus real) para entrenamiento final.")


if __name__ == "__main__":
    main()
