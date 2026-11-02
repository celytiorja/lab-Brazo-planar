# Variantes de compensación del sesgo

| variante_sesgo | metodo | eslabon | sesgo_usado_dps | deriva_final_deg | error_estacionario_rms_deg |
| --- | --- | --- | --- | --- | --- |
| sin compensar | Integración directa | 1 | 0 | 1.845 | 1.153 |
| sin compensar | Integración directa | 2 | 0 | -6.979 | 5.595 |
| sin compensar | Media móvil N=5 + Euler | 1 | 0 | 1.836 | 1.149 |
| sin compensar | Media móvil N=5 + Euler | 2 | 0 | -6.971 | 5.589 |
| sin compensar | Media móvil N=21 + Euler | 1 | 0 | 1.83 | 1.146 |
| sin compensar | Media móvil N=21 + Euler | 2 | 0 | -6.972 | 5.587 |
| sesgo del archivo estático | Integración directa | 1 | 0.355 | -6.138 | 4.339 |
| sesgo del archivo estático | Integración directa | 2 | 0.1135 | -9.531 | 2.051 |
| sesgo del archivo estático | Media móvil N=5 + Euler | 1 | 0.355 | -6.148 | 4.342 |
| sesgo del archivo estático | Media móvil N=5 + Euler | 2 | 0.1135 | -9.524 | 2.044 |
| sesgo del archivo estático | Media móvil N=21 + Euler | 1 | 0.355 | -6.153 | 4.345 |
| sesgo del archivo estático | Media móvil N=21 + Euler | 2 | 0.1135 | -9.524 | 2.042 |
| sesgo del reposo inicial (mismo archivo) | Integración directa | 1 | 0.08132 | 0.01602 | 0.6587 |
| sesgo del reposo inicial (mismo archivo) | Integración directa | 2 | -0.2466 | -1.433 | 0.8674 |
| sesgo del reposo inicial (mismo archivo) | Media móvil N=5 + Euler | 1 | 0.08132 | 0.006762 | 0.6586 |
| sesgo del reposo inicial (mismo archivo) | Media móvil N=5 + Euler | 2 | -0.2466 | -1.425 | 0.8612 |
| sesgo del reposo inicial (mismo archivo) | Media móvil N=21 + Euler | 1 | 0.08132 | 0.001291 | 0.6581 |
| sesgo del reposo inicial (mismo archivo) | Media móvil N=21 + Euler | 2 | -0.2466 | -1.426 | 0.8583 |

El sesgo se aplica IGUAL a todos los métodos de cada variante. El sesgo cambia entre encendidos y con la temperatura: el del reposo del mismo archivo es el más cercano al real.
