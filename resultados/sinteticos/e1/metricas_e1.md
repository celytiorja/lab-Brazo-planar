# Métricas Entrega 1

| metodo | articulacion | ruido_omega_reposo_dps | deriva_reposo_30s_deg | retraso_vs_directa_ms | error_estacionario_rms_deg | deriva_final_perfil_deg | ruido_angulo_reposo_deg |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Integración directa | θ1 | 0.06052 | -0.03961 | 0 | 0.6587 | 0.01602 | 0.00171 |
| Integración directa | θ2 | 0.05949 | -0.09209 | 0 | 0.8674 | -1.449 | 0.002234 |
| Media móvil N=5 + Euler | θ1 | 0.02671 | -0.04167 | 19.27 | 0.6586 | 0.006762 | 0.001624 |
| Media móvil N=5 + Euler | θ2 | 0.02651 | -0.09162 | 19.82 | 0.8612 | -1.432 | 0.002131 |
| Media móvil N=21 + Euler | θ1 | 0.01325 | -0.0443 | 98.97 | 0.6581 | 0.001291 | 0.001397 |
| Media móvil N=21 + Euler | θ2 | 0.0125 | -0.0911 | 99.79 | 0.8583 | -1.427 | 0.00174 |

ruido_omega_reposo: σ de la velocidad estimada con el brazo quieto (archivo estático). deriva_reposo_30s: ángulo acumulado tras 30 s quieto (debería ser 0). retraso_vs_directa: correlación cruzada contra la integración directa (que no filtra). error_estacionario: contra la consigna SOLO donde lleva ≥0.5 s constante (servo ya llegó). deriva_final_perfil: el perfil vuelve a la pose inicial; lo que no vuelva es deriva.

Generado por código · commit 54720e5+cambios_sin_commit · manifiesto datos/sinteticos/manifiesto.json
