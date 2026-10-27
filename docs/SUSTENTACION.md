# Guía rápida de sustentación

## Lo que hay que decir con honestidad

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

## Qué falta (decirlo)

- Captura con IMU reales: el firmware está listo; faltó el montaje físico.
- Teleoperación usando la estimación, y la verificación de la cinemática con medidas en
  papel milimetrado.
