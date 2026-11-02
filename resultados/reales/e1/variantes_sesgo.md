# Variantes de compensación del sesgo

| variante_sesgo | metodo | eslabon | sesgo_usado_dps | deriva_final_deg | error_estacionario_rms_deg |
| --- | --- | --- | --- | --- | --- |
| sin compensar | Integración directa | 1 | 0 | 10.99 | 8.665 |
| sin compensar | Integración directa | 2 | 0 | -4.824 | 10.43 |
| sin compensar | Media móvil N=5 + Euler | 1 | 0 | 10.99 | 8.664 |
| sin compensar | Media móvil N=5 + Euler | 2 | 0 | -4.826 | 10.43 |
| sin compensar | Media móvil N=21 + Euler | 1 | 0 | 10.98 | 8.668 |
| sin compensar | Media móvil N=21 + Euler | 2 | 0 | -4.831 | 10.44 |
| sesgo del archivo estático | Integración directa | 1 | 0.2604 | 5.135 | 5.3 |
| sesgo del archivo estático | Integración directa | 2 | -0.504 | 6.514 | 4.338 |
| sesgo del archivo estático | Media móvil N=5 + Euler | 1 | 0.2604 | 5.134 | 5.299 |
| sesgo del archivo estático | Media móvil N=5 + Euler | 2 | -0.504 | 6.512 | 4.338 |
| sesgo del archivo estático | Media móvil N=21 + Euler | 1 | 0.2604 | 5.127 | 5.304 |
| sesgo del archivo estático | Media móvil N=21 + Euler | 2 | -0.504 | 6.507 | 4.334 |
| sesgo del reposo inicial (mismo archivo) | Integración directa | 1 | 0.2218 | 6.004 | 5.759 |
| sesgo del reposo inicial (mismo archivo) | Integración directa | 2 | -0.5567 | 7.698 | 4.425 |
| sesgo del reposo inicial (mismo archivo) | Media móvil N=5 + Euler | 1 | 0.2218 | 6.002 | 5.758 |
| sesgo del reposo inicial (mismo archivo) | Media móvil N=5 + Euler | 2 | -0.5567 | 7.697 | 4.425 |
| sesgo del reposo inicial (mismo archivo) | Media móvil N=21 + Euler | 1 | 0.2218 | 5.995 | 5.763 |
| sesgo del reposo inicial (mismo archivo) | Media móvil N=21 + Euler | 2 | -0.5567 | 7.691 | 4.421 |

El sesgo se aplica IGUAL a todos los métodos de cada variante. El sesgo cambia entre encendidos y con la temperatura: el del reposo del mismo archivo es el más cercano al real.
