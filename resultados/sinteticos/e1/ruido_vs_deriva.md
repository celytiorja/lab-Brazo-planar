# Ruido de alta frecuencia vs deriva (reposo)

| metodo | eslabon | ruido_alta_frec_angulo_deg | ruido_omega_dps | deriva_deg_por_min | angulo_final_deg |
| --- | --- | --- | --- | --- | --- |
| Integración directa | 1 | 0.009585 | 0.06112 | -0.1714 | -0.1021 |
| Integración directa | 2 | 0.00996 | 0.05917 | -0.3523 | -0.1722 |
| Media móvil N=5 + Euler | 1 | 0.009483 | 0.02698 | -0.1719 | -0.1021 |
| Media móvil N=5 + Euler | 2 | 0.009951 | 0.0262 | -0.3522 | -0.1739 |
| Media móvil N=21 + Euler | 1 | 0.009333 | 0.01361 | -0.1704 | -0.1005 |
| Media móvil N=21 + Euler | 2 | 0.009928 | 0.01234 | -0.351 | -0.1763 |

La media móvil baja el ruido pero NO cambia la pendiente (deriva): son problemas distintos. Evaluado fuera de muestra (sesgo de los primeros 10 s).
