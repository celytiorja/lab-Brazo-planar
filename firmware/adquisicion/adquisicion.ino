/*
  ADQUISICIÓN — Brazo planar 2 GDL (Entregas 1 y 2)
  =================================================
  Hace tres cosas a la vez, a un ritmo FIJO de 100 muestras por segundo:
    1) Lee las dos MPU-6050 (giroscopio + acelerómetro, valores CRUDOS en cuentas).
    2) Mueve los servos: a mano (órdenes h/c) o con un PERFIL repetible.
    3) Envía cada muestra por USB como una línea de texto que empieza con "D,".

  Monitor Serie / Python: 460800 baudios, fin de línea "Nueva línea".
  ¿Por qué 460800 y no 115200? Cada línea tiene ~115 caracteres y se envían 100
  por segundo = 11 500 caracteres/s. A 115200 baudios caben como máximo ~11 520/s:
  quedaríamos al límite y se perderían muestras.

  Órdenes (separables por comas):
    h 90, c 120   -> mover servos a mano (solo si no hay un perfil corriendo)
    s 1 / s 0     -> empezar / dejar de transmitir muestras
    p 1           -> perfil 1: escalones   (3 s reposo + 20 s + 3 s reposo)
    p 2           -> perfil 2: seno lento   (3 s reposo + 20 s + 3 s reposo)
    p 3           -> perfil 3: seno rápido  (3 s reposo + 10 s + 3 s reposo)
    x             -> parar todo (perfil y transmisión)
    ?             -> imprimir la configuración

  Formato de cada muestra (columnas en datos/DICCIONARIO.md):
    D,seq,t1_us,t2_us,perfil,fase,cmd_h,cmd_c,ax1,ay1,az1,gx1,gy1,gz1,ax2,ay2,az2,gx2,gy2,gz2
  Las líneas que empiezan con "#" son mensajes informativos, no datos.

  Librería necesaria: "ESP32Servo" de Kevin Harrington.
*/
#include <Wire.h>
#include <ESP32Servo.h>

const char *VERSION = "adquisicion-1.0";

// ---------- Pines (ver docs/02_conexiones.md) ----------
const int PIN_SERVO_HOMBRO = 25;
const int PIN_SERVO_CODO   = 26;
const int PIN_SDA = 21;
const int PIN_SCL = 22;

// ---------- Muestreo ----------
const uint32_t BAUDIOS    = 460800;
const uint32_t PERIODO_US = 10000;   // 10 ms -> 100 Hz

// ---------- IMU ----------
const uint8_t IMU1 = 0x68;  // eslabón 1 (AD0 a GND)
const uint8_t IMU2 = 0x69;  // eslabón 2 (AD0 a 3.3 V)
const uint8_t REG_SMPLRT_DIV   = 0x19;
const uint8_t REG_CONFIG       = 0x1A;
const uint8_t REG_GYRO_CONFIG  = 0x1B;
const uint8_t REG_ACCEL_CONFIG = 0x1C;
const uint8_t REG_ACCEL_XOUT_H = 0x3B;
const uint8_t REG_PWR_MGMT_1   = 0x6B;
const uint8_t REG_WHO_AM_I     = 0x75;

// ---------- Servos ----------
const int PULSO_MIN_US = 500;
const int PULSO_MAX_US = 2500;
Servo servoHombro, servoCodo;

// ---------- Estado ----------
bool transmitiendo = false;
int perfil = 0;          // 0 = control manual
int fase = -1;           // -1 manual, 0 reposo inicial, 1 movimiento, 2 reposo final
uint32_t t0Perfil = 0;
int cmdH = 90, cmdC = 90;
uint32_t seq = 0;
uint32_t proximo = 0;
bool imu1Ok = false, imu2Ok = false;
String entrada = "";

// =====================================================================
// IMU
// =====================================================================
void escribirRegistro(uint8_t dir, uint8_t reg, uint8_t valor) {
  Wire.beginTransmission(dir);
  Wire.write(reg);
  Wire.write(valor);
  Wire.endTransmission();
}

uint8_t leerRegistro(uint8_t dir, uint8_t reg) {
  Wire.beginTransmission(dir);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(dir, (uint8_t)1);
  return Wire.available() ? Wire.read() : 0xFF;
}

bool iniciarIMU(uint8_t dir) {
  if (leerRegistro(dir, REG_WHO_AM_I) != 0x68) return false;
  escribirRegistro(dir, REG_PWR_MGMT_1, 0x01);   // despertar, reloj = PLL del giro X
  escribirRegistro(dir, REG_SMPLRT_DIV, 9);      // 1 kHz / (1 + 9) = 100 Hz internos
  escribirRegistro(dir, REG_CONFIG, 0x03);       // DLPF ~44 Hz: antialias para fs = 100 Hz
  escribirRegistro(dir, REG_GYRO_CONFIG, 0x08);  // ±500 °/s -> 65.5 cuentas por °/s
  escribirRegistro(dir, REG_ACCEL_CONFIG, 0x00); // ±2 g     -> 16384 cuentas por g
  return true;
}

// Lee ax ay az temp gx gy gz (14 bytes). Devuelve aceleración y giro en cuentas.
bool leerIMU(uint8_t dir, int16_t acc[3], int16_t gyro[3]) {
  Wire.beginTransmission(dir);
  Wire.write(REG_ACCEL_XOUT_H);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(dir, (uint8_t)14) != 14) return false;
  int16_t crudo[7];
  for (int i = 0; i < 7; i++) {
    uint8_t alto = Wire.read();
    uint8_t bajo = Wire.read();
    crudo[i] = (int16_t)((alto << 8) | bajo);
  }
  for (int i = 0; i < 3; i++) {
    acc[i]  = crudo[i];
    gyro[i] = crudo[i + 4];   // crudo[3] es la temperatura
  }
  return true;
}

// =====================================================================
// Perfiles repetibles: la consigna depende SOLO del tiempo, así cada
// repetición es idéntica (es lo que permite separar ajuste y validación).
// =====================================================================
const float REPOSO_S = 3.0;
const int ESCALONES[10][2] = {   // {hombro, codo}, 2 s cada uno
  {90, 90}, {60, 90}, {120, 90}, {60, 90},   // 8 s solo hombro
  {90, 90}, {90, 60}, {90, 120}, {90, 60},   // solo codo
  {60, 120}, {90, 90}                        // ambos
};

float duracionMovimiento(int p) {
  if (p == 1) return 20.0;
  if (p == 2) return 20.0;
  if (p == 3) return 10.0;
  return 0.0;
}

// Calcula la consigna del perfil p en el instante t [s]. Devuelve false al terminar.
bool consignaPerfil(int p, float t, int &h, int &c, int &f) {
  float dur = duracionMovimiento(p);
  if (t < REPOSO_S) { h = 90; c = 90; f = 0; return true; }
  if (t >= 2 * REPOSO_S + dur) return false;
  if (t >= REPOSO_S + dur) { h = 90; c = 90; f = 2; return true; }

  float tau = t - REPOSO_S;   // tiempo dentro del movimiento
  f = 1;
  if (p == 1) {
    int i = constrain((int)(tau / 2.0), 0, 9);
    h = ESCALONES[i][0];
    c = ESCALONES[i][1];
  } else if (p == 2) {        // seno lento: 0.2 Hz y 0.3 Hz, ±30°
    h = lroundf(90 + 30 * sinf(2 * PI * 0.2 * tau));
    c = lroundf(90 + 30 * sinf(2 * PI * 0.3 * tau));
  } else if (p == 3) {        // seno rápido: 0.6 Hz y 0.9 Hz, ±25°
    h = lroundf(90 + 25 * sinf(2 * PI * 0.6 * tau));
    c = lroundf(90 + 25 * sinf(2 * PI * 0.9 * tau));
  }
  return true;
}

// =====================================================================
// Órdenes
// =====================================================================
void imprimirConfiguracion() {
  Serial.printf("# cfg version=%s fs_hz=100 periodo_us=%lu baudios=%lu gyro_lsb_dps=65.5 "
                "acc_lsb_g=16384 dlpf_hz=44 imu1=0x68 imu2=0x69 imu1_ok=%d imu2_ok=%d "
                "pulso_us=%d-%d\n",
                VERSION, (unsigned long)PERIODO_US, (unsigned long)BAUDIOS,
                imu1Ok, imu2Ok, PULSO_MIN_US, PULSO_MAX_US);
}

void moverServos(int h, int c) {
  h = constrain(h, 0, 180);
  c = constrain(c, 0, 180);
  if (h != cmdH) { servoHombro.write(h); cmdH = h; }
  if (c != cmdC) { servoCodo.write(c);   cmdC = c; }
}

void procesarOrden(String orden) {
  orden.trim();
  if (orden.length() == 0) return;
  char cual = orden.charAt(0);
  int valor = orden.substring(1).toInt();

  if (cual == '?') { imprimirConfiguracion(); return; }
  if (cual == 'x') {
    perfil = 0; fase = -1; transmitiendo = false;
    Serial.println("# parado");
    return;
  }
  if (cual == 's') {
    transmitiendo = (valor != 0);
    Serial.printf("# transmision=%d\n", transmitiendo);
    return;
  }
  if (cual == 'p') {
    if (duracionMovimiento(valor) <= 0) { Serial.println("# perfil_invalido"); return; }
    perfil = valor;
    t0Perfil = micros();
    transmitiendo = true;
    Serial.printf("# perfil=%d\n", perfil);
    return;
  }
  if (cual == 'h' || cual == 'c') {
    if (perfil != 0) { Serial.println("# ocupado_perfil"); return; }
    if (cual == 'h') moverServos(valor, cmdC);
    else             moverServos(cmdH, valor);
    return;
  }
  Serial.println("# orden_desconocida");
}

// Lee el puerto SIN bloquear: junta caracteres hasta '\n'. (readStringUntil
// podría quedarse esperando y romper el ritmo de 100 Hz.)
void leerOrdenes() {
  while (Serial.available()) {
    char ch = (char)Serial.read();
    if (ch == '\n') {
      int inicio = 0;
      while (true) {
        int coma = entrada.indexOf(',', inicio);
        if (coma == -1) { procesarOrden(entrada.substring(inicio)); break; }
        procesarOrden(entrada.substring(inicio, coma));
        inicio = coma + 1;
      }
      entrada = "";
    } else if (entrada.length() < 64) {
      entrada += ch;
    }
  }
}

// =====================================================================
// Una muestra
// =====================================================================
void tomarMuestra() {
  if (perfil != 0) {
    float t = (micros() - t0Perfil) / 1e6;
    int h, c, f;
    if (!consignaPerfil(perfil, t, h, c, f)) {
      perfil = 0; fase = -1; transmitiendo = false;
      Serial.println("# fin_perfil");
      return;
    }
    fase = f;
    moverServos(h, c);
  }
  if (!transmitiendo) return;

  int16_t a1[3], g1[3], a2[3], g2[3];
  uint32_t t1 = micros();
  bool ok1 = leerIMU(IMU1, a1, g1);
  uint32_t t2 = micros();
  bool ok2 = leerIMU(IMU2, a2, g2);
  uint32_t n = seq++;
  if (!ok1 || !ok2) {          // se salta la muestra: Python verá el hueco en seq
    Serial.printf("# error_i2c seq=%lu imu1=%d imu2=%d\n", (unsigned long)n, ok1, ok2);
    return;
  }

  char linea[200];
  snprintf(linea, sizeof(linea),
           "D,%lu,%lu,%lu,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
           (unsigned long)n, (unsigned long)t1, (unsigned long)t2, perfil, fase, cmdH, cmdC,
           a1[0], a1[1], a1[2], g1[0], g1[1], g1[2],
           a2[0], a2[1], a2[2], g2[0], g2[1], g2[2]);
  Serial.print(linea);
}

void setup() {
  Serial.setTxBufferSize(2048);   // cola de salida grande: escribir no frena el muestreo
  Serial.begin(BAUDIOS);
  delay(300);

  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);
  imu1Ok = iniciarIMU(IMU1);
  imu2Ok = iniciarIMU(IMU2);

  servoHombro.setPeriodHertz(50);
  servoCodo.setPeriodHertz(50);
  servoHombro.attach(PIN_SERVO_HOMBRO, PULSO_MIN_US, PULSO_MAX_US);
  servoCodo.attach(PIN_SERVO_CODO, PULSO_MIN_US, PULSO_MAX_US);
  servoHombro.write(cmdH);
  servoCodo.write(cmdC);

  imprimirConfiguracion();
  proximo = micros() + PERIODO_US;
}

void loop() {
  leerOrdenes();
  // Muestreo a ritmo fijo: no "esperar 10 ms" (se acumularía el error), sino
  // programar la siguiente muestra exactamente 10 ms después de la anterior.
  if ((int32_t)(micros() - proximo) >= 0) {
    proximo += PERIODO_US;
    if ((int32_t)(micros() - proximo) > (int32_t)(5 * PERIODO_US)) {
      proximo = micros() + PERIODO_US;   // nos atrasamos mucho: resincronizar
    }
    tomarMuestra();
  }
}
