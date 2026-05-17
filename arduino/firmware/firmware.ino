/*
  Asistente Robotico por Voz - Firmware Arduino UNO
  Protocolo serial: 115200 bps, comandos ASCII terminados en '\n'.
  Debe coincidir con backend/src/domain/commands.py.

  Pinout (igual que docs/Texto_Arduino.txt):
    D2          RELE
    D3          BUZZER pasivo (tone/noTone)
    D4          BUZZER activo (HIGH/LOW)
    D5 / D6 / D9   LED RGB (R / G / B, PWM)
    D13         LED VERDE  (sistema en escucha)
    A0          LED AMARILLO (procesando)
    A1          LED ROJO  (rechazo / alarma)

  Notas:
    - Cambia RELE_ACTIVO_LOW si tu relé se activa con HIGH.
    - El LED RGB asume cátodo común (HIGH = más intensidad).
*/

// =====================================================================
// Pines del proyecto
// =====================================================================
const int PIN_RELE          = 2;

const int PIN_BUZZER_PASIVO = 3;
const int PIN_BUZZER_ACTIVO = 4;

const int PIN_RGB_R = 5;
const int PIN_RGB_G = 6;
const int PIN_RGB_B = 9;

const int PIN_LED_VERDE    = 13;
const int PIN_LED_AMARILLO = A0;
const int PIN_LED_ROJO     = A1;

// true: relé se activa con LOW (módulos comunes de 1 canal)
// false: relé se activa con HIGH
const bool RELE_ACTIVO_LOW = false;

String comando = "";

// =====================================================================
// Setup / Loop
// =====================================================================
void setup() {
  Serial.begin(115200);

  pinMode(PIN_RELE, OUTPUT);

  pinMode(PIN_BUZZER_PASIVO, OUTPUT);
  pinMode(PIN_BUZZER_ACTIVO, OUTPUT);

  pinMode(PIN_RGB_R, OUTPUT);
  pinMode(PIN_RGB_G, OUTPUT);
  pinMode(PIN_RGB_B, OUTPUT);

  pinMode(PIN_LED_VERDE, OUTPUT);
  pinMode(PIN_LED_AMARILLO, OUTPUT);
  pinMode(PIN_LED_ROJO, OUTPUT);

  apagarTodo();

  digitalWrite(PIN_LED_VERDE, HIGH); // Sistema en escucha
  Serial.println("Arduino listo para recibir comandos.");
}

void loop() {
  if (Serial.available() > 0) {
    comando = Serial.readStringUntil('\n');
    comando.trim();
    comando.toLowerCase();

    if (comando.length() == 0) {
      return;
    }

    Serial.print("Comando recibido: ");
    Serial.println(comando);

    ejecutarComando(comando);
  }
}

// =====================================================================
// Despacho de comandos (espejo de domain/commands.py)
// =====================================================================
void ejecutarComando(String cmd) {
  if (cmd == "enciende") {
    encenderRele();
    setRGB(255, 255, 255);
    beepActivo(100);
  }
  else if (cmd == "apaga") {
    apagarRele();
    setRGB(0, 0, 0);
    beepActivo(100);
  }
  else if (cmd == "detente") {
    apagarTodo();
    beepActivo(250);
  }
  else if (cmd == "rojo") {
    setRGB(255, 0, 0);
  }
  else if (cmd == "verde") {
    setRGB(0, 255, 0);
  }
  else if (cmd == "azul") {
    setRGB(0, 0, 255);
  }
  else if (cmd == "blanco") {
    setRGB(255, 255, 255);
  }
  else if (cmd == "procesando") {
    estadoProcesando();
  }
  else if (cmd == "rechazo") {
    estadoRechazo();
  }
  else if (cmd == "alarma") {
    alarma();
  }
  else if (cmd == "tono") {
    tonoCompuesto();
  }
  else if (cmd == "off") {
    apagarTodo();
  }
  else {
    estadoRechazo();
  }
}

// =====================================================================
// Helpers
// =====================================================================
void encenderRele() {
  digitalWrite(PIN_RELE, RELE_ACTIVO_LOW ? LOW : HIGH);
}

void apagarRele() {
  digitalWrite(PIN_RELE, RELE_ACTIVO_LOW ? HIGH : LOW);
}

void setRGB(int r, int g, int b) {
  analogWrite(PIN_RGB_R, r);
  analogWrite(PIN_RGB_G, g);
  analogWrite(PIN_RGB_B, b);
}

void beepActivo(int tiempoMs) {
  digitalWrite(PIN_BUZZER_ACTIVO, HIGH);
  delay(tiempoMs);
  digitalWrite(PIN_BUZZER_ACTIVO, LOW);
}

void tonoCompuesto() {
  tone(PIN_BUZZER_PASIVO, 800, 150);
  delay(180);
  tone(PIN_BUZZER_PASIVO, 1200, 150);
  delay(180);
  tone(PIN_BUZZER_PASIVO, 1600, 200);
  delay(250);
  noTone(PIN_BUZZER_PASIVO);
}

void alarma() {
  for (int i = 0; i < 4; i++) {
    setRGB(255, 0, 0);
    tone(PIN_BUZZER_PASIVO, 1000);
    digitalWrite(PIN_BUZZER_ACTIVO, HIGH);
    delay(180);

    setRGB(0, 0, 0);
    noTone(PIN_BUZZER_PASIVO);
    digitalWrite(PIN_BUZZER_ACTIVO, LOW);
    delay(180);
  }
}

void estadoProcesando() {
  digitalWrite(PIN_LED_VERDE, LOW);
  digitalWrite(PIN_LED_AMARILLO, HIGH);
  digitalWrite(PIN_LED_ROJO, LOW);

  setRGB(255, 180, 0);
  delay(500);

  digitalWrite(PIN_LED_AMARILLO, LOW);
  digitalWrite(PIN_LED_VERDE, HIGH);
}

void estadoRechazo() {
  digitalWrite(PIN_LED_VERDE, LOW);
  digitalWrite(PIN_LED_AMARILLO, LOW);
  digitalWrite(PIN_LED_ROJO, HIGH);

  setRGB(255, 0, 0);
  tone(PIN_BUZZER_PASIVO, 250, 300);
  delay(500);

  digitalWrite(PIN_LED_ROJO, LOW);
  digitalWrite(PIN_LED_VERDE, HIGH);
  noTone(PIN_BUZZER_PASIVO);
}

void apagarTodo() {
  apagarRele();

  setRGB(0, 0, 0);

  digitalWrite(PIN_BUZZER_ACTIVO, LOW);
  noTone(PIN_BUZZER_PASIVO);

  digitalWrite(PIN_LED_VERDE, HIGH);
  digitalWrite(PIN_LED_AMARILLO, LOW);
  digitalWrite(PIN_LED_ROJO, LOW);
}
