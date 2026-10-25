# Conexiones (ESP32 DevKit + 2× MG996R + 2× MPU-6050)

## Pines elegidos y por qué

| Señal | GPIO ESP32 | Por qué este pin |
|---|---|---|
| Servo hombro (señal) | **GPIO25** (D25) | Salida "limpia": no es pin de arranque (*strapping*) y no emite pulsos al encender. |
| Servo codo (señal) | **GPIO26** (D26) | Igual que el 25 y está justo al lado: cableado ordenado. |
| I2C SDA (ambas IMU) | **GPIO21** (D21) | Es el SDA por defecto de la librería `Wire`. |
| I2C SCL (ambas IMU) | **GPIO22** (D22) | Es el SCL por defecto de `Wire`. |

Pines **a evitar** en el ESP32: 0, 2, 5, 12 y 15 (definen cómo arranca la placa),
6–11 (memoria flash interna) y 34–39 (solo entrada).

## Dos IMU en el mismo bus I2C

I2C es un "bus": varios dispositivos comparten los mismos 2 cables (SDA = datos,
SCL = reloj) y cada uno tiene una **dirección**, como un número de casa. Todas las
MPU-6050 vienen con la dirección 0x68, así que hay que cambiar una:

- **IMU1 (eslabón 1):** AD0 → GND (o sin conectar) → dirección **0x68**
- **IMU2 (eslabón 2):** AD0 → **3.3 V** → dirección **0x69**

## Diagrama

```
                    ┌──────────── ESP32 DevKit ────────────┐
   USB al PC ───────┤ USB (alimenta el ESP32 + datos serie) │
                    │                                       │
                    │ 3V3 ─┬──────── VCC IMU1               │
                    │      ├──────── VCC IMU2               │
                    │      └──────── AD0 IMU2   (→ 0x69)    │
                    │ GND ─┬──────── GND IMU1, AD0 IMU1     │
                    │      ├──────── GND IMU2               │
                    │      └──────── GND fuente 5 V  ◄── ¡TIERRA COMÚN!
                    │ D21 ────────── SDA IMU1 y SDA IMU2    │
                    │ D22 ────────── SCL IMU1 y SCL IMU2    │
                    │ D25 ────────── señal servo HOMBRO (naranja)
                    │ D26 ────────── señal servo CODO   (naranja)
                    └───────────────────────────────────────┘

   Fuente 5 V (+) ──┬── rojo servo HOMBRO ──┬── rojo servo CODO
                    │                       │
                 [+ condensador 1000–2200 µF, ≥10 V]
                    │                       │
   Fuente 5 V (−) ──┴── café servo HOMBRO ──┴── café servo CODO ── GND ESP32
```

Colores típicos del MG996R: **café/marrón = GND**, **rojo = +5 V**, **naranja = señal**.

## ⚠️ Alimentación: lee esto antes de conectar

1. **Nunca alimentes los servos desde el pin 5V/VIN del ESP32.** Un MG996R puede pedir
   hasta ~2,5 A cuando se atasca; el regulador y el USB del ESP32 no aguantan eso y
   la placa se reinicia, o algo se quema.
2. **Tu cargador de 68 W:** si es USB-C con *Power Delivery* (PD), los 68 W solo los da
   a 20 V. **A 5 V normalmente entrega como máximo 3 A (15 W).** Revisa la etiqueta
   (busca "5V⎓3A"). Con 3 A alcanza para dos MG996R moviendo un brazo liviano, pero
   va justo. Para sacar los 5 V necesitas un cable o placa USB → bornes.
3. **Tierra común:** el GND de la fuente de 5 V **tiene** que unirse al GND del ESP32.
   La señal PWM es una diferencia de voltaje respecto a GND; si cada uno tiene su
   propia "referencia", el servo no entiende la señal.
4. **Condensador grande** (1000–2200 µF) entre +5 V y GND, cerca de los servos.
   Cuando un servo arranca pide un pico de corriente; el condensador lo entrega y
   evita que el voltaje caiga y "contamine" al resto del circuito.
5. La IMU se alimenta a **3.3 V** desde el ESP32. El módulo GY-521 trae su propio
   regulador y resistencias pull-up, no hace falta añadir nada.

## Montaje de las IMU

- IMU1 va pegada al **eslabón 1** e IMU2 al **eslabón 2**, lo más planas y firmes posible.
- El giroscopio mide el giro alrededor del eje **perpendicular al plano del brazo**.
  Con el módulo plano sobre el eslabón suele ser el eje **z**, pero **compruébalo**
  con `firmware/prueba_hardware`: gira un eslabón con la mano y mira qué columna
  `g[°/s]` cambia.
- **IMU2 mide el ángulo absoluto** del eslabón 2 respecto al mundo (θ1 + θ2), porque
  viaja encima del eslabón 1. Por eso el ángulo del codo es **θ2 = θ_IMU2 − θ_IMU1**.
- Los cables de las IMU se mueven con el brazo: déjalos con holgura y bien sujetos.
  Un cable de I2C flojo es la causa n.º 1 de que las lecturas "se congelen".
