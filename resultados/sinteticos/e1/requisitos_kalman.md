# Requisitos para el filtro de Kalman (Entrega 2), calculados de la Entrega 1

- Ruido del giroscopio en reposo: σ1 = 0.0605 °/s, σ2 = 0.0595 °/s → R diagonal (ρ w1–w2 = +0.017).
- Deriva SIN compensar el sesgo: +21.3 y +6.8 °/min. Compensada (fuera de muestra): -0.17 y -0.35 °/min.
- Para bajar el ruido a la mitad, la media móvil necesita N = 5 → retraso ≈ 19 ms.
- En movimiento suave (perfiles seno) el ruido aparente es 27.5× el de reposo.

## Conclusión
- **Integración directa:** retraso 0, pero todo el ruido pasa y la deriva se acumula.
- **Media móvil:** el ruido baja como 1/√N, pagando (N−1)/2 muestras de retraso; la deriva final es la MISMA que sin filtrar (ver `variantes_sesgo` y `ruido_vs_deriva`).
- Ninguno resuelve a la vez deriva y retraso.

## Requisitos para la Entrega 2
1. Retraso de ω ≤ 40 ms.
2. Ruido de ω en reposo ≤ 0.0267 °/s (el de media móvil N = 5) o menor.
3. Usar el Δt_k real y la R medida aquí (y considerar que en movimiento el ruido es mayor).
4. Deriva: con solo giroscopio no es observable; se acota y se declara, o se agrega una referencia absoluta.
