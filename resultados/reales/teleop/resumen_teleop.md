# Teleoperación con cámara: crudo vs Kalman

Se generó con `python python/analisis_teleop.py`. Las dos columnas salen de los MISMOS cuadros de video (mismas condiciones); solo cambia el método.

## sesion_01 (robot movido con: kalman)

- Duración 73.7 s, 1102 cuadros, **14.9 fps** (Δt = 66.9 ± 80.4 ms, máx 782 ms).
- La cámara vio los 3 marcadores en el **83.5 %** de los cuadros; 34 oclusiones, la más larga de 1863 ms; en el 16.5 % de los cuadros solo se vio θ1 (muñeca tapada: Kalman actualizó solo θ1 y predijo θ2).

| Métrica | Crudo (cámara) | Kalman |
|---|---|---|
| Aspereza θ1 [°] (RMS 2.ª diferencia, mismos cuadros) | 1.436 | 1.184 |
| Aspereza θ2 [°] | 2.945 | 2.069 |
| Órdenes al servo por segundo | 4.8 | 5.8 |
| Cambios de dirección/s del servo hombro | 0.7 | 0.8 |
| Cambios de dirección/s del servo codo | 0.7 | 0.8 |
| Retraso respecto a crudo θ1 / θ2 [ms] | 0 | 5 / 5 |

- Cómputo por cuadro: Kalman **260 µs** (p95 427 µs); detección + Kalman **6.4 ms** (p95 13.7 ms) = 10 % del tiempo entre cuadros.
- Robot (giroscopios de la E1): retraso orden → robot **200 ms** (hombro) / 170 ms (codo); cámara → robot **210 ms** / 205 ms. Vibración del robot: 3.26 / 8.83 °/s.

## sesion_02 (robot movido con: sin robot)

- Duración 7.4 s, 96 cuadros, **12.9 fps** (Δt = 77.5 ± 69.0 ms, máx 382 ms).
- La cámara vio los 3 marcadores en el **100.0 %** de los cuadros; 0 oclusiones, la más larga de 0 ms.

| Métrica | Crudo (cámara) | Kalman |
|---|---|---|
| Aspereza θ1 [°] (RMS 2.ª diferencia, mismos cuadros) | 0.163 | 0.132 |
| Aspereza θ2 [°] | 1.447 | 0.954 |
| Órdenes al servo por segundo | 4.2 | 4.2 |
| Cambios de dirección/s del servo hombro | 0.5 | 0.5 |
| Cambios de dirección/s del servo codo | 0.7 | 0.7 |
| Retraso respecto a crudo θ1 / θ2 [ms] | 0 | 5 / 5 |

- Cómputo por cuadro: Kalman **297 µs** (p95 534 µs); detección + Kalman **6.8 ms** (p95 12.0 ms) = 9 % del tiempo entre cuadros.

## sesion_03 (robot movido con: crudo)

- Duración 43.5 s, 495 cuadros, **11.3 fps** (Δt = 88.1 ± 139.7 ms, máx 2174 ms).
- La cámara vio los 3 marcadores en el **94.3 %** de los cuadros; 2 oclusiones, la más larga de 2996 ms; en el 5.7 % de los cuadros solo se vio θ1 (muñeca tapada: Kalman actualizó solo θ1 y predijo θ2).

| Métrica | Crudo (cámara) | Kalman |
|---|---|---|
| Aspereza θ1 [°] (RMS 2.ª diferencia, mismos cuadros) | 0.864 | 0.670 |
| Aspereza θ2 [°] | 2.204 | 1.654 |
| Órdenes al servo por segundo | 3.4 | 3.6 |
| Cambios de dirección/s del servo hombro | 0.3 | 0.3 |
| Cambios de dirección/s del servo codo | 0.3 | 0.3 |
| Retraso respecto a crudo θ1 / θ2 [ms] | 0 | 5 / 5 |

- Cómputo por cuadro: Kalman **269 µs** (p95 433 µs); detección + Kalman **6.6 ms** (p95 11.9 ms) = 7 % del tiempo entre cuadros.
- Robot (giroscopios de la E1): retraso orden → robot **335 ms** (hombro) / 180 ms (codo); cámara → robot **430 ms** / 235 ms. Vibración del robot: 1.88 / 6.46 °/s.

## sesion_04 (robot movido con: kalman)

- Duración 38.1 s, 523 cuadros, **13.7 fps** (Δt = 72.9 ± 132.7 ms, máx 2298 ms).
- La cámara vio los 3 marcadores en el **96.0 %** de los cuadros; 3 oclusiones, la más larga de 705 ms; en el 4.0 % de los cuadros solo se vio θ1 (muñeca tapada: Kalman actualizó solo θ1 y predijo θ2).

| Métrica | Crudo (cámara) | Kalman |
|---|---|---|
| Aspereza θ1 [°] (RMS 2.ª diferencia, mismos cuadros) | 0.987 | 0.723 |
| Aspereza θ2 [°] | 2.822 | 2.088 |
| Órdenes al servo por segundo | 4.3 | 4.9 |
| Cambios de dirección/s del servo hombro | 0.8 | 0.9 |
| Cambios de dirección/s del servo codo | 0.6 | 0.6 |
| Retraso respecto a crudo θ1 / θ2 [ms] | 0 | 10 / 10 |

- Cómputo por cuadro: Kalman **262 µs** (p95 420 µs); detección + Kalman **6.4 ms** (p95 11.3 ms) = 9 % del tiempo entre cuadros.
- Robot (giroscopios de la E1): retraso orden → robot **0 ms** (hombro) / 165 ms (codo); cámara → robot **0 ms** / 200 ms. Vibración del robot: 0.00 / 7.77 °/s.

## Contraste en el robot: teleoperar con crudo vs con Kalman

| Robot movido con | Vibración hombro [°/s] | Vibración codo [°/s] |
|---|---|---|
| crudo | 1.88 | 6.46 |
| kalman | 1.63 | 8.30 |

## Las 3 configuraciones de Q

Ver `configuraciones_q_camara.md`: menor f_n = más suave (menos ruido y temblor) pero más retraso. Q_media (f_n = 3 Hz) deja pasar el movimiento voluntario (< 2 Hz) con < 16 ms de retraso y reduce el temblor de 8 Hz a la mitad.

## Cómo leerlo

- **Aspereza**: si el ángulo cambiara a velocidad constante daría 0. El temblor de la detección la sube. Menor = más suave.
- **Cambios de dirección/s**: cada uno es el servo yendo y viniendo: eso es el temblor que se ve y se oye en el robot.
- **Retraso**: el precio de suavizar (Q más baja = más suave y más tarde). Es pequeño porque el modelo de velocidad casi constante sigue las rampas sin retraso: solo se atrasa cuando la velocidad cambia.
- **Oclusión**: la cámara cruda se queda congelada; Kalman sigue con su modelo de velocidad casi constante (sirve para huecos cortos; en huecos largos la predicción se aleja).
- **Límite**: la latencia teléfono → PC (WiFi) no se puede medir con estos datos; el retraso cámara → robot cuenta desde que el cuadro LLEGA al PC.
