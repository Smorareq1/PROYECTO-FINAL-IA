# Guía de Grabación del Corpus de Voz

> **Equipamiento**: DJI Mic Mini v1 (lavalier inalámbrico) · computadora macOS · repo clonado
> **Voluntarios**: 5 personas · objetivo ≥2 voces de cada género
> **Duración**: 2 días (~3 h día 1, ~2 h día 2)
> **Corpus objetivo**: 1775 clips totales (1575 con voz + 200 ruido), 18 % sobre el mínimo de 1500 exigido por la rúbrica

---

## 0. Tabla de contenidos

1. [Antes de empezar](#1-antes-de-empezar)
2. [Material necesario](#2-material-necesario)
3. [Setup inicial (una sola vez)](#3-setup-inicial-una-sola-vez)
4. [Cómo se dice cada palabra](#4-cómo-se-dice-cada-palabra)
5. [Posición del lavalier y ganancia](#5-posición-del-lavalier-y-ganancia)
6. [Cronograma de 2 días](#6-cronograma-de-2-días)
7. [Comandos exactos por sesión](#7-comandos-exactos-por-sesión)
8. [Sesiones de `ruido_fondo`](#8-sesiones-de-ruido_fondo)
9. [Post-sesión: auditoría y backup](#9-post-sesión-auditoría-y-backup)
10. [Troubleshooting](#10-troubleshooting)
11. [Checklist final del corpus](#11-checklist-final-del-corpus)

---

## 1. Antes de empezar

### Composición del grupo de voluntarios

`docs/instrucciones.md` exige "**al menos cinco voluntarios externos** además de los integrantes del grupo" para garantizar variabilidad de timbre y género. La rúbrica evalúa esto en el criterio 2 (Recolección y Procesamiento del Corpus, 12 puntos).

- **Si los 5 voluntarios son externos al grupo software**: se cumple el mínimo. Si pueden, sumen también 1–2 sesiones cortas con integrantes del grupo para enriquecer el corpus.
- **Si entre los 5 hay integrantes del grupo**: agendar 1–2 sesiones extra con voluntarios externos puros antes de la entrega (lunes 18 de mayo). Si no es viable, declararlo explícitamente en el documento PDF entregable para anticipar la pregunta en la defensa.

### Balance de género

Objetivo: **al menos 2 voces masculinas y 2 femeninas** entre los 5 hablantes. Las arquitecturas CNN/BiLSTM con MFCC son sensibles al pitch fundamental; sin balance, el modelo aprende a discriminar género en lugar de comando.

### Idioma y comandos

10 clases, todas en español:
- 5 simples obligatorias: `enciende`, `apaga`, `izquierda`, `derecha`, `detente`
- 4 compuestas: `enciende_rapido`, `enciende_lento`, `gira_izquierda`, `gira_derecha`
- 1 especial: `ruido_fondo` (sin voz de comando)

---

## 2. Material necesario

| Item | Detalle |
|---|---|
| Micrófono | **DJI Mic Mini v1** — transmisor lavalier + receptor USB-C |
| Adaptador | Cable USB-C ↔ USB-C (incluido) si la Mac tiene USB-C, o USB-C ↔ USB-A si es Mac vieja |
| Computadora | macOS (Sonoma o Sequoia ideal; Big Sur o más nuevo funciona) |
| Sala 1 | "Salón silencioso": cuarto cerrado, sin ventiladores, sin tráfico cercano |
| Sala 2 | "Laboratorio": espacio con ruido ambiente moderado (HVAC, ventiladores de equipo, conversación lejana) |
| Pasillo | Para una de las sesiones de `ruido_fondo` |
| Auriculares | Para el operador, verificar nivel sin que el sonido del altavoz contamine el mic |
| Vaso de agua | Para los voluntarios (la garganta seca cambia la voz) |
| Cinta o sticker | Para marcar la posición de la pinza y la perilla de ganancia |
| Cargador del DJI | El transmisor + receptor duran ~3 h cada uno; tener el cargador a mano |

---

## 3. Setup inicial (una sola vez)

### 3.1 Clonar el repo e instalar dependencias mínimas

No hace falta instalar PyTorch/torchaudio en la compu de grabación. Sólo lo necesario para `record.py`:

```bash
git clone <url_del_repo>
cd PROYECTO-FINAL-IA/backend

python3 -m venv .venv
source .venv/bin/activate

pip install sounddevice==0.4.6 soundfile==0.12.1 numpy==1.26.4 pyyaml==6.0.1
```

### 3.2 Permisos del micrófono en macOS

1. **System Settings → Privacy & Security → Microphone** → activar el toggle para la app de Terminal que vayan a usar (Terminal.app, iTerm2, Warp, etc.).
2. Si lanzan `record.py` antes de dar el permiso, macOS muestra el diálogo automáticamente; aceptar y volver a lanzar el comando.

### 3.3 Configurar el receptor DJI como entrada de audio

1. Conectar el receptor por USB-C a la Mac. El LED del receptor se ilumina.
2. **System Settings → Sound → Input** → seleccionar el dispositivo que aparece como `DJI MIC MINI RX` (o similar). Si aparece más de uno, elegir el que NO diga "(Bluetooth)".
3. **Input volume al 75 %**, no al 100 %. Esto deja headroom; la ganancia real se ajusta en la perilla del receptor (sección 5).
4. Probar el medidor de nivel: hablar normal y verificar que las barras suban a 2/3 de la escala. Si saturan, bajar el volumen de macOS y la ganancia del receptor.

### 3.4 Apagar procesamiento de voz que pueda interferir

| Setting | Dónde | Estado correcto |
|---|---|---|
| **Microphone Mode** (Voice Isolation / Wide Spectrum) | Control Center → mic icon (sólo visible cuando una app usa el mic) | **Standard** |
| **Noise cancellation del DJI** | Botón de power del transmisor (un click) | **OFF** — verificar que el LED del transmisor no muestre el indicador de NC |
| **Echo Cancellation** del sistema | Auto, no hace falta tocar | (no aplica al input por USB) |
| **Apps que toman el mic exclusivo** | Quit Zoom, Teams, FaceTime, Discord, Skype, OBS, etc. | Cerradas durante la sesión |

**Por qué NC OFF**: no queremos que el mic aplique DSP en la fuente. La robustez al ruido la aprende el modelo con augmentación de datos. Si grabamos con NC y la demo se hace sin NC (o viceversa), el modelo falla.

### 3.5 Parear y verificar el DJI

El DJI Mic Mini viene pre-pareado. Si no, mantener presionado el botón del transmisor hasta que parpadee, ídem el receptor, y se sincronizan solos.

Verificación rápida:
```bash
python -c "import sounddevice as sd; [print(i, d['name']) for i, d in enumerate(sd.query_devices()) if d['max_input_channels'] > 0]"
```
Debe aparecer una línea tipo `2 DJI MIC MINI RX`. Anotar el índice (acá `2`) por si después hay que forzarlo con `--mic 2`.

### 3.6 Prueba de 5 clips (smoke test)

Antes de la primera sesión real, hacer una grabación de prueba con un integrante del grupo:

```bash
cd backend
source .venv/bin/activate

python -m src.cli.record \
    --speaker spk_test --gender M --age 26-35 \
    --environment salon_silencioso --device dji_mic_mini_v1 \
    --classes enciende --repeats 5
```

Después de cada toma `record.py` imprime `peak` y `rms`. Validar:
- `peak` entre 0.40 y 0.85
- `rms` entre 0.05 y 0.20
- Ningún `RECHAZADO` consecutivo

Si los valores quedan fuera de rango, ver sección 10 (Troubleshooting) y ajustar la perilla de ganancia del receptor antes de la sesión real.

Borrar los clips de prueba al terminar (NO entran al corpus):
```bash
rm -rf backend/data/raw/enciende/spk_test_*
# y eliminar las filas de spk_test del manifest manualmente, o:
python -c "
import csv
rows = [r for r in csv.DictReader(open('backend/data/manifests/corpus.csv')) if r['speaker_id'] != 'spk_test']
with open('backend/data/manifests/corpus.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
    w.writeheader(); w.writerows(rows)
"
```

---

## 4. Cómo se dice cada palabra

### 4.1 Una palabra por archivo (decisión metodológica)

Cada archivo WAV contiene **una sola pronunciación del comando**, no varias. El operador presiona ENTER, el voluntario dice la palabra, se guarda; el operador presiona ENTER otra vez, el voluntario la repite, se guarda otro archivo.

**Por qué NO grabar "muchas veces seguidas en un mismo audio"**:

1. **La distribución de entrenamiento debe igualar la de inferencia**. En la demo en vivo, el pipeline (`InferencePipeline` + `StreamingVADGate`) extrae UNA ventana de ~2 s con UN comando cuando el VAD detecta fin de voz. Si entrenamos con clips que contienen varias palabras seguidas, el modelo aprende patrones de cadenas que en inferencia no aparecen.
2. **Sin segmentador post-hoc no hay errores de etiquetado**. Cortar un audio largo en N clips requiere un VAD que decida dónde empieza y termina cada palabra. Cualquier error de segmentación (cortar a mitad de un fonema, incluir silencio etiquetado como voz, fundir dos palabras) contamina la etiqueta. Una palabra por archivo elimina ese problema de raíz.
3. **Variación natural entre tomas**. Cada presionar-ENTER es un reset cognitivo del voluntario: nueva respiración, entonación ligeramente distinta, posible variación de velocidad. Esa variación es exactamente la que queremos en el corpus.
4. **Control de calidad por clip**. Si una toma sale mal (tos, risa, eco, voz lejos del mic) se rechaza y se repite. Con grabación corrida hay que descartar el tramo entero o intentar editarlo manualmente.
5. **`record.py` ya está implementado para este flujo**. Cambia el flujo y hay que reescribir todo.

### 4.2 Tono y pacing

Cuando aparezca el prompt en pantalla y el voluntario presione ENTER:

1. **Respirar normal**. No aguantar el aire ni hacer inhalación profunda.
2. **Leer el comando mentalmente una vez**.
3. **Esperar el beep agudo** (`record.py` lo emite 0.4 s después de ENTER).
4. **Decir la palabra en tono conversacional**, como si le pidieras un favor a alguien al lado tuyo.
   - **No** exagerar la articulación ("E-N-CIEN-DE").
   - **No** susurrar.
   - **No** gritar.
   - **No** hacer voz robótica.
5. **Esperar el beep grave** (señala fin de la toma).
6. **Pausa 1–2 s** mientras `record.py` valida y guarda.
7. **Si la toma fue rechazada** (`RECHAZADO: ...`), el script repite el mismo prompt. No es un problema; volver a intentar.

**Variación natural permitida y deseable**:
- Hablar a velocidades ligeramente distintas entre tomas.
- Pequeñas variaciones de entonación (afirmativa, neutra, levemente interrogativa).
- Pausa antes del comando que varíe entre 200 ms y 800 ms.

**Variación NO permitida**:
- Cambiar la palabra ("encienda" en lugar de "enciende").
- Cortar el final ("encien-" sin la "-de").
- Añadir muletillas ("eh enciende", "enciende eh").
- Risas o toses dentro de la toma.

### 4.3 Comandos compuestos (`enciende_rapido`, `gira_izquierda`, etc.)

Decir las dos palabras **como una sola frase fluida**, sin pausa marcada entre ellas:
- ✓ "enciende rápido" (con la velocidad normal del habla)
- ✗ "enciende ... rápido" (pausa larga, suena como dos comandos)
- ✗ "enciendrápido" (sin espacio audible, fusión)

El operador puede leer el prompt en voz alta una vez antes de empezar la primera repetición de cada clase compuesta, para asegurarse de que el voluntario entendió el ritmo esperado.

---

## 5. Posición del lavalier y ganancia

### 5.1 Pinzar el transmisor

```
       (cara del voluntario)
              |
              | ~20 cm
              |
        ┌─────▼─────┐
        │   pinza   │  ← lavalier clipeado en la solapa de la camisa,
        │  DJI TX   │     a unos 20 cm bajo la barbilla,
        └───────────┘     en el mismo lado para todos los voluntarios
              │
        (pecho/camisa)
```

- Pinza siempre en el **mismo lado** (por convención: lado izquierdo del voluntario, sobre la solapa de la camisa).
- Distancia constante: **~20 cm bajo la barbilla**. Marcar con cinta una guía en la propia solapa o en la mesa donde se sienta el voluntario.
- El cápsula del mic **apunta hacia arriba** (a la boca), no hacia abajo o hacia los lados.
- Si el voluntario tiene cabello largo, asegurarse que no roce el mic — el roce genera artefactos peores que el ruido ambiente.

### 5.2 Ajuste de ganancia del receptor (perilla rotativa)

La perilla en la parte superior del receptor controla la ganancia analógica antes del USB.

1. Conectar todo. Pedirle al voluntario que diga "enciende" en tono normal.
2. Mirar el medidor de nivel en `System Settings → Sound → Input`. Apuntar a **2/3 de la barra**, no al máximo.
3. Hacer un smoke test (sección 3.6). Validar `peak < 0.85` y `rms ≈ 0.05–0.20`.
4. Una vez encontrada la posición correcta, **marcarla con un sticker o cinta** en la perilla. No moverla durante las sesiones.
5. Si entre voluntarios hay diferencia grande de volumen de voz (voz muy potente vs voz suave), ajustar de a 1 click la perilla, no mover globalmente.

### 5.3 Verificación entre voluntarios

Después de pinzar el lavalier en un nuevo voluntario, hacer **2 tomas de prueba** que NO se guarden:
```bash
python -c "
import sounddevice as sd, numpy as np
audio = sd.rec(int(2*16000), 16000, channels=1, dtype='float32', blocking=True)
peak = float(np.max(np.abs(audio))); rms = float(np.sqrt(np.mean(audio**2)))
print(f'peak={peak:.3f} rms={rms:.3f}')
"
```
Y pedirle al voluntario que diga "enciende" durante esos 2 s. Si `peak > 0.90` o `rms < 0.03`, ajustar perilla o reposicionar pinza antes de empezar la sesión real.

---

## 6. Cronograma de 2 días

### 6.1 Resumen

| Día | Entorno | Reps por clase | Total voz | Total ruido | Tiempo estimado |
|---|---|---|---|---|---|
| Día 1 | salon_silencioso | 25 × 9 × 5 hablantes | 1125 | 100 (sesiones 1 y 2 de ruido) | ~3 h |
| Día 2 | laboratorio | 10 × 9 × 5 hablantes | 450 | 100 (sesiones 3 y 4 de ruido) | ~2 h |
| **Total** | | | **1575** | **200** | **~5 h en 2 días** |

**Total del corpus: 1775 muestras** (18 % de margen sobre el mínimo de 1500).

### 6.2 Día 1 — salón silencioso

| Bloque | Duración | Actividad |
|---|---|---|
| 14:00 – 14:30 | 30 min | Setup: armar mic, configurar macOS, smoke test |
| 14:30 – 14:55 | 25 min | **Voluntario spk01**: 25 reps × 9 clases = 225 clips |
| 14:55 – 15:05 | 10 min | Break + cambio de voluntario + ajuste de pinza |
| 15:05 – 15:30 | 25 min | **Voluntario spk02**: 225 clips |
| 15:30 – 15:40 | 10 min | Break |
| 15:40 – 16:05 | 25 min | **Voluntario spk03**: 225 clips |
| 16:05 – 16:15 | 10 min | Break |
| 16:15 – 16:40 | 25 min | **Voluntario spk04**: 225 clips |
| 16:40 – 16:50 | 10 min | Break |
| 16:50 – 17:15 | 25 min | **Voluntario spk05**: 225 clips |
| 17:15 – 17:25 | 10 min | Sesión `ruido_fondo` 1: silencio total (50 clips) |
| 17:25 – 17:35 | 10 min | Sesión `ruido_fondo` 4: habla irrelevante junto al mic (50 clips) |
| 17:35 – 17:50 | 15 min | Auditoría con `audit_corpus.py`, backup a Drive, commit del manifest |

**Total día 1**: ~3 h 50 min. Ajustar horarios según disponibilidad real de los voluntarios; lo importante es el orden, no las horas exactas.

### 6.3 Día 2 — laboratorio

| Bloque | Duración | Actividad |
|---|---|---|
| 14:00 – 14:20 | 20 min | Mover el setup a la sala laboratorio. Re-verificar nivel (puede cambiar por acústica) |
| 14:20 – 14:32 | 12 min | **Voluntario spk01**: 10 reps × 9 clases = 90 clips |
| 14:32 – 14:40 | 8 min | Break + cambio |
| 14:40 – 14:52 | 12 min | **Voluntario spk02**: 90 clips |
| 14:52 – 15:00 | 8 min | Break |
| 15:00 – 15:12 | 12 min | **Voluntario spk03**: 90 clips |
| 15:12 – 15:20 | 8 min | Break |
| 15:20 – 15:32 | 12 min | **Voluntario spk04**: 90 clips |
| 15:32 – 15:40 | 8 min | Break |
| 15:40 – 15:52 | 12 min | **Voluntario spk05**: 90 clips |
| 15:52 – 16:02 | 10 min | Sesión `ruido_fondo` 2: laboratorio con ventilación / equipo (50 clips) |
| 16:02 – 16:12 | 10 min | Mover el receptor al pasillo. Sesión `ruido_fondo` 3 (50 clips) |
| 16:12 – 16:30 | 18 min | Auditoría final, backup completo, generación de splits, commit |

**Total día 2**: ~2 h 30 min.

### 6.4 Anotaciones operativas

- **El mismo voluntario debe ir al mismo `speaker_id` los dos días** (spk01 día 1 = spk01 día 2). Esto permite al modelo aprender la variación intra-hablante entre entornos.
- Si un voluntario sólo viene un día, no es problema: tendrá menos clips pero seguirá representando una voz distinta.
- **Mantener un registro fuera del repo**: `backend/data/manifests/speakers.csv` con `speaker_id,nombre_real,sesion_date,notas`. Está en `.gitignore`.
- **Dejar al voluntario un minuto antes de empezar** para que se siente, se acomode y bebe agua.

---

## 7. Comandos exactos por sesión

Sustituir `--gender` y `--age` por los valores reales de cada voluntario. Las opciones válidas:

- `--gender`: `M`, `F`, `X`
- `--age`: `18-25`, `26-35`, `36-50`, `50+`

### 7.1 Día 1 — salón silencioso (25 reps × 9 clases por voluntario)

```bash
cd backend
source .venv/bin/activate

# Voluntario 1
python -m src.cli.record \
    --speaker spk01 --gender M --age 18-25 \
    --environment salon_silencioso --device dji_mic_mini_v1 \
    --classes enciende,apaga,izquierda,derecha,detente,enciende_rapido,enciende_lento,gira_izquierda,gira_derecha \
    --repeats 25 --shuffle --seed 42

# Voluntario 2 (cambiar --speaker spk02 y los datos demográficos)
python -m src.cli.record \
    --speaker spk02 --gender F --age 18-25 \
    --environment salon_silencioso --device dji_mic_mini_v1 \
    --classes enciende,apaga,izquierda,derecha,detente,enciende_rapido,enciende_lento,gira_izquierda,gira_derecha \
    --repeats 25 --shuffle --seed 42

# Voluntario 3 ... 4 ... 5 (idem, ajustar --speaker, --gender, --age)
```

### 7.2 Día 2 — laboratorio (10 reps × 9 clases por voluntario)

```bash
python -m src.cli.record \
    --speaker spk01 --gender M --age 18-25 \
    --environment laboratorio --device dji_mic_mini_v1 \
    --classes enciende,apaga,izquierda,derecha,detente,enciende_rapido,enciende_lento,gira_izquierda,gira_derecha \
    --repeats 10 --shuffle --seed 42

# ... repetir para spk02 ... spk05 con sus datos
```

**Importante**: NO cambiar el `seed` entre sesiones. Si dos voluntarios usan el mismo seed con `--shuffle`, el orden de clases que ven es el mismo, lo cual facilita el ritmo del operador (que aprende el flujo y no se confunde).

---

## 8. Sesiones de `ruido_fondo`

Total objetivo: **200 clips** distribuidos en 4 contextos. Los hablantes pueden ser cualquier integrante del grupo; el `speaker_id` queda vacío porque la clase no es de voz dirigida al sistema.

### 8.1 Sesión 1 — Silencio total (día 1, salón silencioso)

Sala cerrada, sin nadie hablando. El mic graba el piso de ruido (ventilación apagada idealmente, o lo más silenciosa posible).

```bash
python -m src.cli.record \
    --speaker "" --gender X --age 18-25 \
    --environment salon_silencioso --device dji_mic_mini_v1 \
    --classes ruido_fondo --repeats 50
```

El operador sólo presiona ENTER 50 veces sin que nadie hable. Tarda ~5 min.

### 8.2 Sesión 2 — Laboratorio con ruido moderado (día 2)

Misma idea, pero en la sala laboratorio con el ventilador / aire acondicionado / equipo zumbando. Sin voces dirigidas al mic.

```bash
python -m src.cli.record \
    --speaker "" --gender X --age 18-25 \
    --environment laboratorio --device dji_mic_mini_v1 \
    --classes ruido_fondo --repeats 50
```

### 8.3 Sesión 3 — Pasillo o zona de tránsito (día 2)

Llevar el receptor al pasillo. Capturar sonidos ambientes: pasos, puertas, conversaciones distantes (que no se entiendan claramente). El transmisor queda sobre una mesa o pinzado al operador.

```bash
python -m src.cli.record \
    --speaker "" --gender X --age 18-25 \
    --environment pasillo_ruidoso --device dji_mic_mini_v1 \
    --classes ruido_fondo --repeats 50
```

### 8.4 Sesión 4 — Habla irrelevante junto al mic (día 1)

**Crítica**: aquí el voluntario sí habla, pero diciendo palabras que NO son ninguno de los 10 comandos. Le enseña al modelo a rechazar habla no relacionada (que va a pasar mucho en la defensa: gente del público hablando cerca, palabras sueltas que se parecen a "enciende", etc.).

Ejemplos de palabras/frases a decir:
- Números: "uno", "dos", "tres", "cinco mil"
- Saludos: "hola", "buenas tardes", "qué tal"
- Palabras parecidas pero NO comandos: "encender" (infinitivo, no "enciende"), "apaguen", "girando", "girar"
- Frases sueltas: "no entiendo", "puede repetir", "está bien"

```bash
python -m src.cli.record \
    --speaker "" --gender X --age 18-25 \
    --environment salon_silencioso --device dji_mic_mini_v1 \
    --classes ruido_fondo --repeats 50
```

El operador puede mostrar una lista de palabras al voluntario para variar.

---

## 9. Post-sesión: auditoría y backup

### 9.1 Auditar el corpus al cierre de cada día

```bash
cd backend
python -m scripts.audit_corpus
```

Verificar:
- **Conteo por clase**: las 9 clases con voz deberían tener exactamente `n_voluntarios * reps` clips. `ruido_fondo` suma incrementalmente.
- **Conteo por hablante**: cada `spkNN` con `n_clases * reps` clips.
- **Matriz hablante × clase**: sin celdas vacías.
- **Huérfanos o faltantes**: cero. Si hay, investigar (probablemente `record.py` se interrumpió a mitad de un clip).
- **SNR**: mediano > 18 dB, sin clips no-ruido con SNR < 8 dB.

### 9.2 Backup del corpus crudo

Los WAVs están en `.gitignore`. Subirlos a la carpeta compartida del grupo en Drive después de cada sesión:

```
voz-corpus-grupo/
├── 2026-05-14-dia1/
│   ├── raw/
│   │   ├── enciende/
│   │   ├── apaga/
│   │   └── ...
│   └── corpus.csv         (copia del manifest hasta ese punto)
└── 2026-05-15-dia2/
    └── ...
```

Mínimo 2 propietarios de la carpeta para que si una persona se cae, el corpus no se pierde.

### 9.3 Commitear el manifest (sí, los WAVs no)

```bash
git add backend/data/manifests/corpus.csv
git commit -m "data: sesión día 1, 5 voluntarios en salón silencioso (1225 clips)"
git push
```

### 9.4 Después de la última sesión: generar splits

```bash
python -m scripts.generate_splits --test-speakers 2 --val-frac 0.15 --seed 42
```

Esto reescribe la columna `split` del manifest y crea `data/splits/{train,val,test}.csv`.

**Ajuste recomendado para 5 hablantes**: si en el reporte del trainer la métrica de test queda muy ruidosa (poca data), bajar a 1 hablante held-out y subir val_frac:

```bash
python -m scripts.generate_splits --test-speakers 1 --val-frac 0.20 --seed 42
```

### 9.5 Aumentar el corpus (offline)

```bash
python -m scripts.augment_offline --train-only --variants 4 --seed 42
```

Genera `data/augmented/<clase>/*.wav` con 4 variantes por clip de entrenamiento. No toca val ni test (sería data leakage).

---

## 10. Troubleshooting

### "No se detecta dispositivo de entrada" o `record.py` se cuelga

- Verificar que el receptor DJI esté conectado y prendido (LED encendido).
- En `System Settings → Sound → Input`, ¿aparece el DJI? Si no: desconectar y reconectar el USB-C.
- Re-otorgar permiso al Terminal: `System Settings → Privacy & Security → Microphone`.
- Probar con `--mic 2` (o el índice que muestre `sd.query_devices()`) para forzar el dispositivo.

### Todos los clips se rechazan por clipping (`peak > 0.95`)

- Bajar la perilla de ganancia del receptor 2-3 clicks.
- Si persiste, bajar el "Input volume" de macOS al 50 %.
- Verificar que el voluntario no esté hablando demasiado fuerte o muy cerca del mic.
- Verificar que la pinza esté a 20 cm de la boca, no a 5 cm.

### Todos los clips se rechazan por señal débil (`rms < 0.01`)

- Subir la perilla del receptor 2-3 clicks.
- Verificar que el voluntario no esté susurrando.
- Confirmar que el transmisor está prendido y emparejado (LED del receptor estable, no parpadeando).
- Verificar que no haya algo bloqueando el mic (cabello, ropa, scarf).

### El VAD no detecta voz pero sí hay voz

- El piso de ruido inicial del clip puede ser raro. `record.py` usa los primeros 30 ms como referencia.
- Pedirle al voluntario que pause 300 ms entre presionar ENTER y empezar a hablar.
- Si persiste, posiblemente la ganancia es demasiado baja (RMS muy cercano al piso).

### Voice Isolation se activa solo en macOS Sonoma+

- Abrir Control Center mientras `record.py` graba (icono arriba a la derecha de la barra de menú).
- Bajar a `Mic Mode` y verificar que esté en `Standard`. Si está en Voice Isolation, cambiarlo.
- Este setting es **por aplicación**. Una vez puesto Standard para Terminal, queda persistido.

### El mic genera "popping" (plosivas, "p", "b", "t" explosivas)

- Reposicionar la pinza levemente off-axis (un poco hacia el costado, no apuntando directo a la boca).
- Si la sala lo permite, pedirle al voluntario que hable un poquito hacia el costado, no de frente.
- DJI Mic Mini viene con una espuma anti-pop opcional — no usarla en interior pero si los pops persisten, ponerla.

### El transmisor se descarga durante la sesión

- Conectar el cargador al transmisor mientras graba (no afecta la señal).
- O hacer pausa, cargar 15 min, continuar. La batería dura ~3 h sin NC.

### `record.py` interrumpido a la mitad de una clase

- No pasa nada: las filas ya escritas en el manifest se mantienen.
- Re-lanzar el comando con la misma `--speaker` y reducir `--repeats` a las que falten.
- Antes de re-lanzar, revisar el manifest: `grep spk01 backend/data/manifests/corpus.csv | grep enciende | wc -l` debe darte cuántos clips de esa clase ya tenés.

---

## 11. Checklist final del corpus

Antes de pasar al entrenamiento, verificar:

- [ ] `python -m scripts.audit_corpus` pasa sin warnings rojos.
- [ ] Total ≥ 1500 clips entre las 10 clases.
- [ ] Cada clase con voz tiene ≥ 100 clips.
- [ ] `ruido_fondo` tiene ≥ 200 clips repartidos en al menos 3 entornos.
- [ ] Al menos 5 hablantes con sus 9 clases completas.
- [ ] Al menos 2 entornos representados (salon_silencioso + laboratorio).
- [ ] Al menos 2 voces de cada género.
- [ ] `data/splits/{train,val,test}.csv` generados.
- [ ] `data/augmented/` poblado con `python -m scripts.augment_offline --train-only`.
- [ ] Backup del corpus crudo en Drive del grupo.
- [ ] Manifest commiteado al repo.
- [ ] `speakers.csv` (con nombres reales) NO commiteado, sólo en Drive privado.

Con todo esto en verde, ya se puede iniciar la fase de entrenamiento del modelo CNN base y luego el BiLSTM.

---

**Fin de la guía.** Para dudas operativas durante la sesión, mantener este documento abierto en una pestaña al lado de la terminal.
