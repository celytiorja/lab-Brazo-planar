# Guía definitiva de la Entrega 2 (Kalman + teleoperación)

Todos los números de esta guía son **tuyos** (datos reales de `datos/crudos`), salvo los de la
sección de teleoperación marcados como sintéticos hasta que grabes tus sesiones.
Los archivos se regeneran con código: nada se editó a mano.

---

## 1. ¿Se cumple cada criterio?

| Criterio (peso) | Lo que piden | Evidencia | Estado |
|---|---|---|---|
| **C1 (50 %)** modelo | estado, F, H, Q, R (de la E1), x0 y P0 | `python/modelo_kalman.py`, `python/kalman.py`, `python/config_kalman.py`, `resultados/reales/e1/R.json` | ✅ |
| C1 | ≥ 3 Q razonadas, ajuste y validación **separados** | `config_kalman.py` (3 Q por f_c), `datos/crudos/manifiesto.json` (ajuste `_01`, validación `_02`/`_03`), `resultados/reales/e2/resumen_seleccion_Q.md`, `seleccion_Q.json` | ✅ |
| C1 | comparación integración directa / media móvil / Kalman | `resultados/reales/e2/metricas_e2_validacion_resumen.md`, `15_validacion_comparacion_*.png` | ✅ |
| C1 | aceleración angular numérica | `resultados/reales/e2/aceleracion_angular.md`, `13_aceleracion_angular.png` | ✅ |
| **C2 (20 %)** N3 | **teleoperación del brazo usando la estimación** | `python/teleop_camara.py` (en vivo) + `datos/teleop/` + `resultados/reales/teleop/` | ⏳ **grabar las 2 sesiones** (`docs/PRUEBA_FINAL.md`) |
| C2 N4–N5 | validación: crudo vs Kalman, tiempos de cómputo, latencia | `resultados/reales/teleop/resumen_teleop.md`, `configuraciones_q_camara.md`, `python/prueba_latencia_video.py` | ⏳ sale solo al grabar |
| **C3 (30 %)** | interpretar métricas, justificar Q, suavizar ≠ precisión, límites | `consistencia_kalman.md`, `11_innovaciones_nis.png`, `12_P_y_K.png`, `14_compromiso_Q_R.png`, esta guía §4 | ✅ |
| C3 N5 | fusión sensorial / rediseño | §4.5 (cámara + giroscopios; código preparado en `kalman_camara.py`) | ✅ (propuesta argumentada) |

---

## 2. Guion de 8 minutos (qué abrir, en este orden)

| Min | Abres | Dices (corto) |
|---|---|---|
| 0–1 | `docs/GUIA_ENTREGA2.md` §1 | "Hay dos Kalman: uno para las **IMU del robot** (la E2 clásica) y otro para la **cámara** (la teleoperación)." |
| 1–3 | `python/modelo_kalman.py` | Estado, F, H, Q, R, x0/P0 (§3.1). |
| 3–4 | `resumen_seleccion_Q.md` | Las 3 Q y la regla de selección (§3.2). |
| 4–5 | `15_validacion_comparacion_seno_rapido_02.png` + `metricas_e2_validacion_resumen.md` | Directa vs MM vs Kalman (§3.3). |
| 5–7 | **Demostración en vivo**: `teleop_camara.py` | El robot te copia; F = crudo ↔ Kalman; tapa la muñeca (§3.5). |
| 7–8 | `resumen_teleop.md` + `consistencia_kalman.md` | Tiempos, latencia, límites (§4). |

---

## 3. Qué decir en cada punto

### 3.1 El modelo (C1)

**Kalman de las IMU** (`modelo_kalman.py`, `kalman.py`):

- **Estado:** `x = [φ1, ω1, φ2, ω2]` = ángulo absoluto y velocidad de cada eslabón (°, °/s).
  Al final, θ1 = φ1 y θ2 = φ2 − φ1 (la IMU2 va montada sobre el eslabón 1).
- **F** (velocidad casi constante, con el **Δt real** de cada muestra, sacado del timestamp del ESP32):
  `[[1, Δt], [0, 1]]` por eslabón.
- **Q** = `q · [[Δt³/3, Δt²/2], [Δt²/2, Δt]]`: es lo que el modelo NO explica, como si un
  "empujón" de aceleración aleatoria cambiara la velocidad.
- **H** = `[[0,1,0,0], [0,0,0,1]]`: los giroscopios miden **solo ω**.
  Medición: `z = [w1 − b1, w2 − b2]`, con el sesgo b medido en el reposo inicial.
- **R** (de la E1, `estatico_03`): diagonal, σ = 0,030 y 0,033 °/s. La correlación entre las
  dos IMU es ρ = 0,00, por eso los términos fuera de la diagonal son 0.
- **x0:** φ0 = la consigna en el reposo inicial (la pose conocida) y ω0 = 0.
  **P0** = diag(2², 5²) por eslabón: ±2° de la pose y ±5 °/s, porque arranca quieto.
- **Ecuaciones** (`kalman.py`):
  - Predicción: `x⁻ = F x`, `P⁻ = F P Fᵀ + Q`.
  - Ganancia: `K = P⁻Hᵀ (H P⁻ Hᵀ + R)⁻¹`.
  - Actualización: `x = x⁻ + K (z − H x⁻)`.
  - P se actualiza con la **forma de Joseph**, `P = (I−KH) P⁻ (I−KH)ᵀ + K R Kᵀ`, que mantiene
    P simétrica y positiva. Asimetría medida: 10⁻²⁰; autovalor mínimo > 0 (`consistencia_kalman.md`).

**Kalman de la cámara** (`kalman_camara.py`): es el mismo filtro con otro sensor.
- Estado `[θ1, ω1, θ2, ω2]` y **H = `[[1,0,0,0], [0,0,1,0]]`**: la cámara mide el **ángulo**.
- R se mide con la tecla N (10 s con el brazo quieto).
- q = r·Δt·(2π f_n)⁴.
- **Medición parcial:** si la mano tapa la muñeca, H se queda solo con la fila de θ1. θ1 sigue
  medido y θ2 se predice.

### 3.2 Las 3 Q y su elección (C1, C3)

Cada Q se razona por la **frecuencia de corte** f_c que le da al filtro. Para ω con solo
giroscopio, el Kalman estacionario equivale a un paso bajo de primer orden:

    K = 1 − e^(−2π f_c Δt)      λ = K² / (1 − K)      q = λ · r / Δt

| Q | f_c | q [°²/s³] | Retraso ω medido (ajuste) | Ruido ω en reposo puro | Razón |
|---|---|---|---|---|---|
| Q_baja | 1,5 Hz | 0,00087 | **55 ms** ❌ | 0,0085 °/s | máxima suavidad, pero llega tarde |
| **Q_media** | 5 Hz | 0,0097 | **17,6 ms** ✅ | 0,0144 °/s | sigue el seno rápido (0,6–0,9 Hz) sin atenuarlo |
| Q_alta | 15 Hz | 0,093 | 4,7 ms ✅ | 0,0225 °/s | casi no filtra |

- **Regla fija, decidida ANTES de ver los resultados:** el menor ruido de ω entre las Q con
  retraso ≤ 40 ms. 40 ms porque en teleoperación los retrasos de más de ~50 ms se notan, y parte
  ya la gasta el servo. → **Q_media**.
- **Ajuste ≠ validación:** la Q se elige SOLO con los registros `_01` (ajuste), y la tabla de
  comparación sale de los `_02`/`_03` (validación). Así no se "hace trampa" con los mismos datos.
- Si preguntan por qué el retraso medido (17,6 ms) es menor que 1/(2π·5 Hz) = 32 ms: 32 ms es
  la aproximación de diseño a baja frecuencia. Kalman es un filtro **recursivo (IIR)** y su
  retraso **depende del movimiento**. La media móvil tiene fase lineal (retraso constante); por
  eso la MM sí coincide con su teoría: 19,7 y 98 ms medidos contra 20 y 100 ms teóricos.
  **Lo que manda en la regla es el valor medido.**

### 3.3 Comparación de métodos (C1) — validación, promedio de archivos y eslabones

| Método | Ruido ω en reposo puro | Retraso de ω | Retraso de θ | Ruido de α | Deriva final | Cómputo |
|---|---|---|---|---|---|---|
| Integración directa | 0,031 °/s | 0 | 0 | 12,0 °/s² | 1,47° | 5 µs |
| Media móvil N = 5 | 0,017 | 19,7 ms | 19,2 ms | 3,6 | 1,49° | 15 µs |
| Media móvil N = 21 | 0,009 | 98 ms | 98 ms | 0,9 | 1,61° | 17 µs |
| **Kalman Q_media** | **0,014** | **17,3 ms** | **3,8 ms** | **3,3** | 1,48° | 69 µs |

Qué decir:
- Kalman tiene **menos ruido que la MM5 y menos retraso**. La MM21 filtra más, pero llega
  **98 ms tarde**: inútil para teleoperar.
- **El ángulo θ de Kalman casi no se atrasa (3,8 ms frente a 19 ms de la MM5).** La razón: Kalman
  también corrige φ con la innovación del giroscopio, usando la covarianza cruzada φ–ω de P
  (`12_P_y_K.png`). La MM solo promedia y luego integra.
- **La deriva final es la misma en todos (~1,5°).** Ningún método la corrige, porque con solo
  giroscopio el ángulo no se mide (§4.2).
- **Cómputo:** 69 µs por muestra, frente a 10 ms entre muestras = 0,7 % del tiempo.

### 3.4 Aceleración angular numérica (C1)

`aceleracion_angular.md`: derivar divide por Δt = 10 ms, así que **el ruido se multiplica
por ~141**.
- Diferencia hacia atrás: teoría √2·σω/Δt = 6,6 °/s², medido 4,9.
- Diferencia central: teoría 3,3 °/s², medido 3,0. Es menos ruidosa, pero no es causal: necesita
  la muestra siguiente.
- **Kalman Q_media: 1,25 °/s²**, porque deriva una ω ya filtrada.
- En validación el ruido de α baja de 12,0 (directa) a 3,3 °/s² (Kalman).

### 3.5 Teleoperación usando la estimación (C2)

- **Qué es:** la cámara del teléfono ve tus 3 cuadros ArUco y calcula θ1 y θ2 de **tu** brazo.
  Kalman los estima y `modelo_a_servo(θ̂)` mueve el robot. La pantalla muestra en vivo las dos
  gráficas, crudo (naranja) contra Kalman (azul).
- **Validación en las mismas condiciones:** crudo y Kalman se calculan en **los mismos cuadros**.
  Además se graban 2 sesiones con el mismo protocolo (lento, rápido, tapar la muñeca), una con el
  robot movido por crudo y otra por Kalman.
- **Las 3 Q de la cámara** (`configuraciones_q_camara.md`, simulando el filtro real):

  | Q | f_n | Ruido | Temblor de 8 Hz | Retraso a 2 Hz |
  |---|---|---|---|---|
  | Q_baja | 1,5 Hz | ×0,53 | ×0,27 | 58 ms |
  | **Q_media** | 3 Hz | ×0,70 | ×0,49 | 16 ms |
  | Q_alta | 6 Hz | ×0,86 | ×0,83 | 2 ms |

  El movimiento voluntario va por debajo de 2 Hz y el temblor natural está entre 8 y 12 Hz.
  Q_media deja pasar el primero y reduce el segundo a la mitad.
- **Números que salen solos al grabar** (`resumen_teleop.md`): aspereza crudo vs Kalman, órdenes
  al servo, cambios de dirección del servo, oclusiones, cómputo por cuadro y retraso
  orden → robot y cámara → robot medidos con **los giroscopios del robot** (las IMU de la E1).
- **Referencia sintética, para saber qué esperar** (no son mediciones):
  - Kalman reduce la aspereza de θ1 0,81 → 0,50° y la de θ2 1,88 → 0,93°.
  - Con la muñeca tapada, el error de θ1 baja de 19° (cámara congelada) a 0,24°.
  - Detección + Kalman ≈ 3 ms por cuadro, el 9 % de los 33 ms entre cuadros.
- **Latencia del video:** `python python/prueba_latencia_video.py`. Antes, OpenCV acumulaba
  cuadros y el retraso pasaba de 2 s; ahora se mantiene en ~17 ms. La WiFi se mide con `ping`
  y por eso se usa el hotspot del teléfono.

---

## 4. Interpretación y límites (C3) — lo que más pesa

1. **Suavizar ≠ ser preciso.** Una curva más suave puede estar igual de corrida.
   - IMU: la deriva final es la misma en Kalman y en la integración directa (1,48° vs 1,47°).
   - Cámara (sintético): cuando la cámara ve bien, Kalman es más suave pero **no** más exacto
     (0,38° vs 0,33° de error). Su ventaja de exactitud aparece **en las oclusiones**.
2. **La deriva no es observable** con las IMU en el plano horizontal. H solo mide ω, y el
   acelerómetro no ve el ángulo porque la gravedad es perpendicular al plano. Por eso:
   - el sesgo se resta medido en reposo (deriva sin compensar +15,6 / −30,2 °/min; compensada
     +0,56 / −0,10 °/min);
   - Kalman **no** puede afirmar que corrige la deriva.
3. **Consistencia (NIS, `consistencia_kalman.md`):**
   - En reposo el NIS es ≈ 3,7 (seno_rapido_01), cerca del esperado (2).
   - En movimiento el NIS ≫ 2: el modelo de velocidad casi constante no explica las
     aceleraciones del servo ni su vibración.
   - Es la consecuencia de elegir Q por respuesta en frecuencia (retraso/ruido) y no por
     consistencia. En movimiento el NIS medio es ~10⁵ veces el esperado: una Q
     "consistente" tendría que ser muchísimo mayor y ya casi no filtraría.
     **Se declara como límite.**
4. **Q de la cámara y R:** como q = r·Δt·(2π f_n)⁴ es proporcional a r, la suavidad depende
   **solo de f_n**. La R medida (tecla N) decide cuánto confía el filtro en cada medición respecto
   a su predicción (la consistencia), no la suavidad.
5. **Fusión / rediseño (N5):**
   - La cámara mide θ sin deriva, pero tiembla y se tapa.
   - El giroscopio no tiembla, pero deriva.
   - Juntos se complementan: en `kalman_camara.py` bastaría agregar las filas de los giroscopios
     a H (`[0,1,0,0]`, `[0,0,0,1]`) y su varianza de la E1 a R. Con eso θ sería observable y la
     deriva se corregiría.
   - Otras opciones: un encoder en cada eje, o montar el brazo en plano vertical para que el
     acelerómetro vea la inclinación.
6. **Lo que no se puede verificar con estos datos:**
   - la latencia teléfono → PC por WiFi (se estima con `ping`);
   - la exactitud absoluta del brazo humano, porque no hay una "verdad" medida;
   - la perspectiva si el teléfono no está paralelo a la mesa.

---

## 5. Preguntas difíciles probables

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué Kalman si la MM21 tiene menos ruido? | Porque llega 98 ms tarde. Con la regla de ≤ 40 ms, la MM21 queda descartada. Kalman da menos ruido que la MM5 con menos retraso. |
| ¿Kalman corrige la deriva? | **No** con solo giroscopio: θ no se mide (H solo ve ω). La deriva final es igual en todos los métodos. |
| ¿Qué pasa si sube q? | El filtro confía más en la medición: menos retraso y más ruido (Q_alta: 4,7 ms y 0,022 °/s). |
| ¿Qué pasa si sube R? | Confía más en el modelo: más suave y más lento. En la cámara la suavidad no cambia, porque q ∝ r. |
| ¿Para qué sirve P? | Es la incertidumbre del estado. Decide K: P grande → K grande → confía en la medición. Crece en las oclusiones y por eso, al reaparecer el marcador, Kalman "salta" a la medición. |
| ¿Cómo sabe Kalman dónde está la muñeca tapada? | Por su modelo: sigue con la última velocidad estimada. Si la oclusión pasa de 0,2 s, frena esa velocidad para no seguir de largo. Y θ1 sigue medido. |
| ¿Por qué ArUco y no colores? | El blanco/negro se distingue con cualquier luz y cada cuadro "dice" su número. Con colores, el azul claro se perdía. |
| ¿Por qué el Δt real y no 1/fs? | Si se pierde una muestra, Δt = 20 ms. Con 1/fs el ángulo se correría. En la cámara el Δt varía de verdad (WiFi). |
| ¿Cómo separaron ajuste y validación? | El manifiesto automático asigna la 1.ª repetición válida a ajuste y la 2.ª a validación. La Q se elige solo con ajuste. |

## 6. Qué NO decir

- ❌ "Kalman elimina la deriva" (con solo giroscopio no puede).
- ❌ "Kalman es más preciso" sin decir respecto a qué: es más **suave** y tiene **menos retraso**
  que la MM; la exactitud absoluta no se mide.
- ❌ Presentar los números sintéticos como mediciones (están en `datos/sinteticos`, marcados).
- ❌ "El retraso es 32 ms": ese es el valor de diseño. **El medido es 17,6 ms.**
