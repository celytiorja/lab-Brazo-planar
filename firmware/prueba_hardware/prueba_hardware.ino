/*
  PRUEBA DE HARDWARE — Brazo planar 2 GDL
  =======================================
  Objetivo: comprobar que TODO está bien conectado antes de escribir el
  programa definitivo. Hace 3 cosas:
    1) Escanea el bus I2C y dice qué IMU encontró (esperado: 0x68 y 0x69).
    2) Lee las dos MPU-6050 y muestra giroscopio y acelerómetro.
    3) Mueve los servos con comandos escritos en el Monitor Serie.

  Comandos (Monitor Serie a 115200 baudios, fin de línea "Nueva línea"):
    h 90   -> servo del HOMBRO a 90°
    c 45   -> servo del CODO a 45°
    imu    -> activa/desactiva la impresión de las IMU

  Librería necesaria: "ESP32Servo" de Kevin Harrington (Gestor de librerías).
  Las IMU se leen directamente por registros (sin librería) para que veas
  cómo funciona por dentro.
*/
#include <Wire.h>
#include <ESP32Servo.h>

// ---------- Pines (ver docs/02_conexiones.md) ----------
const int PIN_SERVO_HOMBRO = 25;
const int PIN_SERVO_CODO   = 26;
const int PIN_SDA = 21;
const int PIN_SCL = 22;

// ---------- Direcciones I2C ----------
const uint8_t IMU1 = 0x68;  // eslabón 1 (hombro), AD0 a GND o sin conectar
const uint8_t IMU2 = 0x69;  // eslabón 2 (codo),   AD0 a 3.3 V

// ---------- Registros de la MPU-6050 (hoja de datos) ----------
const uint8_t REG_PWR_MGMT_1   = 0x6B;
const uint8_t REG_CONFIG       = 0x1A;  // filtro paso bajo digital (DLPF)
const uint8_t REG_GYRO_CONFIG  = 0x1B;
const uint8_t REG_ACCEL_CONFIG = 0x1C;
const uint8_t REG_ACCEL_XOUT_H = 0x3B;  // primer byte de los 14 de datos
const uint8_t REG_WHO_AM_I     = 0x75;

// Escalas elegidas:
//  Giroscopio ±500 °/s -> 65.5 cuentas por °/s. (Un MG996R gira ~350 °/s, así
//  que ±250 °/s se saturaría en movimientos rápidos.)
//  Acelerómetro ±2 g   -> 16384 cuentas por g.
const float GYRO_LSB_POR_DPS = 65.5;
const float ACC_LSB_POR_G    = 16384.0;

Servo servoHombro, servoCodo;
bool imprimirIMU = true;

void escribirRegistro(uint8_t dir, uint8_t reg, uint8_t valor) {
  Wire.beginTransmission(dir);
  Wire.write(reg);
  Wire.write(valor);
  Wire.endTransmission();
}

uint8_t leerRegistro(uint8_t dir, uint8_t reg) {
  Wire.beginTransmission(dir);
  Wire.write(reg);
  Wire.endTransmission(false);       // false = no soltar el bus (lectura repetida)
  Wire.requestFrom(dir, (uint8_t)1);
  return Wire.available() ? Wire.read() : 0xFF;
}

bool iniciarIMU(uint8_t dir) {
  uint8_t quienSoy = leerRegistro(dir, REG_WHO_AM_I);
  Serial.printf("  IMU 0x%02X: WHO_AM_I = 0x%02X %s\n", dir, quienSoy,
                quienSoy == 0x68 ? "(OK)" : "(¡NO RESPONDE BIEN!)");
  if (quienSoy != 0x68) return false;
  escribirRegistro(dir, REG_PWR_MGMT_1, 0x01);   // despertar, reloj = PLL del giro X
  escribirRegistro(dir, REG_CONFIG, 0x03);       // DLPF ~44 Hz
  escribirRegistro(dir, REG_GYRO_CONFIG, 0x08);  // ±500 °/s
  escribirRegistro(dir, REG_ACCEL_CONFIG, 0x00); // ±2 g
  return true;
}

// Lee 14 bytes seguidos: ax ay az temp gx gy gz (cada uno 16 bits con signo).
bool leerIMU(uint8_t dir, float acc[3], float gyro[3]) {
  Wire.beginTransmission(dir);
  Wire.write(REG_ACCEL_XOUT_H);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(dir, (uint8_t)14) != 14) return false;
  int16_t crudo[7];
  for (int i = 0; i < 7; i++) {
    uint8_t alto = Wire.read();   // se leen por separado: C++ no garantiza el orden
    uint8_t bajo = Wire.read();   // de evaluación dentro de una misma expresión
    crudo[i] = (int16_t)((alto << 8) | bajo);
  }
  for (int i = 0; i < 3; i++) {
    acc[i]  = crudo[i] / ACC_LSB_POR_G;
    gyro[i] = crudo[i + 4] / GYRO_LSB_POR_DPS;   // crudo[3] es la temperatura
  }
  return true;
}

void escanearI2C() {
  Serial.println("Escaneando bus I2C...");
  int encontrados = 0;
  for (uint8_t dir = 1; dir < 127; dir++) {
    Wire.beginTransmission(dir);
    if (Wire.endTransmission() == 0) {
      Serial.printf("  Dispositivo en 0x%02X\n", dir);
      encontrados++;
    }
  }
  if (encontrados == 0) Serial.println("  Ninguno. Revisa SDA/SCL, VCC y GND.");
}

void procesarComando(String linea) {
  linea.trim();
  if (linea == "imu") { imprimirIMU = !imprimirIMU; return; }
  if (linea.length() < 3) return;
  char cual = linea.charAt(0);
  int angulo = constrain(linea.substring(2).toInt(), 0, 180);
  if (cual == 'h') { servoHombro.write(angulo); Serial.printf("Hombro -> %d°\n", angulo); }
  if (cual == 'c') { servoCodo.write(angulo);   Serial.printf("Codo -> %d°\n", angulo); }
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== Prueba de hardware ===");

  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);   // I2C rápido: 400 kHz
  escanearI2C();
  iniciarIMU(IMU1);
  iniciarIMU(IMU2);

  // MG996R: pulso de 500 a 2500 µs ≈ 0° a 180° (puede variar por unidad).
  servoHombro.setPeriodHertz(50);
  servoCodo.setPeriodHertz(50);
  servoHombro.attach(PIN_SERVO_HOMBRO, 500, 2500);
  servoCodo.attach(PIN_SERVO_CODO, 500, 2500);
  servoHombro.write(90);
  servoCodo.write(90);
  Serial.println("Servos en 90°. Escribe 'h <ángulo>', 'c <ángulo>' o 'imu'.");
}

void loop() {
  if (Serial.available()) procesarComando(Serial.readStringUntil('\n'));

  static unsigned long ultimo = 0;
  if (imprimirIMU && millis() - ultimo >= 200) {   // 5 veces por segundo
    ultimo = millis();
    float a1[3], g1[3], a2[3], g2[3];
    bool ok1 = leerIMU(IMU1, a1, g1);
    bool ok2 = leerIMU(IMU2, a2, g2);
    if (ok1) Serial.printf("IMU1 g[°/s]=%7.2f %7.2f %7.2f  a[g]=%5.2f %5.2f %5.2f | ",
                           g1[0], g1[1], g1[2], a1[0], a1[1], a1[2]);
    else     Serial.print("IMU1 sin datos | ");
    if (ok2) Serial.printf("IMU2 g[°/s]=%7.2f %7.2f %7.2f  a[g]=%5.2f %5.2f %5.2f\n",
                           g2[0], g2[1], g2[2], a2[0], a2[1], a2[2]);
    else     Serial.println("IMU2 sin datos");
  }
}
