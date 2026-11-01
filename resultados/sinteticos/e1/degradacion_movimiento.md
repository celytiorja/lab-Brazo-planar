# Ruido en reposo vs en movimiento

| archivo | eslabon | ruido_aparente_reposo_dps | ruido_aparente_movimiento_dps | cociente_mov_reposo |
| --- | --- | --- | --- | --- |
| escalones_01 | 1 | 0.0523 | 12.57 | 240.3 |
| escalones_01 | 2 | 0.04772 | 13.6 | 285.1 |
| seno_lento_01 | 1 | 0.08768 | 4.211 | 48.02 |
| seno_lento_01 | 2 | 0.1635 | 5.891 | 36.03 |
| seno_rapido_01 | 1 | 0.1723 | 3.851 | 22.35 |
| seno_rapido_01 | 2 | 0.3724 | 5.45 | 14.64 |

Residuo de alta frecuencia: w − Savitzky–Golay (ventana 11, orden 3). Un cociente > 1 indica que la R medida en reposo SUBESTIMA el ruido real durante el movimiento. En 'escalones' el residuo incluye los arranques bruscos.
