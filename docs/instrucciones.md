Universidad Rafael Landívar
Inteligencia Artificial
Primer Semestre 2025

PROYECTO FINAL

Asistente Robótico por Comandos de Voz

Modalidad

Grupos de 3 a 4 estudiantes

Valor

Entrega

10 puntos netos  ·  Rúbrica sobre 100 puntos

Lunes 18 de mayo de 2026 (código y documentación)

Presentación

Miércoles 20 de mayo de 2026

Descripción General

El  objetivo  de  este  proyecto  es  integrar  técnicas  de  procesamiento  digital  de  señales,  aprendizaje

automático  y  sistemas  embebidos  para  construir  un  Asistente  Robótico  por  Comandos  de  Voz.  Los

estudiantes  deberán  desarrollar  un  sistema  capaz  de  escuchar  al  usuario  a  través  de  un  micrófono,

reconocer  un  conjunto  cerrado  de  comandos  en  español  pronunciados  en  tiempo  real  y ejecutar una

acción física coordinada sobre un robot móvil, un brazo robótico o un actuador equivalente.

El proyecto se divide en dos componentes críticos:

1.  Reconocimiento  de  Comandos  (Modelo  Base):  Implementación  de  un  modelo  de  clasificación
(Red Neuronal Convolucional, Red Densa o SVM) entrenado desde cero por los estudiantes sobre
características espectrales (MFCC, Mel-Spectrogram) extraídas de grabaciones de audio propias. El
modelo debe clasificar al menos cinco comandos discretos en tiempo real.

2.  Procesamiento  Secuencial  (Módulo  Avanzado):  Implementación  de  una  red recurrente (LSTM o
GRU)  entrenada  por  los  estudiantes  para  reconocer  comandos  compuestos  o  secuencias  de
palabras  (por  ejemplo,  "avanza  tres  metros",  "gira  a  la  derecha  y  detente"),  ampliando  la
capacidad expresiva del sistema más allá de palabras aisladas.

A  diferencia  de  un  sistema  que simplemente invoca una API de reconocimiento de voz comercial, este

proyecto exige que el estudiante gestione todo el pipeline: captura y segmentación de audio, extracción

de características, entrenamiento supervisado con un dataset propio, inferencia en hardware embebido

y control de actuadores con baja latencia. La prohibición explícita de usar servicios externos o modelos

preentrenados "caja negra" garantiza que el estudiante demuestre dominio conceptual y práctico de los

algoritmos de aprendizaje automático.

Asimismo, cada grupo es responsable del diseño y construcción de su propio banco de pruebas físico, así

como  de  la  recolección  del  corpus  de  audio  de  entrenamiento  en  condiciones  representativas  del

entorno operativo, lo cual garantiza la variabilidad necesaria para obtener modelos robustos.

Dataset

Para este proyecto se trabajará con un enfoque mixto de generación de datos propia y aprovechamiento

de corpus públicos complementarios:

1. Corpus de Voz Propio (Obligatorio)

•  Cada grupo deberá recolectar y etiquetar un mínimo de 1,500 muestras de audio grabadas por los
integrantes del grupo y al menos cinco voluntarios externos (para garantizar variabilidad de timbre
y género).

•  Cada muestra debe durar entre 1 y 2 segundos y ser grabada a 16 kHz como mínimo.

•  Comandos obligatorios (mínimo 5 clases): AVANZA, RETROCEDE, IZQUIERDA, DERECHA, DETENTE.
Los  grupos  pueden  agregar  comandos  adicionales  según  la  aplicación  elegida  (por  ejemplo,
ENCIENDE, APAGA, RÁPIDO, LENTO).

•  Debe incluirse una clase adicional "RUIDO_FONDO" con al menos 200 muestras de silencio, ruido

ambiente y habla no relacionada, para que el modelo aprenda a rechazar entradas espurias.

•  Las grabaciones deben realizarse en al menos dos entornos distintos (por ejemplo, salón silencioso

y laboratorio con ruido moderado).

2. Corpus Público Complementario (Recomendado)

•  Google Speech Commands Dataset (v2): disponible en TensorFlow Datasets. Contiene 35 palabras
en inglés grabadas por miles de hablantes. Útil para comparar resultados, realizar transferencia de
aprendizaje inicial o pruebas de referencia.

•  Mozilla  Common  Voice  (subconjunto  español):  puede  utilizarse  para  enriquecer  el  dataset  de

ruido de fondo y exposición a habla continua en español.

•  El  uso  del  corpus  público  es  opcional  y  únicamente  como  complemento;  el  modelo  final  debe

evaluarse sobre el corpus propio del grupo.

Especificaciones del Banco de Pruebas

Cada equipo deberá presentar un montaje físico funcional que demuestre la integración entre el motor

de inferencia y un actuador real. Se aceptan tres modalidades de aplicación, y el grupo debe elegir una al

inicio del proyecto:

Modalidad A — Robot Móvil

•  Chasis con dos motores DC y tracción diferencial.

•  Debe responder a los cinco comandos base con movimientos claramente diferenciables.

•  Pista o área de pruebas de al menos 2 m × 2 m con marcadores de inicio y fin.

Modalidad B — Brazo Robótico o Actuador Articulado

•  Mínimo tres grados de libertad controlados por servomotores.

•  Los comandos deben mapear acciones distinguibles (subir, bajar, abrir pinza, cerrar pinza, posición

inicial).

•  Área de trabajo definida donde pueda manipular al menos un objeto físico.

Modalidad C — Panel de Domótica Controlada por Voz

•  Al  menos  cuatro  actuadores  independientes  (relés,  LEDs  de  alta  potencia,  ventilador,  motor,

cerradura simulada).

•  Cada comando enciende, apaga o modifica el estado de un dispositivo diferente.

•  Tablero físico montado sobre placa, madera o acrílico.

Independientemente de la modalidad elegida, el sistema debe funcionar con alimentación independiente

(batería o powerbank) durante la demostración final, para garantizar portabilidad y autonomía.

Objetivos Específicos

•  Diseñar  y  entrenar  una  arquitectura  de  red  neuronal  personalizada  (CNN  1D,  CNN  2D  sobre
espectrogramas,  MLP,  o  SVM con features de audio) para la clasificación de comandos de voz en
tiempo real.

•  Construir  un  pipeline  completo  de  preprocesamiento  de  audio  que  incluya  segmentación,
normalización  de  amplitud,  extracción  de  MFCC  o  Mel-Spectrogram,  y  Voice  Activity  Detection
(VAD) básico.

•  Implementar  un  modelo  secuencial  (LSTM  o GRU) entrenado por los estudiantes para reconocer

comandos compuestos de dos o más palabras.

•  Integrar el motor de inferencia con hardware físico mediante comunicación directa (GPIO, serial) o
inalámbrica  (WiFi,  Bluetooth),  ejecutando  acciones  coordinadas  sobre  motores,  servos  o
actuadores.

•  Optimizar la latencia de extremo a extremo (audio → predicción → actuador) para mantenerla por

debajo de 500 ms en hardware embebido.

•  Aplicar técnicas de aumento de datos específicas para audio (time shifting, pitch shifting, inyección
de ruido, SpecAugment) y evaluar cuantitativamente su impacto sobre la robustez del modelo.

Requisitos Técnicos

Hardware

La  plataforma  de  cómputo  y  control  es  flexible: cada grupo puede elegir la combinación que mejor se

ajuste  a  su aplicación y presupuesto, siempre que justifique técnicamente la decisión en el documento

entregable. Se aceptan las siguientes configuraciones:

•  Configuración A — Raspberry Pi (3B+, 4 o 5): inferencia local completa, micrófono USB o HAT de

audio, control directo de GPIO o puente L298N.

•  Configuración B — Arduino o ESP32 + PC de inferencia: el PC procesa audio y ejecuta el modelo;
el microcontrolador recibe comandos por serial, WiFi o Bluetooth y opera los motores. Útil cuando
el modelo supera la capacidad del dispositivo embebido.

•  Configuración  C  —  ESP32-S3  standalone:

inferencia  embebida  con  modelos  cuantizados
(TensorFlow Lite Micro). Requiere optimización agresiva del modelo y es la opción más exigente en
términos de ingeniería.

Componentes físicos mínimos obligatorios:

•  Micrófono con calidad suficiente para 16 kHz (USB, I2S o analógico con ADC adecuado).

•  Actuadores acordes a la modalidad elegida (motores DC con driver, servomotores, relés).

•  Fuente  de  alimentación  independiente  (batería  de  litio,  powerbank  o  pack  de  baterías  con

regulación apropiada).

•  Chasis, soporte o tablero físico construido o ensamblado por el grupo.

Software y Modelos

•  Lenguaje: Python para entrenamiento; Python, C++ o MicroPython para ejecución en hardware.

•  Librerías permitidas para entrenamiento: TensorFlow/Keras, PyTorch, scikit-learn, librosa, NumPy,

SciPy, Matplotlib.

•  Librerías  permitidas  para  despliegue:  TensorFlow  Lite,  ONNX  Runtime,  PySerial,  pyaudio,

sounddevice, RPi.GPIO, gpiozero.

Restricciones importantes:

•  Modelos:  la  arquitectura  y los pesos deben ser entrenados por los estudiantes desde cero o con
transferencia  de  aprendizaje  justificada. No se permite usar modelos preentrenados "caja negra"
sin ajuste ni modificación.

•  Servicios externos: queda explícitamente prohibido el uso de APIs comerciales de reconocimiento
de  voz  (Google  Speech-to-Text,  Whisper-API,  Azure  Speech,  Amazon  Transcribe,  Picovoice,  Vosk
preentrenado, etc.). El sistema debe funcionar sin conexión a internet durante la evaluación.

•  Extracción  de

features:  se  permite  el  uso  de

librosa  o
python_speech_features  para  calcular  MFCC/espectrogramas,  siempre  que  el  grupo  pueda
explicar matemáticamente lo que esas funciones calculan.

librerías  estándar  como

Técnicas Obligatorias

Técnica

Descripción / Expectativa

Extracción de Features

Cálculo de MFCC (mínimo 13 coeficientes) o Mel-Spectrogram como
representación de entrada al modelo. El grupo debe justificar su elección.

Data Augmentation

Voice Activity Detection

Aplicación de al menos tres técnicas sobre el corpus propio: time shifting,
pitch shifting, inyección de ruido gaussiano/ambiente, time stretching o
SpecAugment.

Segmentación automática de la señal para aislar el tramo con voz y
descartar silencios. Puede implementarse por energía, cruces por cero o
biblioteca ligera (WebRTC VAD).

Modelo Base de Clasificación

CNN 1D/2D, MLP o SVM entrenado desde cero para clasificar comandos
aislados. Arquitectura, hiperparámetros y procedimiento de
entrenamiento justificados por el grupo.

Modelo Secuencial

Red recurrente (LSTM o GRU) entrenada por los estudiantes para
comandos compuestos de dos o más palabras.

Inferencia en Tiempo Real

Pipeline continuo que captura audio, lo segmenta, lo clasifica y acciona el
hardware con latencia total menor a 500 ms.

Control de Hardware

Sincronización entre predicción del modelo y señales de control (PWM,
GPIO, serial, WiFi/Bluetooth) sobre los actuadores físicos.

Producto a Entregar

Fecha de entrega (código y documentación): Lunes 18 de mayo de 2026.

Presentación y defensa: Miércoles 20 de mayo de 2026.

Valor: 10 puntos netos.

Componentes de la Entrega

1. Repositorio del Proyecto (GitHub)

•  Código fuente completo: scripts de grabación, preprocesamiento, entrenamiento y despliegue.

•  Corpus  propio  recolectado  (o  enlace  a  almacenamiento  externo si excede el tamaño permitido),

con estructura de carpetas por clase.

•  Modelos entrenados exportados (.h5, .pt, .tflite u .onnx).

•  Archivo README.md con descripción, instalación, instrucciones de grabación y de ejecución.

•  Notebook Jupyter reproducible con el entrenamiento y la generación de métricas.

2. Documento (PDF)

•  Introducción y descripción del problema.

•  Descripción detallada del corpus propio: tamaño, distribución por clase, condiciones de grabación,

hablantes.

•  Explicación de las arquitecturas (modelo base y modelo secuencial) con diagramas de capas.

•  Descripción  del  preprocesamiento  de  audio  y  justificación  de  los  hiperparámetros  (tamaño  de

ventana, hop length, número de coeficientes MFCC).

•  Matriz  de  confusión  y  reporte  de  métricas  (accuracy,  precisión,  recall,  F1-score)  para  ambos

modelos sobre el conjunto de prueba.

•  Análisis de latencia: tiempos medidos de captura, inferencia y actuación, con tabla de FPS/latencia

por componente.

•  Diagramas  obligatorios:  arquitectura  de  la  solución,  diagrama  de  flujo  del  reconocimiento  en
tiempo  real,  diagrama  de  componentes  hardware-software,  diagrama  de  secuencia  de  una
interacción completa.

•  Evidencias  de  funcionamiento  (capturas  de  pantalla,  fotografías  del  montaje,  gráficas  de

entrenamiento).

•  Conclusiones, limitaciones observadas y propuestas de trabajo futuro.

3. Video de Funcionamiento (máximo 5 minutos)

•  Demostración del sistema operando en tiempo real, sin cortes ni edición engañosa.

•  Ejecución de al menos tres comandos simples y uno compuesto con el modelo secuencial.

•  Demostración del rechazo correcto de ruido de fondo o habla no registrada.

•  Explicación breve del flujo de procesamiento y del hardware empleado.

Rúbrica de Evaluación

La  calificación  se  realiza  sobre  100 puntos que se convierten proporcionalmente a los 10 puntos netos

del  proyecto.  La defensa oral individual tiene un peso determinante para asegurar que cada integrante

demuestre dominio del trabajo entregado.

Criterio

Descripción

Puntaje

1. Documentación Técnica

Diagramas de arquitectura, flujo, secuencia y componentes;
explicación clara de los modelos, del pipeline de
preprocesamiento y de las decisiones técnicas.

2. Recolección y
Procesamiento del Corpus

Calidad, tamaño, variabilidad y balance del corpus propio;
correctitud del pipeline de extracción de features; evidencia
de aumento de datos aplicado.

3. Modelo Base de
Clasificación

4. Modelo Secuencial
(LSTM/GRU)

5. Control de Hardware

6. Integración y Latencia

7. Reporte de Métricas

Precisión del modelo sobre el conjunto de prueba;
justificación de la arquitectura y de los hiperparámetros;
evidencia de entrenamiento propio sin atajos prohibidos.

Implementación y evaluación del modelo recurrente para
comandos compuestos; análisis comparativo frente al
modelo base.

Movimiento correcto y fluido de los actuadores en respuesta
a los comandos reconocidos; robustez de la comunicación
hardware-software.

El sistema reacciona en tiempo real, con latencia menor a
500 ms de extremo a extremo, sin cuelgues ni retrasos
perceptibles.

Análisis cuantitativo: matrices de confusión, precisión, recall,
F1 por clase; análisis crítico de errores y casos
problemáticos.

8. Construcción del Banco de
Pruebas

Calidad del montaje físico, cumplimiento de las
especificaciones de la modalidad elegida, autonomía
energética durante la demostración.

9. Presentación y Defensa

TOTAL

Exposición clara del sistema, demostración en vivo,
respuesta a preguntas técnicas individuales, justificación de
decisiones de diseño y participación equitativa del grupo.

5 pts

8 pts

12 pts

8 pts

10 pts

7 pts

5 pts

5 pts

40 pts

100 pts

Observaciones Adicionales

•  Plagio cero: cada entrega será revisada contra otros grupos y entregas previas. Los proyectos con

coincidencias elevadas en código o documento serán anulados.

•  Uso responsable de asistentes de IA: el uso de herramientas como ChatGPT, Copilot o Claude para
generar ideas o explicar conceptos es aceptable, pero el código entregado debe ser comprendido y
defendido por el grupo. Durante la defensa se harán preguntas individuales orientadas a verificar
la autoría real.

•  Modelos  preentrenados:  queda  prohibido  el  uso  de  modelos  de  reconocimiento  de  voz
preentrenados  como  Whisper,  Vosk,  Wav2Vec2  u  otros  de  Hugging  Face,  incluso  en  modalidad
local. El núcleo del modelo debe ser entrenado por el grupo.

•  Funcionamiento sin internet: durante la presentación, el sistema debe funcionar con conexión de
red desconectada o con el modo avión activo, para comprobar que no se están invocando servicios
remotos.

•  Equilibrio  de  responsabilidades:  el  trabajo  debe  reflejar  una  distribución  equitativa  entre  los

miembros del grupo. Todos los integrantes deben poder explicar cualquier parte del sistema.

•  Se trabajará en grupos de 3 a 4 estudiantes.

Cronograma Sugerido

El siguiente cronograma es referencial y busca orientar a los grupos sobre una distribución razonable del

esfuerzo a lo largo del ciclo. Los grupos pueden adaptarlo según su organización interna.

Periodo

Actividad

Semana 1

Semana 2

Semana 3

Semana 4

Semana 5

Conformación de grupos, elección de modalidad (A, B o C), definición del conjunto de
comandos, adquisición de hardware.

Recolección inicial del corpus propio; diseño del pipeline de preprocesamiento;
primeros experimentos con MFCC.

Entrenamiento del modelo base (CNN/MLP/SVM); evaluación sobre conjunto de
validación; iteración sobre hiperparámetros.

Aumento del corpus, aplicación de data augmentation; entrenamiento del modelo
secuencial (LSTM/GRU).

Integración con hardware: captura en vivo, comunicación con actuadores, pruebas de
latencia.

Semana 6

Construcción final del banco de pruebas; pruebas en entorno real; ajustes de robustez.

Semana 7

Redacción del documento, grabación del video, preparación de la defensa; entrega
final.

— Fin del documento —


