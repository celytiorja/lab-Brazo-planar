# Requisitos para el filtro de Kalman (Entrega 2), calculados de la Entrega 1

- Ruido del giroscopio en reposo: σ1 = 0.0299 °/s, σ2 = 0.0326 °/s → R diagonal (ρ w1–w2 = -0.000).
- Deriva SIN compensar el sesgo: +15.6 y -30.2 °/min. Compensada (fuera de muestra): +0.56 y -0.10 °/min.
- Para bajar el ruido a la mitad, la media móvil necesita N = 9 → retraso ≈ 39 ms.
- En movimiento suave (perfiles seno) el ruido aparente es 102.9× el de reposo.

## Conclusión
- **Integración directa:** retraso 0, pero todo el ruido pasa y la deriva se acumula.
- **Media móvil:** el ruido baja como 1/√N, pagando (N−1)/2 muestras de retraso; la deriva final es la MISMA que sin filtrar (ver `variantes_sesgo` y `ruido_vs_deriva`).
- Ninguno resuelve a la vez deriva y retraso.

## Requisitos para la Entrega 2
1. Retraso de ω ≤ 40 ms.
2. Ruido de ω en reposo ≤ 0.0163 °/s (el de media móvil N = 5) o menor.
3. Usar el Δt_k real y la R medida aquí (y considerar que en movimiento el ruido es mayor).
4. Deriva: con solo giroscopio no es observable; se acota y se declara, o se agrega una referencia absoluta.
