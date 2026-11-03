# Teleoperación con cámara: crudo vs Kalman

Se generó con `python python/analisis_teleop.py`. Las dos columnas salen de los MISMOS cuadros de video (mismas condiciones); solo cambia el método.

> ⚠️ DATOS SINTÉTICOS: video generado por código para probar el análisis. No son mediciones.

## sesion_01 (robot movido con: crudo)

- Duración 30.0 s, 900 cuadros, **30.0 fps** (Δt = 33.3 ± 5.6 ms, máx 50 ms).
- La cámara vio los 3 marcadores en el **92.6 %** de los cuadros; 3 oclusiones, la más larga de 1263 ms.

| Métrica | Crudo (cámara) | Kalman |
|---|---|---|
| Aspereza θ1 [°] (RMS 2.ª diferencia, mismos cuadros) | 0.810 | 0.710 |
| Aspereza θ2 [°] | 1.882 | 1.400 |
| Órdenes al servo por segundo | 14.6 | 15.2 |
| Cambios de dirección/s del servo hombro | 1.1 | 1.1 |
| Cambios de dirección/s del servo codo | 1.1 | 1.0 |
| Retraso respecto a crudo θ1 / θ2 [ms] | 0 | 0 / 0 |
| Error RMS vs verdad (cuadros vistos) θ1 / θ2 [°] (sintético) | 0.33 / 1.22 | 0.30 / 1.23 |
| Error RMS en oclusiones θ1 / θ2 [°] (sintético) | 19.08 / 14.73 | 10.70 / 12.96 |

- Cómputo por cuadro: Kalman **155 µs** (p95 219 µs); detección + Kalman **3.4 ms** (p95 4.4 ms) = 10 % del tiempo entre cuadros.
- Robot (giroscopios de la E1): retraso orden → robot **175 ms** (hombro) / 170 ms (codo); cámara → robot **210 ms** / 210 ms. Vibración del robot: 12.12 / 15.29 °/s.

## sesion_02 (robot movido con: kalman)

- Duración 30.0 s, 900 cuadros, **30.0 fps** (Δt = 33.3 ± 5.6 ms, máx 50 ms).
- La cámara vio los 3 marcadores en el **92.6 %** de los cuadros; 3 oclusiones, la más larga de 1263 ms.

| Métrica | Crudo (cámara) | Kalman |
|---|---|---|
| Aspereza θ1 [°] (RMS 2.ª diferencia, mismos cuadros) | 0.810 | 0.710 |
| Aspereza θ2 [°] | 1.882 | 1.400 |
| Órdenes al servo por segundo | 14.6 | 15.2 |
| Cambios de dirección/s del servo hombro | 1.1 | 1.1 |
| Cambios de dirección/s del servo codo | 1.1 | 1.0 |
| Retraso respecto a crudo θ1 / θ2 [ms] | 0 | 0 / 0 |
| Error RMS vs verdad (cuadros vistos) θ1 / θ2 [°] (sintético) | 0.33 / 1.22 | 0.30 / 1.23 |
| Error RMS en oclusiones θ1 / θ2 [°] (sintético) | 19.08 / 14.73 | 10.70 / 12.96 |

- Cómputo por cuadro: Kalman **141 µs** (p95 186 µs); detección + Kalman **3.3 ms** (p95 4.1 ms) = 10 % del tiempo entre cuadros.
- Robot (giroscopios de la E1): retraso orden → robot **175 ms** (hombro) / 170 ms (codo); cámara → robot **210 ms** / 210 ms. Vibración del robot: 10.76 / 15.89 °/s.

## Contraste en el robot: teleoperar con crudo vs con Kalman

| Robot movido con | Vibración hombro [°/s] | Vibración codo [°/s] |
|---|---|---|
| crudo | 12.12 | 15.29 |
| kalman | 10.76 | 15.89 |

## Cómo leerlo

- **Aspereza**: si el ángulo cambiara a velocidad constante daría 0. El temblor de la detección la sube. Menor = más suave.
- **Cambios de dirección/s**: cada uno es el servo yendo y viniendo: eso es el temblor que se ve y se oye en el robot.
- **Retraso**: el precio de suavizar (Q más baja = más suave y más tarde).
- **Oclusión**: la cámara cruda se queda congelada; Kalman sigue con su modelo de velocidad casi constante (sirve para huecos cortos; en huecos largos la predicción se aleja).
- **Límite**: la latencia teléfono → PC (WiFi) no se puede medir con estos datos; el retraso cámara → robot cuenta desde que el cuadro LLEGA al PC.
