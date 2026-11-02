# Correlación cruzada

| par | tipo | relacion_fisica | retraso_ms | coef_pico |
| --- | --- | --- | --- | --- |
| consigna θ1 → θ1 medido (integración) | físico | el eslabón sigue a la consigna del servo (respuesta mecánica del servo) | 66.65 | 0.9854 |
| consigna θ2 → θ2 medido (integración) | físico | el eslabón sigue a la consigna del servo (respuesta mecánica del servo) | 76.09 | 0.9852 |
| w1 (IMU1) → w2 (IMU2), codo fijo | instrumental | con el codo quieto ω2 = ω1: cualquier retraso es de la adquisición, no del brazo | -0.00898 | 1 |
| lectura IMU1 → IMU2 (timestamps t2 − t1) | instrumental | las IMU se leen una tras otra por I2C | 0.4101 | — |

Retraso positivo = la segunda señal llega después. Pico refinado con parábola (la resolución bruta es 1 muestra = 10 ms). INSTRUMENTAL = lo introduce la adquisición (lectura secuencial de las IMU, cuantización del muestreo); FÍSICO = lo introduce el mecanismo (el servo tarda en seguir la consigna).
