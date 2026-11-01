# Localizadores de evidencias (Entregas 1 y 2)

Para llenar la columna **"Archivo, enlace, página o ubicación"** de cada instrumento.

- **Repositorio:** `github.com/celytiorja/lab-Brazo-planar`, rama `claude/friendly-feynman-xfljpf`.
  Indicar el **commit** o la etiqueta (`git tag entrega1`).
- `<origen>` = `reales` (capturas con las IMU) o `sinteticos` (datos de prueba, marcados).
- **Nunca** presentar los resultados `sinteticos` como mediciones.

## Entrega 1: caracterización y métodos base

| Código | Evidencia que pide el instrumento | Dónde está | Criterio / nivel que respalda |
|---|---|---|---|
| **E1** | Datos crudos estáticos y dinámicos de ambas IMU, timestamp, configuración, diccionario. Reposo ≥ 30 s | `datos/crudos/estatico_01.csv` (40 s) + `escalones_01.csv`, `seno_*_01/02.csv`, cada uno con su `.json`. Diccionario: `datos/DICCIONARIO.md`. Firmware: `firmware/adquisicion/adquisicion.ino`. Configuración: `python/config_imu.py` | C2-N3 (timestamp, fs, unidades, correspondencia sensor–eje–articulación); C2-N4 (marco fijo vs eslabón: sección "Marco de referencia" del diccionario) |
| **E2** | Código de cinemática, caracterización, Euler y media móvil; parámetros; dependencias; comando | Cinemática: `python/cinematica.py`, `python/verificacion_cinematica.py`. Caracterización: `python/analisis_e1.py`, `python/analisis_e1_extra.py`. Euler y media móvil: `python/estimadores.py`. Parámetros: `python/parametros.py`, `python/config_imu.py`, `python/config_kalman.py`. Dependencias: `requirements.txt`. Comandos: `README.md` y `docs/04_captura_y_entregas.md`. Pruebas: `python -m pytest python/` | C1-N3/N4 (pipeline parametrizado; mismo sesgo y condición inicial para todos los métodos); C2-N5 (`python/validar_datos.py`: integridad automática) |
| **E3** | Gráficas y tablas generadas por código: cinemática, media, varianza, R, análisis temporal, ≥ 2 métricas | `resultados/<origen>/e1/` (ver tabla siguiente) | C3-N3…N5, C1-N4/N5 |
| **E4** | Demostración y comprobación individual | Ejecutar en vivo: `python python/analisis_e1.py` (regenera todo) y `python python/interfaz_imu.py` (IMU en vivo). Respuestas modelo abajo | C1–C3 individual |

### Detalle de E3 (`resultados/<origen>/e1/`)

| Qué pide la guía | Archivo |
|---|---|
| Integridad de los datos | `00_validacion_datos.md` |
| Comprobación cinemática (posiciones de referencia, errores, repetibilidad, offsets) | `verificacion_cinematica.md`, `verificacion_cinematica_resumen.md`, `09_verificacion_cinematica.png` |
| Media y varianza por canal | `estadisticas_estatico.md`, `01_reposo_senales_histogramas.png` |
| Matriz R (variables y unidades) | `matriz_R.csv`, `R.json`, `03_matriz_R.png` |
| Estructura de R: estacionariedad y correlación entre canales | `estructura_R.md`, `11_correlacion_canales.png` |
| Análisis temporal: fs, Δt, jitter, pérdidas, desfase IMU1–IMU2 | `temporizacion.md`, `04_histograma_dt.png` |
| Correlación cruzada: desfase instrumental vs físico | `correlacion_cruzada.md`, `06_correlacion_cruzada.png` |
| Deriva por sesgo (fuera de muestra) | `05_deriva_en_reposo.png`, `ruido_vs_deriva.md` |
| Euler y media móvil (N = 5 y 21), mismas condiciones | `07_dinamico_comparacion.png`, `08_zoom_retraso.png` |
| Tabla con ≥ 2 métricas | `metricas_e1.md`: ruido, deriva, retraso, error estacionario |
| Sensibilidad a la ventana (N = 1…51) | `sensibilidad_ventana.md`, `10_sensibilidad_ventana.png` |
| Variantes de compensación del sesgo | `variantes_sesgo.md` |
| Δt_k real vs 1/fs | `dt_real_vs_nominal.md` |
| Repetibilidad (rep. 01 vs 02) | `repetibilidad.md` |
| Ruido en reposo vs en movimiento | `degradacion_movimiento.md` |
| Requisitos cuantitativos para el Kalman | `requisitos_kalman.md` |

## Entrega 2: filtro de Kalman

| Código | Evidencia | Dónde está | Criterio |
|---|---|---|---|
| **E5** | Código de Kalman y comparación; estado, mediciones, F, H, Q, R, inicialización, parámetros | Ecuaciones: `python/kalman.py`. Modelo (estado, F, Q, H): `python/modelo_kalman.py`. Configuración (3 Q, P0, regla): `python/config_kalman.py`. R: `resultados/<origen>/e1/R.json`. Comparación: `python/analisis_e2.py`, `python/estimadores.py` | C1-N3…N5 |
| **E6** | Datos de ajuste y validación identificados; ≥ 3 Q razonadas | Manifiesto: `datos/<crudos\|sinteticos>/manifiesto.json` (ajuste = `_01`, validación = `_02`). Selección: `resultados/<origen>/e2/seleccion_Q.json`, `resumen_seleccion_Q.md`, `metricas_e2_ajuste.md` | C2-N3, C3-N3 |
| **E7** | Gráficas y métricas por código; aceleración angular y método numérico; límites de lo verificable | `resultados/<origen>/e2/`: `metricas_e2_validacion*.md`, `10_*`, `15_*`, `11_innovaciones_nis.png`, `consistencia_kalman.md`, `12_P_y_K.png`, `14_compromiso_Q_R.png`, `compromiso_Q_R.md`, `aceleracion_angular.md`, `13_aceleracion_angular.png` | C1-N4/N5, C3-N3/N4 |
| **E8** | Visualización comparativa y teleoperación con la estimación | `python python/interfaz_imu.py` ("Mover el brazo con: Kalman / Media móvil / Integración directa"); tiempo de cómputo por muestra en la parte inferior. Grabaciones de sesión: botón "Grabar libre" | C2-N3…N5 |
| **E9** | Comprobación individual | Respuestas modelo abajo | — |

---

# Preguntas de comprobación individual: respuestas modelo

Las respuestas son **cortas**, para decirlas con tus palabras **mostrando el archivo**. Los números
que aparecen son de los datos sintéticos; con datos reales, léelos de las mismas tablas.

## Entrega 1

**C1. "Ejecute o señale el paso de integración y una ventana de media móvil; explique el intervalo
de muestreo, la digitalización y la condición inicial."**

- **Mostrar** `python/estimadores.py`, clases `IntegracionDirecta.paso` y `MediaMovilIntegracion.paso`.
- **Integración:** `φ_k = φ_{k−1} + Δt_k · (w_k − b)` (Euler). Δt_k es el **real**, sale de los
  timestamps `t1_us` del ESP32, no de 1/fs. Si se pierde una muestra, Δt_k = 20 ms y el ángulo
  no se corre (ver `dt_real_vs_nominal.md`).
- **Media móvil:** promedio de las últimas N muestras de w, antes de integrar. Retraso (N−1)/2
  muestras: N = 5 → 20 ms y N = 21 → 100 ms (medido: 19 y 99 ms).
- **Digitalización:** la MPU-6050 entrega enteros de 16 bits. A ±500 °/s, 1 cuenta = 1/65,5 °/s.
  Se muestrea a 100 Hz con un filtro interno de 44 Hz como antialias (Nyquist = 50 Hz).
- **Condición inicial:** todos los métodos parten de la misma pose (la consigna en el reposo
  inicial) y del mismo sesgo (media del reposo de 3 s del mismo archivo).

**C2. "Identifique un registro estático y uno dinámico, sus condiciones de captura y una
comprobación de la plataforma o la cinemática."**

- **Estático:** `datos/crudos/estatico_01.csv`. 40 s con el brazo quieto en servos (90, 90),
  perfil 0, fase −1.
- **Dinámico:** `escalones_01.csv`. Perfil 1: 3 s de reposo, 20 s de escalones y 3 s de reposo,
  generado por el firmware en función del tiempo, así que es repetible.
- **Condiciones de ambos:** 100 Hz, ±500 °/s, ±2 g, DLPF 44 Hz, 460800 baudios. Está en su `.json`.
- **Comprobaciones:**
  - `00_validacion_datos.md`: fs real, jitter, pérdidas y que ninguna IMU esté congelada.
  - `verificacion_cinematica_resumen.md`: RMSE en mm, repetibilidad y offsets estimados.

**C3. "Interprete una métrica o un componente de R y explique una diferencia de ruido, deriva o
retraso entre métodos."**

- **R:** R[0,0] ≈ 0,0037 (°/s)² es la varianza del giro 1 en reposo, o sea σ ≈ 0,06 °/s. Fuera
  de la diagonal ≈ 0: ρ = 0,02 < 0,1, así que R puede ser diagonal (`estructura_R.md`).
- **Diferencia entre métodos** (`metricas_e1.md`, `sensibilidad_ventana.md`):
  - **Ruido:** la media móvil N = 21 baja el ruido de ω de 0,060 a 0,013 °/s.
  - **Retraso:** a cambio, llega 99 ms tarde.
  - **Deriva:** la deriva final es la **misma** en los dos métodos, porque promediar no quita el
    sesgo.

## Entrega 2

**C1. "Identifique el vector de estado y una etapa de predicción o actualización; explique el papel
de H y de las mediciones."**

- **Mostrar** `python/modelo_kalman.py` y `python/kalman.py`.
- **Estado:** `x = [φ1, ω1, φ2, ω2]`: ángulo absoluto y velocidad de cada eslabón, en ° y °/s.
- **Predicción:** `x̂⁻ = F x̂` con F = [[1, Δt_k], [0, 1]] por eslabón, y `P⁻ = F P Fᵀ + Q`.
- **Mediciones:** los dos giroscopios, z = [w1 − b1, w2 − b2].
- **Papel de H** = [[0,1,0,0], [0,0,0,1]]: dice que los giroscopios miden **solo ω**. Por eso
  el ángulo no se corrige con mediciones: se obtiene integrando, y su deriva no es observable.
- Al final: θ2 = φ2 − φ1.

**C2. "Reproduzca o identifique una configuración de Q y explique cómo se controlaron las
condiciones de comparación y se validó la teleoperación."**

- **Configuración de Q** (`config_kalman.py`): Q_media tiene f_c = 5 Hz, es decir, unas 5 veces
  la frecuencia del seno rápido.
  - De f_c sale la ganancia K = 1 − e^(−2π f_c Δt).
  - De K sale q = λ·r/Δt, con λ = K²/(1 − K) y r tomado de R (Entrega 1).
  - El valor queda en `seleccion_Q.json`.
- **Condiciones de comparación:** los tres métodos usan la misma φ0, el mismo sesgo, los mismos
  Δt_k y las mismas unidades.
- **Ajuste y validación separados:** se ajusta con los registros `_01` y se valida con los `_02`.
- **Teleoperación:** en `interfaz_imu.py`, la fuente "Kalman" envía al servo `modelo_a_servo(θ̂)`.
  Se mide el tiempo de cómputo por muestra (decenas de µs, muy por debajo de los 10 ms del
  periodo).

**C3. "Interprete una métrica y justifique la elección final de Q; distinga suavizado de
precisión e indique el límite de una conclusión."**

- **Métrica y elección** (`resumen_seleccion_Q.md`):
  - La regla fija es: menor ruido de ω con un retraso de 40 ms o menos.
  - Q_baja tiene el menor ruido, pero 69 ms de retraso, así que no cumple.
  - **Gana Q_media:** 0,023 °/s de ruido con 13 ms de retraso.
  - En validación, frente a la integración directa, baja el ruido de ω de 0,060 a 0,025 °/s.
- **Suavizar no es lo mismo que ser preciso:** una curva más suave puede estar igual de corrida.
  La deriva final es prácticamente igual en Kalman y en integración directa (0,41 vs 0,43°).
- **Límite:** con solo giroscopio, Kalman **no puede** afirmar que corrige la deriva. Para eso
  falta una referencia independiente: el acelerómetro en un plano vertical, un encoder o la
  cámara. Las afirmaciones de precisión contra la "verdad" solo valen en los datos sintéticos.
