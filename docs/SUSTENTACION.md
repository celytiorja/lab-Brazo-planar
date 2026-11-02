# Guía rápida de sustentación

## ⭐ Ya hay DATOS REALES (2 de noviembre de 2026)

Las secciones de abajo se escribieron cuando aún no había IMU. **Ahora todo se genera
con mediciones reales**, en `resultados/reales/e1/` y `resultados/reales/e2/`:

```
python python/analisis_e1.py
python python/analisis_e2.py
```

### Números clave (tus datos)

| Qué | Valor | Archivo |
|---|---|---|
| Muestreo | 100,00 Hz, 0 muestras perdidas en todas las capturas válidas | `e1/00_validacion_datos.md` |
| Ruido del giroscopio (reposo puro, `estatico_03`) | σ = 0,030 y 0,033 °/s | `e1/estadisticas_estatico.md` |
| R | diagonal: 8,9·10⁻⁴ y 1,06·10⁻³ (°/s)², ρ = 0,00 | `e1/matriz_R.csv`, `e1/estructura_R.md` |
| Deriva sin compensar el sesgo | +15,6 y −30,2 °/min | `e1/requisitos_kalman.md` |
| Deriva compensada (fuera de muestra) | +0,56 y −0,10 °/min | idem |
| Retraso consigna → brazo (servo) | ≈ 190 ms | `e1/correlacion_cruzada.md` |
| Media móvil N = 5 / N = 21 | 20 / 98 ms de retraso (teoría: 20 / 100) | `e1/metricas_e1.md` |
| Q elegida (con los registros de ajuste) | **Q_media**, f_c = 5 Hz, q = 0,0097 °²/s³ | `e2/resumen_seleccion_Q.md` |
| Ruido de ω en reposo puro | directa 0,031 · MM5 0,017 · **Kalman 0,014** · MM21 0,009 °/s | `e2/ruido_reposo_puro.md` |
| Retraso de ω (validación) | MM5 19,7 · **Kalman 17,3** · MM21 98 ms | `e2/metricas_e2_validacion_resumen.md` |
| Ruido de α en reposo | directa 12,0 · **Kalman 3,3** °/s² (3,7× menos) | idem |
| NIS de Kalman en reposo / en movimiento | ≈ 3,7 (seno rápido) / ~10⁵ | `e2/consistencia_kalman.md` |

**Conclusión cuantitativa:** con el mismo retraso que la media móvil N = 5 (~18–20 ms),
Kalman deja **menos ruido**. La media móvil N = 21 filtra más, pero llega **100 ms tarde**.
**Ninguno corrige la deriva del ángulo**: el error final es igual en todos (~1,5°), porque
con solo giroscopio la deriva no es observable.

### Historias reales para contar (diagnóstico con datos)

1. **Muestreo irregular en los senos (firmware 1.0 → 1.1 → 1.2).** `servo.write()` bloqueaba
   ~15 ms y el muestreo bajó a 55 Hz. Con 2 núcleos subió a 97 Hz. La interrupción del I2C
   seguía en el núcleo de los servos (lecturas de 39 ms). Con el I2C en el núcleo de muestreo:
   100,00 Hz exactos. Evidencia: `datos/crudos/descartados/LEEME.md`.
2. **El hombro no obedeció en `escalones_02`.** La consigna pidió 60° y 120°; las IMU midieron
   90°. Rechazada automáticamente (amplitud medida/consigna = 0,47). **La consigna es un deseo,
   no una medición.** Ver `rechazadas` en `datos/crudos/manifiesto.json`.
3. **Dos de tres reposos no eran reposo** (Levene p ≈ 10⁻³⁶, ρ = 0,85 entre giros: un
   movimiento físico común). El tercero es ruido puro (p = 0,77, ρ = 0,00) y es el que da R.
4. **El brazo se movía al empezar el perfil** (venía de otra pose): se descarta el 1.er
   segundo del reposo inicial. El error estacionario bajó de 49° a 5,8°.
5. **R de reposo subestima el ruido en operación:** NIS ≫ 2 en movimiento (vibración del servo,
   amplitud que el servo no alcanza). Es una limitación del modelo y de R, y propone R mayor en
   movimiento o una referencia absoluta.

## Lo que había que decir cuando aún no había IMU (histórico)

**Las IMU no se lograron conectar físicamente.** Por eso:

- Lo de **cinemática y servos** está probado **en el brazo real**.
- Toda la cadena de **procesamiento de señales** (Entrega 1 y Kalman) está **implementada
  y funcionando**. Se probó con **datos SINTÉTICOS**, generados por código con el mismo
  formato que enviará el ESP32. Todas las gráficas llevan la marca "DATOS SINTÉTICOS".
- Cuando haya IMU, se capturan los datos reales y se ejecutan **los mismos dos comandos**:
  no hay que cambiar el código.

> Nunca presentar los datos sintéticos como mediciones reales.

## Qué mostrar, en orden

### 1. Cinemática directa e inversa (brazo real)

- Teoría: `docs/01_cinematica.md` (ejemplo resuelto a mano: θ1 = 30°, θ2 = 45°).
- Código: `python/cinematica.py`.
- Pruebas automáticas: `python -m pytest python/`
- Simulador: `python python/simulador.py` (codo arriba/abajo, espacio de trabajo).
- Brazo real: `python python/interfaz.py`, con el ESP32 cargado con `prueba_servos`.
- Error observado: al cambiar de codo arriba a codo abajo, la punta no quedaba en el mismo
  punto. Causa: el servo del codo estaba montado al revés (signo). Un offset en el hombro
  NO rompe esa coincidencia; uno en el codo SÍ.

### 2. Firmware de adquisición (listo, sin probar con IMU)

`firmware/adquisicion/adquisicion.ino`

- 100 Hz con ritmo fijo (`micros()`), y una marca de tiempo por cada IMU.
- 460 800 baudios: a 115 200 no caben 100 líneas de ~115 caracteres por segundo.
- DLPF de 44 Hz como antialias (por debajo de Nyquist, que es 50 Hz).
- Giroscopio a ±500 °/s, porque el MG996R gira a ~350 °/s.
- Perfiles repetibles en el propio ESP32 (escalones, seno lento, seno rápido), con reposo
  de 3 s antes y después.
- Columnas del archivo: ver el encabezado del `.ino`. Configuración: `python/config_imu.py`.

### 3. Entrega 1: caracterización (con datos sintéticos)

Ejecutar: `python python/analisis_e1.py --manifiesto datos/sinteticos/manifiesto.json`

Los resultados quedan en `resultados/sinteticos/e1/`:

| Punto de la guía | Archivo |
|---|---|
| Media, varianza y σ por canal | `estadisticas_estatico.md` |
| Matriz R | `matriz_R.csv`, `03_matriz_R.png` |
| Muestreo real, jitter, pérdidas, desfase IMU1–IMU2 | `temporizacion.md`, `04_histograma_dt.png` |
| Correlación cruzada (relación física esperada) | `correlacion_cruzada.md`, `06_correlacion_cruzada.png` |
| Deriva por sesgo | `05_deriva_en_reposo.png` |
| Euler con media móvil (N = 5 y N = 21) | `07_dinamico_comparacion.png`, `08_zoom_retraso.png` |
| Tabla de métricas | `metricas_e1.md` |

**Frases clave:**

- **Ruido:** se ve en reposo; el giroscopio tiene σ ≈ 0,06 °/s.
- **Deriva:** el sesgo, integrado, crece linealmente con el tiempo. En `05_deriva_en_reposo.png`
  se ven unos 10° en 30 s sin quitar el sesgo, contra ~0,1° quitándolo. El sesgo se estima
  con los primeros 10 s y se prueba en el resto, para no hacer trampa.
- **Retraso:** una media móvil de N muestras retrasa (N−1)/2 muestras. Para N = 5 son 20 ms
  y para N = 21 son 100 ms. El código mide 19 ms y 99 ms, y coincide.

### 4. Entrega 2: Kalman (con datos sintéticos)

Ejecutar: `python python/analisis_e2.py --manifiesto datos/sinteticos/manifiesto.json`

Los resultados quedan en `resultados/sinteticos/e2/`:

- **Modelo:** `python/modelo_kalman.py`.
  - Estado `x = [φ1, ω1, φ2, ω2]`, en ángulos absolutos de cada eslabón.
  - Proceso: F = [[1, Δt], [0, 1]] por eslabón, usando el Δt_k real de los timestamps.
  - Ruido de proceso: Q = q·[[Δt³/3, Δt²/2], [Δt²/2, Δt]] (aceleración como ruido blanco).
  - Medición: H = [[0,1,0,0], [0,0,0,1]]: los giroscopios miden ω.
  - R sale de la Entrega 1, y la inicialización de x̂0 y P0 está en `python/config_kalman.py`.
  - Al final: θ1 = φ1 y θ2 = φ2 − φ1.
- **Ecuaciones:** `python/kalman.py`. Predicción, ganancia K, actualización, y la forma de
  Joseph para P.
- **Tres configuraciones de Q razonadas** (`config_kalman.py`):
  - Cada Q se define por la frecuencia de corte que se busca: 1,5, 5 y 15 Hz.
  - El valor de q se calcula a partir de R.
- **Ajuste y validación separados:** archivos `_01` para ajustar y `_02` para validar.
  - La selección queda en `seleccion_Q.json` y `resumen_seleccion_Q.md`.
  - Regla: menor ruido con retraso ≤ 40 ms. Resultado: Q_media.
  - Validación: `metricas_e2_validacion_resumen.md`.
- **Consistencia:** `consistencia_kalman.md`, `11_innovaciones_nis.png`.
  - En reposo, el NIS ≈ 2, que es lo esperado.
  - En movimiento, el NIS sube mucho: la vibración del servo y los cambios bruscos no
    están en el modelo. Es una limitación honesta.
  - P es simétrica (asimetría ~1e-20) y positiva.
- **P y K:** `12_P_y_K.png`. K converge a un valor estacionario.
- **Compromiso Q/R:** `14_compromiso_Q_R.png`. Más q da más ancho de banda y menos retraso,
  pero más ruido.
- **Aceleración angular:** `aceleracion_angular.md`, `13_aceleracion_angular.png`.
  - Diferencia hacia atrás: el ruido de α es √2·σω/Δt, unas 141 veces σω.
  - Central: σω/(√2·Δt). Medido ≈ teórico.

**Límite clave para la sustentación:** con solo giroscopio, la deriva del ángulo **no es
observable**. Kalman suaviza ω, pero no puede corregir la deriva de φ. Para eso hace falta
una referencia absoluta: el acelerómetro en un plano vertical (el código ya lo soporta con
`PLANO_VERTICAL = True`), un encoder o la cámara. **Suavizar no es lo mismo que ser más
preciso.**

## Material adicional de la Entrega 1 (añadido)

- **Localizadores E1–E9 y respuestas modelo** de la comprobación individual: `docs/ENTREGAS.md`.
- **Diccionario de datos:** `datos/DICCIONARIO.md`. Cada IMU mide respecto al **marco fijo**;
  por eso θ2 = φ2 − φ1.
- **Verificación cinemática:** `python python/verificacion_cinematica.py`. Da el error en mm por
  punto, la repetibilidad y los **offsets estimados** de cada articulación
  (`09_verificacion_cinematica.png`).
- **Integridad de los datos:** `00_validacion_datos.md`.
- **Sensibilidad a la ventana:** `10_sensibilidad_ventana.png`. El retraso medido sigue la recta
  (N−1)/2 y el ruido baja como σ/√N.
- **Estructura de R:** `estructura_R.md`. Ruido estacionario y ρ(w1, w2) ≈ 0, así que R es
  diagonal.
- **Requisitos para el Kalman, calculados con datos:** `requisitos_kalman.md`.

## Qué falta (decirlo)

- Captura con IMU reales: el firmware está listo; faltó el montaje físico.
- Teleoperación usando la estimación, y la verificación de la cinemática con medidas en
  papel milimetrado.
