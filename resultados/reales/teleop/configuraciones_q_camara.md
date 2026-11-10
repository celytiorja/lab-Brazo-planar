# Kalman de la cámara: las 3 configuraciones de Q

| Q | f_n [Hz] | factor de ruido | ganancia 1 Hz | retraso 1 Hz [ms] | ganancia 2 Hz | retraso 2 Hz [ms] | ganancia 8 Hz (temblor) | razon |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q_baja | 1.5 | 0.53 | 1.2 | 37.8 | 0.97 | 57.7 | 0.27 | muy suave: ruido x0.53, temblor 8 Hz x0.27; retraso ~40-60 ms a 1-2 Hz |
| Q_media | 3 | 0.7 | 1.06 | 5.1 | 1.15 | 15.9 | 0.49 | equilibrio: ruido x0.70, temblor 8 Hz x0.49; retraso < 16 ms hasta 2 Hz |
| Q_alta | 6 | 0.86 | 1.01 | 0.5 | 1.04 | 1.8 | 0.83 | casi sin retraso (< 3 ms a 2 Hz); filtra poco: ruido x0.86 |

Simulación del filtro real a 30 cuadros/s (kalman_camara.caracterizar_q). q = r·Δt·(2π f_n)⁴: como q es proporcional a r, este comportamiento NO depende de la R medida. Factor de ruido = desviación de la salida / de la entrada. Movimiento voluntario < 2 Hz; temblor fisiológico ~8–12 Hz.
