# Ruido de alta frecuencia vs deriva (reposo)

| metodo | eslabon | ruido_alta_frec_angulo_deg | ruido_omega_dps | deriva_deg_por_min | angulo_final_deg |
| --- | --- | --- | --- | --- | --- |
| Integración directa | 1 | 0.005365 | 0.02954 | 0.5607 | 0.2811 |
| Integración directa | 2 | 0.007098 | 0.03278 | -0.09617 | -0.03326 |
| Media móvil N=5 + Euler | 1 | 0.005354 | 0.0158 | 0.5607 | 0.2807 |
| Media móvil N=5 + Euler | 2 | 0.007098 | 0.01701 | -0.0961 | -0.03395 |
| Media móvil N=21 + Euler | 1 | 0.005306 | 0.00821 | 0.561 | 0.2808 |
| Media móvil N=21 + Euler | 2 | 0.0071 | 0.008301 | -0.09577 | -0.03427 |

La media móvil baja el ruido pero NO cambia la pendiente (deriva): son problemas distintos. Evaluado fuera de muestra (sesgo de los primeros 10 s).
