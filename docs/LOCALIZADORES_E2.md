# Localizadores para el instrumento de la Entrega 2 (v2.0)

Para copiar en la **sección 3 "Registro mínimo de evidencias"** del instrumento y para saber qué
abrir frente al profesor. Rutas relativas a la raíz del repositorio
`github.com/celytiorja/lab-Brazo-planar`, rama `claude/friendly-feynman-xfljpf`
(al entregar: `git tag entrega2` y anotar el commit).

> La rúbrica dice: **no se califica informe** (0 %). Se evalúan **código, datos, resultados
> reproducibles y demostración**. Todo lo de abajo se regenera con código.

---

## Sección 1 del instrumento (identificación)

| Campo | Qué poner |
|---|---|
| Repositorio, commit o versión | `https://github.com/celytiorja/lab-Brazo-planar`, etiqueta `entrega2` (commit: `git log --oneline -1`) |
| Enlace o ubicación | el mismo repositorio; guía de evidencias: `docs/LOCALIZADORES_E2.md` |

---

## Sección 3: texto para cada evidencia

**E5 — Código de Kalman y comparación; estado, mediciones, F, H, Q, R, inicialización, parámetros**
> Ecuaciones (predicción, K, actualización, Joseph, NIS): `python/kalman.py`. Modelo (estado
> [φ1, ω1, φ2, ω2], F, Q, H con Δt real): `python/modelo_kalman.py`. Estimadores comparados
> (integración directa, media móvil, Kalman; θ2 = φ2 − φ1): `python/estimadores.py`.
> Parámetros (3 Q por f_c, P0, regla ≤ 40 ms): `python/config_kalman.py`. R de la Entrega 1:
> `resultados/reales/e1/R.json`. Ejecución: `python python/analisis_e2.py`. Kalman de la
> cámara (teleoperación, H mide θ, medición parcial): `python/kalman_camara.py`,
> `python/config_camara.py`. Pruebas: `python -m pytest python/`.

**E6 — Datos de ajuste y validación; ≥ 3 configuraciones razonadas de Q**
> Datos crudos: `datos/crudos/*.csv` + `.json`. Asignación ajuste/validación automática:
> `datos/crudos/manifiesto.json` (ajuste: escalones_01, seno_lento_01, seno_rapido_01;
> validación: escalones_03, seno_lento_02, seno_rapido_02; reposo para R: estatico_03).
> 3 Q razonadas (f_c 1.5 / 5 / 15 Hz) y selección: `resultados/reales/e2/seleccion_Q.json`,
> `resumen_seleccion_Q.md`, `metricas_e2_ajuste.md`. Cámara (f_n 1.5 / 3 / 6 Hz):
> `resultados/<origen>/teleop/configuraciones_q_camara.md`.

**E7 — Gráficas y métricas por código; aceleración angular; selección final; límites**
> `resultados/reales/e2/`: comparación en validación `metricas_e2_validacion_resumen.md` y
> `15_validacion_comparacion_*.png`; ajuste de las 3 Q `10_ajuste_configuraciones_Q_*.png`;
> aceleración angular (diferencia hacia atrás/central, amplificación √2·σ/Δt)
> `aceleracion_angular.md`, `13_aceleracion_angular.png`; consistencia (NIS, simetría y
> positividad de P) `consistencia_kalman.md`, `11_innovaciones_nis.png`, `12_P_y_K.png`;
> compromiso Q/R `compromiso_Q_R.md`, `14_compromiso_Q_R.png`. Límites de lo verificable
> (deriva no observable con solo giroscopio en plano horizontal): `docs/GUIA_ENTREGA2.md` §4.

**E8 — Visualización comparativa y teleoperación con la estimación**
> Ejecución en vivo: `python python/teleop_camara.py --video <IP> --puerto COM3` (panel con θ
> crudo vs Kalman y gráficas en vivo, tecla F crudo↔Kalman). Sesiones grabadas:
> `datos/teleop/sesion_XX.csv` (+ `.json` con Q, R, offset y commit; `_robot.csv` con el
> giroscopio del robot). Métricas por código: `python python/analisis_teleop.py` →
> `resultados/reales/teleop/resumen_teleop.md`, `20_teleop_*.png`, `21_robot_*.png`.
> Latencia del lector de video: `python python/prueba_latencia_video.py`
> (`resultados/latencia_video.json`). Visualización de las IMU en vivo: `python python/interfaz_imu.py`.
> Video de apoyo: (agregar enlace si se graba).

**E9 — Comprobación individual**
> Respuestas modelo a las tres preguntas del instrumento: `docs/ENTREGAS.md` (sección
> Entrega 2) y `docs/GUIA_ENTREGA2.md` §5.

---

## Qué mostrar para cada NIVEL (sección 4 del instrumento)

### C1 — Modelo e implementación (50 %)

| Nivel | Lo que pide | Dónde se ve |
|---|---|---|
| N3 | estado, mediciones, unidades; F, H, Q, R (R de la E1); x̂0, P0; predicción, K, actualización y P reproducibles; aceleración con su esquema numérico | `modelo_kalman.py`, `kalman.py` (líneas 22–42), `config_kalman.py` (P0 línea 44), `R.json`, `aceleracion_angular.md` |
| N4 | simetría y positividad de P; comportamiento de K; **Δt_k real**; amplificación de ruido al derivar | `consistencia_kalman.md` (max_asimetria ~1e−20, min_autovalor > 0), `12_P_y_K.png`, `estimadores.py` (`paso(dt, …)` con el Δt de los timestamps), `aceleracion_angular.md` (teoría 6.6 vs medido 4.9 °/s²) |
| N5 | estructura física del modelo (acoplamiento articular / cinemática / bias); consistencia de las innovaciones y_k; todas las configuraciones modulares sin editar salidas | acoplamiento: la IMU2 mide φ2 = θ1 + θ2 → θ2 = φ2 − φ1 (`estimadores.py`); bias como estado opcional (`config_kalman.py`, `ESTIMAR_BIAS_SI_HAY_INCLINACION`, se justifica por qué no aplica en plano horizontal); NIS y autocorrelación de innovaciones (`consistencia_kalman.md`); las 3 Q corren solas desde `config_kalman.py` con `analisis_e2.py` |

### C2 — Validación y demostración (20 %)

| Nivel | Lo que pide | Dónde se ve |
|---|---|---|
| N3 | ≥ 3 Q con ajuste ≠ validación; directa, MM y Kalman con mismas condiciones; teleoperación funcional con la estimación | `manifiesto.json`, `seleccion_Q.json`, `metricas_e2_validacion_resumen.md`; **demo en vivo** `teleop_camara.py` |
| N4 | ensayos repetibles de teleoperación con distintos perfiles; trazabilidad archivo ↔ Q ↔ métricas ↔ respuesta | protocolo de 30 s (lento/rápido/oclusión) guiado en pantalla; cada `sesion_XX.json` guarda la Q, R, offset y commit; `resumen_teleop.md` |
| N5 | tiempos de cómputo por ciclo, latencia, estabilidad; **contraste teleoperar crudo vs Kalman** | `resumen_teleop.md` (t Kalman µs, detección + Kalman ms, retraso orden→robot y cámara→robot con el giroscopio del robot, sesión crudo vs sesión Kalman), `latencia_video.json` |

### C3 — Interpretación y selección de parámetros (30 %)

| Nivel | Lo que pide | Dónde se ve |
|---|---|---|
| N3 | comparar los 3 métodos con métricas de la E1 + validación; justificar Q frente a R; explicar ruido, deriva, retraso y aceleración; acotar la deriva no observable | `metricas_e2_validacion_resumen.md`, `resumen_seleccion_Q.md` (regla ≤ 40 ms), `docs/GUIA_ENTREGA2.md` §3–§4 |
| N4 | compromiso Q/R cuantitativo (ancho de banda, retardo, rechazo de ruido) y vínculo con la suavidad en teleoperación | `compromiso_Q_R.md` + `14_compromiso_Q_R.png` (IMU); `configuraciones_q_camara.md` (cámara: ruido ×0.53/0.70/0.86, retraso a 2 Hz 58/16/2 ms); `resumen_teleop.md` (aspereza crudo vs Kalman) |
| N5 | límites estructurales con datos (incluida la ausencia de mejora) y decisiones de fusión o rediseño | NIS ≫ 2 en movimiento, deriva igual en todos los métodos, Kalman no más exacto que la cámara cuando ve bien (`docs/GUIA_ENTREGA2.md` §4); fusión cámara + giroscopio en `kalman_camara.py` (filas de H y R a agregar) |

---

## Antes de entregar (lista corta)

1. Grabar las sesiones de teleoperación (una con F = CRUDO y otra con F = KALMAN), salir con Q
   para que se analicen y se suban (`docs/PRUEBA_FINAL.md`).
2. Comprobar que existe `resultados/reales/teleop/resumen_teleop.md`.
3. `git tag entrega2` y `git push origin entrega2`; anotar el commit en el instrumento.
