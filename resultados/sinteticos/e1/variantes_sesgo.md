# Variantes de compensación del sesgo

| variante_sesgo | metodo | eslabon | sesgo_usado_dps | deriva_final_deg | error_estacionario_rms_deg |
| --- | --- | --- | --- | --- | --- |
| sin compensar | Integración directa | 1 | 0 | 1.886 | 1.175 |
| sin compensar | Integración directa | 2 | 0 | -7.103 | 5.741 |
| sin compensar | Media móvil N=5 + Euler | 1 | 0 | 1.877 | 1.172 |
| sin compensar | Media móvil N=5 + Euler | 2 | 0 | -7.096 | 5.735 |
| sin compensar | Media móvil N=21 + Euler | 1 | 0 | 1.871 | 1.168 |
| sin compensar | Media móvil N=21 + Euler | 2 | 0 | -7.097 | 5.735 |
| sesgo del archivo estático | Integración directa | 1 | 0.355 | -6.276 | 4.475 |
| sesgo del archivo estático | Integración directa | 2 | 0.1135 | -9.713 | 2.075 |
| sesgo del archivo estático | Media móvil N=5 + Euler | 1 | 0.355 | -6.286 | 4.478 |
| sesgo del archivo estático | Media móvil N=5 + Euler | 2 | 0.1135 | -9.706 | 2.069 |
| sesgo del archivo estático | Media móvil N=21 + Euler | 1 | 0.355 | -6.291 | 4.482 |
| sesgo del archivo estático | Media móvil N=21 + Euler | 2 | 0.1135 | -9.706 | 2.069 |
| sesgo del reposo inicial (mismo archivo) | Integración directa | 1 | 0.08081 | 0.02791 | 0.641 |
| sesgo del reposo inicial (mismo archivo) | Integración directa | 2 | -0.2507 | -1.339 | 0.8071 |
| sesgo del reposo inicial (mismo archivo) | Media móvil N=5 + Euler | 1 | 0.08081 | 0.01863 | 0.6412 |
| sesgo del reposo inicial (mismo archivo) | Media móvil N=5 + Euler | 2 | -0.2507 | -1.331 | 0.8011 |
| sesgo del reposo inicial (mismo archivo) | Media móvil N=21 + Euler | 1 | 0.08081 | 0.01304 | 0.641 |
| sesgo del reposo inicial (mismo archivo) | Media móvil N=21 + Euler | 2 | -0.2507 | -1.332 | 0.7995 |

El sesgo se aplica IGUAL a todos los métodos de cada variante. El sesgo cambia entre encendidos y con la temperatura: el del reposo del mismo archivo es el más cercano al real.
