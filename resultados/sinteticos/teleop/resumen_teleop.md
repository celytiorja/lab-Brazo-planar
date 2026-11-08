# Teleoperación con cámara: crudo vs Kalman

Se generó con `python python/analisis_teleop.py`. Las dos columnas salen de los MISMOS cuadros de video (mismas condiciones); solo cambia el método.

> ⚠️ DATOS SINTÉTICOS: video generado por código para probar el análisis. No son mediciones.

## sesion_01 (robot movido con: crudo)

- Duración 30.0 s, 900 cuadros, **30.0 fps** (Δt = 33.3 ± 5.6 ms, máx 50 ms).
- La cámara vio los 3 marcadores en el **92.6 %** de los cuadros; 3 oclusiones, la más larga de 1263 ms; en el 7.4 % de los cuadros solo se vio θ1 (muñeca tapada: Kalman actualizó solo θ1 y predijo θ2).

| Métrica | Crudo (cámara) | Kalman |
|---|---|---|
| Aspereza θ1 [°] (RMS 2.ª diferencia, mismos cuadros) | 0.810 | 0.501 |
| Aspereza θ2 [°] | 1.882 | 0.931 |
| Órdenes al servo por segundo | 14.6 | 15.6 |
| Cambios de dirección/s del servo hombro | 1.1 | 0.9 |
| Cambios de dirección/s del servo codo | 1.1 | 1.0 |
| Retraso respecto a crudo θ1 / θ2 [ms] | 0 | 0 / 5 |
| Error RMS vs verdad (cuadros vistos) θ1 / θ2 [°] (sintético) | 0.33 / 1.22 | 0.38 / 1.37 |
| Error RMS en oclusiones θ1 / θ2 [°] (sintético) | 19.08 / 14.73 | 0.24 / 12.81 |

- Cómputo por cuadro: Kalman **240 µs** (p95 313 µs); detección + Kalman **2.9 ms** (p95 3.8 ms) = 9 % del tiempo entre cuadros.
- Robot (giroscopios de la E1): retraso orden → robot **175 ms** (hombro) / 170 ms (codo); cámara → robot **210 ms** / 210 ms. Vibración del robot: 12.12 / 15.29 °/s.

## sesion_02 (robot movido con: kalman)

- Duración 30.0 s, 900 cuadros, **30.0 fps** (Δt = 33.3 ± 5.6 ms, máx 50 ms).
- La cámara vio los 3 marcadores en el **92.6 %** de los cuadros; 3 oclusiones, la más larga de 1263 ms; en el 7.4 % de los cuadros solo se vio θ1 (muñeca tapada: Kalman actualizó solo θ1 y predijo θ2).

| Métrica | Crudo (cámara) | Kalman |
|---|---|---|
| Aspereza θ1 [°] (RMS 2.ª diferencia, mismos cuadros) | 0.810 | 0.501 |
| Aspereza θ2 [°] | 1.882 | 0.931 |
| Órdenes al servo por segundo | 14.6 | 15.6 |
| Cambios de dirección/s del servo hombro | 1.1 | 0.9 |
| Cambios de dirección/s del servo codo | 1.1 | 1.0 |
| Retraso respecto a crudo θ1 / θ2 [ms] | 0 | 0 / 5 |
| Error RMS vs verdad (cuadros vistos) θ1 / θ2 [°] (sintético) | 0.33 / 1.22 | 0.38 / 1.37 |
| Error RMS en oclusiones θ1 / θ2 [°] (sintético) | 19.08 / 14.73 | 0.24 / 12.81 |

- Cómputo por cuadro: Kalman **184 µs** (p95 265 µs); detección + Kalman **2.7 ms** (p95 3.5 ms) = 8 % del tiempo entre cuadros.
- Robot (giroscopios de la E1): retraso orden → robot **180 ms** (hombro) / 170 ms (codo); cámara → robot **210 ms** / 215 ms. Vibración del robot: 9.50 / 15.65 °/s.

## Contraste en el robot: teleoperar con crudo vs con Kalman

| Robot movido con | Vibración hombro [°/s] | Vibración codo [°/s] |
|---|---|---|
| crudo | 12.12 | 15.29 |
| kalman | 9.50 | 15.65 |

## Las 3 configuraciones de Q

Ver `configuraciones_q_camara.md`: menor f_n = más suave (menos ruido y temblor) pero más retraso. Q_media (f_n = 3 Hz) deja pasar el movimiento voluntario (< 2 Hz) con < 16 ms de retraso y reduce el temblor de 8 Hz a la mitad.

## Cómo leerlo

- **Aspereza**: si el ángulo cambiara a velocidad constante daría 0. El temblor de la detección la sube. Menor = más suave.
- **Cambios de dirección/s**: cada uno es el servo yendo y viniendo: eso es el temblor que se ve y se oye en el robot.
- **Retraso**: el precio de suavizar (Q más baja = más suave y más tarde). Es pequeño porque el modelo de velocidad casi constante sigue las rampas sin retraso: solo se atrasa cuando la velocidad cambia.
- **Oclusión**: la cámara cruda se queda congelada; Kalman sigue con su modelo de velocidad casi constante (sirve para huecos cortos; en huecos largos la predicción se aleja).
- **Límite**: la latencia teléfono → PC (WiFi) no se puede medir con estos datos; el retraso cámara → robot cuenta desde que el cuadro LLEGA al PC.
