# Métricas Entrega 1

| metodo | articulacion | ruido_omega_reposo_dps | deriva_reposo_30s_deg | retraso_vs_directa_ms | error_estacionario_rms_deg | deriva_final_perfil_deg | ruido_angulo_reposo_deg |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Integración directa | θ1 | 0.02986 | 0.1939 | 0 | 5.759 | 6.004 | 0.02189 |
| Integración directa | θ2 | 0.03258 | -0.01968 | 0 | 4.425 | 1.695 | 0.007796 |
| Media móvil N=5 + Euler | θ1 | 0.01628 | 0.1933 | 19.2 | 5.758 | 6.002 | 0.02094 |
| Media móvil N=5 + Euler | θ2 | 0.01675 | -0.02016 | 19.81 | 4.425 | 1.695 | 0.007438 |
| Media móvil N=21 + Euler | θ1 | 0.00896 | 0.1935 | 98.95 | 5.763 | 5.995 | 0.01716 |
| Media móvil N=21 + Euler | θ2 | 0.008144 | -0.01929 | 99.72 | 4.421 | 1.696 | 0.007916 |

ruido_omega_reposo: σ de la velocidad estimada con el brazo quieto (archivo estático). deriva_reposo_30s: ángulo acumulado tras 30 s quieto (debería ser 0). retraso_vs_directa: correlación cruzada contra la integración directa (que no filtra). error_estacionario: contra la consigna SOLO donde lleva ≥0.5 s constante (servo ya llegó). deriva_final_perfil: el perfil vuelve a la pose inicial; lo que no vuelva es deriva.

Generado por código · commit 54720e5+cambios_sin_commit · manifiesto datos/crudos/manifiesto.json
