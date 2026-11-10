/*
  ADQUISICIÓN — Brazo planar 2 GDL (Entregas 1 y 2)
  =================================================
  Hace tres cosas a la vez:
    1) Lee las dos MPU-6050 a un ritmo FIJO de 100 muestras por segundo
       (giroscopio + acelerómetro, valores CRUDOS en cuentas).
    2) Mueve los servos: a mano (órdenes h/c) o con un PERFIL repetible.
    3) Envía cada muestra por USB como una línea de texto que empieza con "D,".

  ¿Por qué DOS TAREAS? (v1.1) El ESP32 tiene dos núcleos. En la v1.0 todo iba en
  loop() y se descubrió con datos reales que servo.write() BLOQUEA ~15 ms si se
  llama antes de que termine el pulso anterior (20 ms): en los perfiles seno el
  muestreo bajaba a ~55 Hz con Δt de hasta 40 ms. Ahora:
    - Núcleo 0, tarea "muestreo": SOLO lee las IMU cada 10 ms exactos
      (vTaskDelayUntil) y deja cada muestra en una cola.
    - Núcleo 1, loop(): órdenes, perfiles, servos (máx. 1 escritura cada 20 ms)
      y envío por USB de lo que haya en la cola.
  Así, aunque un servo se bloquee, la medición no se entera.

  v1.2: con la v1.1 aún había lecturas I2C de hasta 40 ms en los senos. Causa:
  Wire.begin() instala la interrupción del I2C en el núcleo DONDE SE LLAMA, y se
  llamaba en setup() (núcleo 1, el de los servos). Si ese núcleo se bloqueaba,
  nadie atendía al I2C. Ahora el I2C se inicia DENTRO de la tarea de muestreo
  (núcleo 0): toda la cadena de medición vive en su propio núcleo.

  v1.3: funciona también en el ESP32-S3 (que NO tiene los GPIO 22 ni 25): los
  pines se eligen solos según la placa elegida en el IDE, y la línea "# cfg" dice
  la placa y los pines. La medición es idéntica a la v1.2.

  v1.4: lectura I2C ROBUSTA. Con el ESP32-S3 aparecieron "error_i2c" sueltos cuando
  se movían los servos (ruido eléctrico + cables). Antes, un fallo botaba la muestra
  y podía bloquear 50 ms. Ahora: I2C a 100 kHz (más tolerante al ruido), espera
  máxima de 5 ms por lectura, hasta 3 reintentos, y si una IMU falla 5 veces
  seguidas se reinicia el bus y se reconfiguran las IMU ("# i2c_reiniciado").

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

const char *VERSION = "adquisicion-1.4";

// ---------- Pines (ver docs/02_conexiones.md) ----------
// Se eligen SOLOS según la placa que se compila (Herramientas → Placa):
//   ESP32 clásico ("ESP32 Dev Module"):  servos 25 / 26,  I2C SDA 21 / SCL 22.
//   ESP32-S3      ("ESP32S3 Dev Module"): los GPIO 22 y 25 NO EXISTEN en el S3
//                                          -> servos 4 / 5,  I2C SDA 8 / SCL 9.
#if CONFIG_IDF_TARGET_ESP32S3
const char *PLACA = "ESP32-S3";
const int PIN_SERVO_HOMBRO = 4;
const int PIN_SERVO_CODO   = 5;
const int PIN_SDA = 8;
const int PIN_SCL = 9;
#else
const char *PLACA = "ESP32";
const int PIN_SERVO_HOMBRO = 25;
const int PIN_SERVO_CODO   = 26;
const int PIN_SDA = 21;
const int PIN_SCL = 22;
#endif

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

const uint32_t MIN_ENTRE_ESCRITURAS_US = 20000;   // un pulso de servo dura 20 ms

// ---------- Estado compartido entre los dos núcleos ----------
// "volatile": el compilador no debe guardar copias, porque la otra tarea puede
// cambiar el valor en cualquier momento.
volatile bool transmitiendo = false;
volatile int perfil = 0;          // 0 = control manual
volatile int fase = -1;           // -1 manual, 0 reposo inicial, 1 movimiento, 2 reposo final
volatile int cmdH = 90, cmdC = 90; // lo ÚLTIMO que se escribió a cada servo
uint32_t t0Perfil = 0;
bool imu1Ok = false, imu2Ok = false;
volatile bool imusListas = false;   // la tarea de muestreo terminó de iniciar el I2C
String entrada = "";

// Pedido de posición (puede llegar más rápido de lo que conviene escribir al servo).
int pedidoH = 90, pedidoC = 90;
uint32_t ultimaEscrituraH = 0, ultimaEscrituraC = 0;
bool finPerfilPendiente = false;

// ---------- I2C robusto (v1.4) ----------
const uint32_t I2C_HZ = 100000;      // 100 kHz: 2 IMU ≈ 3.5 ms de los 10 ms del periodo
const uint16_t I2C_TIMEOUT_MS = 5;   // una lectura fallida no bloquea más de esto
const int I2C_REINTENTOS = 3;
const int FALLOS_PARA_REINICIAR = 5;
volatile uint32_t reintentosI2C = 0, reiniciosI2C = 0;

// Una muestra viaja del núcleo 0 al núcleo 1 dentro de esta estructura.
struct Muestra {
  uint32_t seq, t1, t2;
  int8_t perfil, fase;
  int16_t cmdH, cmdC;
  int16_t a1[3], g1[3], a2[3], g2[3];
  bool ok1, ok2;
};
QueueHandle_t cola;               // "buzón" entre las dos tareas (64 muestras = 0.64 s)

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

// Igual que leerIMU, pero reintenta; t = instante (µs) del intento que funcionó.
bool leerIMUConReintentos(uint8_t dir, int16_t acc[3], int16_t gyro[3], uint32_t &t) {
  for (int i = 0; i < I2C_REINTENTOS; i++) {
    t = micros();
    if (leerIMU(dir, acc, gyro)) return true;
    reintentosI2C++;
  }
  return false;
}

void iniciarBusI2C() {
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(I2C_HZ);
  Wire.setTimeOut(I2C_TIMEOUT_MS);
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
                "pulso_us=%d-%d placa=%s servo_pines=%d/%d i2c_sda_scl=%d/%d i2c_hz=%lu "
                "reintentos_i2c=%lu reinicios_i2c=%lu\n",
                VERSION, (unsigned long)PERIODO_US, (unsigned long)BAUDIOS,
                imu1Ok, imu2Ok, PULSO_MIN_US, PULSO_MAX_US,
                PLACA, PIN_SERVO_HOMBRO, PIN_SERVO_CODO, PIN_SDA, PIN_SCL,
                (unsigned long)I2C_HZ, (unsigned long)reintentosI2C, (unsigned long)reiniciosI2C);
}

// Solo ANOTA el pedido; actualizarServos() lo aplica sin escribir más de una vez
// cada 20 ms por servo (más rápido no sirve: el servo recibe un pulso cada 20 ms).
void moverServos(int h, int c) {
  pedidoH = constrain(h, 0, 180);
  pedidoC = constrain(c, 0, 180);
}

void actualizarServos() {
  uint32_t ahora = micros();
  if (pedidoH != cmdH && ahora - ultimaEscrituraH >= MIN_ENTRE_ESCRITURAS_US) {
    servoHombro.write(pedidoH);
    cmdH = pedidoH;
    ultimaEscrituraH = ahora;
  }
  if (pedidoC != cmdC && ahora - ultimaEscrituraC >= MIN_ENTRE_ESCRITURAS_US) {
    servoCodo.write(pedidoC);
    cmdC = pedidoC;
    ultimaEscrituraC = ahora;
  }
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
    t0Perfil = micros();
    fase = 0;                     // antes que "perfil": ninguna muestra sale con fase −1
    perfil = valor;
    transmitiendo = true;
    Serial.printf("# perfil=%d\n", perfil);
    return;
  }
  if (cual == 'h' || cual == 'c') {
    if (perfil != 0) { Serial.println("# ocupado_perfil"); return; }
    if (cual == 'h') moverServos(valor, pedidoC);
    else             moverServos(pedidoH, valor);
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
// NÚCLEO 0: tarea de muestreo (solo IMU, ritmo exacto)
// =====================================================================
void tareaMuestreo(void *) {
  // El I2C se inicia AQUÍ (núcleo 0) para que su interrupción quede en este núcleo.
  iniciarBusI2C();
  imu1Ok = iniciarIMU(IMU1);
  imu2Ok = iniciarIMU(IMU2);
  imusListas = true;

  uint32_t seq = 0;
  int fallosSeguidos = 0;
  TickType_t ultimo = xTaskGetTickCount();
  for (;;) {
    // Espera HASTA el próximo múltiplo de 10 ms (no "10 ms desde ahora"):
    // así los retrasos no se acumulan.
    vTaskDelayUntil(&ultimo, pdMS_TO_TICKS(PERIODO_US / 1000));
    if (!transmitiendo) continue;

    Muestra m;
    m.ok1 = leerIMUConReintentos(IMU1, m.a1, m.g1, m.t1);
    m.ok2 = leerIMUConReintentos(IMU2, m.a2, m.g2, m.t2);
    if (m.ok1 && m.ok2) {
      fallosSeguidos = 0;
    } else if (++fallosSeguidos >= FALLOS_PARA_REINICIAR) {
      // El bus quedó "pegado" o una IMU se reinició (pico de corriente): empezar de nuevo.
      Wire.end();
      iniciarBusI2C();
      iniciarIMU(IMU1);
      iniciarIMU(IMU2);
      reiniciosI2C++;
      fallosSeguidos = 0;
    }
    m.seq = seq++;
    m.perfil = perfil;
    m.fase = fase;
    m.cmdH = cmdH;
    m.cmdC = cmdC;
    // Si la cola está llena (el USB no da abasto) la muestra se pierde:
    // Python lo verá como un hueco en "seq".
    xQueueSend(cola, &m, 0);
  }
}

// =====================================================================
// NÚCLEO 1: perfiles, servos y envío por USB
// =====================================================================
void actualizarPerfil() {
  if (perfil == 0) return;
  float t = (micros() - t0Perfil) / 1e6;
  int h, c, f;
  if (!consignaPerfil(perfil, t, h, c, f)) {
    perfil = 0; fase = -1; transmitiendo = false;
    finPerfilPendiente = true;    // se avisa cuando ya se enviaron todas sus muestras
    return;
  }
  fase = f;
  moverServos(h, c);
}

void enviarMuestras() {
  static uint32_t reiniciosAvisados = 0;
  if (reiniciosI2C != reiniciosAvisados) {
    reiniciosAvisados = reiniciosI2C;
    Serial.printf("# i2c_reiniciado veces=%lu\n", (unsigned long)reiniciosAvisados);
  }
  Muestra m;
  while (xQueueReceive(cola, &m, 0) == pdTRUE) {
    if (!m.ok1 || !m.ok2) {
      Serial.printf("# error_i2c seq=%lu imu1=%d imu2=%d\n", (unsigned long)m.seq, m.ok1, m.ok2);
      continue;
    }
    char linea[200];
    snprintf(linea, sizeof(linea),
             "D,%lu,%lu,%lu,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
             (unsigned long)m.seq, (unsigned long)m.t1, (unsigned long)m.t2,
             m.perfil, m.fase, m.cmdH, m.cmdC,
             m.a1[0], m.a1[1], m.a1[2], m.g1[0], m.g1[1], m.g1[2],
             m.a2[0], m.a2[1], m.a2[2], m.g2[0], m.g2[1], m.g2[2]);
    Serial.print(linea);
  }
  if (finPerfilPendiente && uxQueueMessagesWaiting(cola) == 0) {
    finPerfilPendiente = false;
    Serial.println("# fin_perfil");
  }
}

void setup() {
  Serial.setTxBufferSize(2048);   // cola de salida grande: escribir no frena el programa
  Serial.begin(BAUDIOS);
  delay(300);

  servoHombro.setPeriodHertz(50);
  servoCodo.setPeriodHertz(50);
  servoHombro.attach(PIN_SERVO_HOMBRO, PULSO_MIN_US, PULSO_MAX_US);
  servoCodo.attach(PIN_SERVO_CODO, PULSO_MIN_US, PULSO_MAX_US);
  servoHombro.write(cmdH);
  servoCodo.write(cmdC);

  // El bus I2C lo inicia y lo usa SOLO la tarea de muestreo (núcleo 0).
  cola = xQueueCreate(64, sizeof(Muestra));
  xTaskCreatePinnedToCore(tareaMuestreo, "muestreo", 4096, NULL,
                          3,     // prioridad alta: que nada la interrumpa
                          NULL,
                          0);    // núcleo 0 (loop() corre en el núcleo 1)
  while (!imusListas) delay(5);   // esperar a que la tarea inicie las IMU
  imprimirConfiguracion();
}

void loop() {
  leerOrdenes();
  actualizarPerfil();
  actualizarServos();
  enviarMuestras();
  delay(1);                       // cede el procesador un instante
}
