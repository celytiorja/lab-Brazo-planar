/*
  PRUEBA DE SERVOS — Brazo planar 2 GDL (sin IMU)
  ===============================================
  Mueve los dos MG996R con órdenes escritas en el Monitor Serie.

  Monitor Serie: 115200 baudios, fin de línea "Nueva línea".
    h 90   -> servo del HOMBRO a 90°
    c 45   -> servo del CODO a 45°
    b      -> barrido lento 0° -> 180° -> 90° del hombro y luego del codo
    h 45, c 120  -> varias órdenes en una línea, separadas por comas

  Librería necesaria: "ESP32Servo" de Kevin Harrington.

  ¿Cómo entiende un servo el ángulo?
  Recibe un pulso 50 veces por segundo (cada 20 ms). El ANCHO del pulso es la
  orden:  ~0.5 ms -> 0°,  ~1.5 ms -> 90°,  ~2.5 ms -> 180°.
  El servo tiene dentro un motor, engranajes, un potenciómetro que mide dónde
  está y un pequeño control que mueve el motor hasta que la posición medida
  coincide con la pedida.
*/
#include <ESP32Servo.h>

// ---------- Pines (ver docs/02_conexiones.md) ----------
const int PIN_SERVO_HOMBRO = 25;
const int PIN_SERVO_CODO   = 26;

// Ancho de pulso [µs] para 0° y 180°. Si en los extremos el servo zumba o
// choca, acerca estos valores al centro (p. ej. 600 y 2400).
const int PULSO_MIN_US = 500;
const int PULSO_MAX_US = 2500;

Servo servoHombro, servoCodo;

void moverLento(Servo &servo, int desde, int hasta) {
  int paso = (hasta > desde) ? 1 : -1;
  for (int a = desde; a != hasta + paso; a += paso) {
    servo.write(a);
    delay(15);   // 15 ms por grado ≈ 2,7 s para 180°
  }
}

void barrido() {
  Serial.println("Barrido del hombro...");
  moverLento(servoHombro, servoHombro.read(), 0);
  moverLento(servoHombro, 0, 180);
  moverLento(servoHombro, 180, 90);
  Serial.println("Barrido del codo...");
  moverLento(servoCodo, servoCodo.read(), 0);
  moverLento(servoCodo, 0, 180);
  moverLento(servoCodo, 180, 90);
  Serial.println("Listo. Ambos en 90°.");
}

// Una sola orden: "h 45", "h45", "c 120" o "b".
void procesarOrden(String orden) {
  orden.trim();
  if (orden == "b") { barrido(); return; }
  if (orden.length() < 2) {
    Serial.println("Ordenes: 'h <0-180>', 'c <0-180>' o 'b'");
    return;
  }
  char cual = orden.charAt(0);
  // toInt() salta los espacios del inicio y lee dígitos hasta el primer
  // carácter que no sea número; por eso sirven "h 45" y "h45".
  int angulo = constrain(orden.substring(1).toInt(), 0, 180);
  if (cual == 'h') {
    servoHombro.write(angulo);
    Serial.printf("Hombro -> %d°\n", angulo);
  } else if (cual == 'c') {
    servoCodo.write(angulo);
    Serial.printf("Codo -> %d°\n", angulo);
  } else {
    Serial.println("Ordenes: 'h <0-180>', 'c <0-180>' o 'b'");
  }
}

// Una línea puede traer varias órdenes separadas por comas: "h 45, c 90".
// Se recorre la línea cortándola en cada coma y se procesa cada trozo.
void procesarComando(String linea) {
  int inicio = 0;
  while (true) {
    int coma = linea.indexOf(',', inicio);   // -1 si ya no hay más comas
    if (coma == -1) {
      procesarOrden(linea.substring(inicio));
      break;
    }
    procesarOrden(linea.substring(inicio, coma));
    inicio = coma + 1;
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== Prueba de servos ===");

  servoHombro.setPeriodHertz(50);   // un pulso cada 20 ms
  servoCodo.setPeriodHertz(50);
  servoHombro.attach(PIN_SERVO_HOMBRO, PULSO_MIN_US, PULSO_MAX_US);
  servoCodo.attach(PIN_SERVO_CODO, PULSO_MIN_US, PULSO_MAX_US);

  // Arrancar en el centro: es la posición más segura si el brazo ya está montado.
  servoHombro.write(90);
  servoCodo.write(90);
  Serial.println("Servos en 90°. Escribe 'h <ángulo>', 'c <ángulo>' o 'b'.");
}

void loop() {
  if (Serial.available()) procesarComando(Serial.readStringUntil('\n'));
}
