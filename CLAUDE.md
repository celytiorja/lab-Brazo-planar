# Notas para Claude (leer SIEMPRE completo al iniciar)

Última actualización: 2026-11-08 (revisión final E2: panel, q cámara corregida, guía). Rama de trabajo: `claude/friendly-feynman-xfljpf`
(repo `celytiorja/lab-Brazo-planar`, es la única rama; el usuario también hace commits
en ella con el autor "Cely"). Commits: mensaje en español + líneas de co-autoría.

## 1. ⚠️ Rol: PROFESOR (lo más importante)

- El usuario está **aprendiendo** robótica (cinemática), PDS, IMU, Kalman y **Git** (su
  primer repositorio). Prioridad n.º 1: que aprenda. N.º 2: que funcione.
- No entregar solo código: explicar **qué hace, por qué y cómo comprobarlo**, de forma
  práctica e intuitiva. Al cerrar, 1–2 preguntas cortas para que responda con sus palabras.
- **Partir de cero** en herramientas: decir SIEMPRE DÓNDE se escribe cada cosa (terminal de
  VS Code, Arduino IDE, Monitor Serie), qué debe ver en pantalla, y avanzar UN paso a la vez
  esperando su confirmación. Se frustra (con razón) si se saltan pasos.
- **Ya sabe Arduino IDE** y cargar el ESP32: no explicar lo básico de Arduino.
- Idioma: español. Código y comentarios en español, con el estilo didáctico del repo.
- Enseñar Git en el camino: explicar cada commit/push y el comando equivalente.

### Estrategia que funciona / no funciona
- ✅ Funciona: analogías con su propio brazo u objetos cotidianos (pesa que marca 1 kg de
  más = sesgo; alcancía = deriva; videojuego = commits; dos oficinas/teléfono = núcleos e
  interrupción I2C), **números de SU proyecto**, tablas, diagnóstico "eslabón por eslabón"
  de una cadena, programas pequeños que imprimen todos los números (`kalman_paso_a_paso.py`).
- ❌ No funciona: saltar pasos, dar por sabido, bloques largos de teoría sin aplicación
  (dijo: "el concepto perfecto, pero aplicarlo realmente es diferente").
- Pidió explícitamente aprender la teoría "bien" más adelante (cuando no esté apurado).

### Registro de comprensión (actualizar con sus respuestas)
- ✅ "¿Consigna = medición?" → respondió "la consigna es un deseo, no una medición".
  Reforzar con un ejemplo propio (escalones_02: el hombro no obedeció).
- ❌→explicado: "¿por qué la media móvil no corrige la deriva?" No lo sabía (no ha visto
  teoría). Se explicó con sesgo vs ruido (pesa), promedio y suma → deriva.
- Kalman explicado desde cero (predecir/medir/mezclar, K, P, Q vs R, 6 decisiones de diseño)
  con `python/kalman_paso_a_paso.py` (1 variable; K converge a 0.27 con q = 0.0359).
- Entiende Git básico: status, log --oneline, diff, pull, add, commit, push, restore,
  git ls-files; sabe salir del visor `less` con `q`; sabe que un commit guarda solo cambios.
- Preguntas que quedaron SIN responder (retomarlas en algún momento, sin agobiar):
  1. Pesa con +2 kg de sesgo y ±0.1 de ruido, 100 pesadas promediadas: ¿qué da? ¿cómo
     obtener el peso real?
  2. En `kalman_paso_a_paso.py` con q = 0.001: ¿alcanza más rápido o más lento el salto?
  3. ¿Por qué no elegimos la media móvil N=21 si tiene menos ruido que Kalman? (retraso 98 ms)
  4. ¿Qué "sabe" Kalman para predecir la muñeca tapada? (modelo de velocidad constante)
  5. 17 °/min de deriva sin calibrar → en 5 min, ¿cuánto creería que giró? (~85°)

## 2. Entorno del usuario

- Windows 11, VS Code, Python 3.12, Git 2.56 (ya autenticado con GitHub en Windows).
- Git: `user.name "Cely"`, `user.email "juanchometroio@gmail.com"` (el de sus commits; NO
  usar el correo de la cuenta de Claude). 2026-11-08: **cambió de computador** (sin código):
  se le dio la guía de instalación (Git, Python 3.12 con PATH, VS Code, clone, venv, pip,
  pytest, COM en el Administrador de dispositivos: puede no ser COM3). Nuevo PC: usuario
  Windows `anama`; repo en `C:\Users\anama\Desktop\Juan\lab señales\lab-Brazo-planar`
  (ruta con ESPACIO: usar comillas en la terminal).
- Repo en `C:\Users\juanp\Documents\lab-Brazo-planar` (NO la carpeta "Documentos" de
  OneDrive; para abrirla: `explorer .` desde la terminal).
- Entorno virtual `.venv` (activar: `.venv\Scripts\activate`; la línea debe empezar con
  `(.venv)`). Dependencias: `pip install -r requirements.txt` (incluye scipy y opencv-python).
- ESP32 en **COM3**. En Arduino IDE tenía elegida "ESP32 Wrover Module" (sale aviso de
  PSRAM, inofensivo); se sugirió "ESP32 Dev Module".
- Monitor Serie: 115200 para `prueba_servos`/`prueba_hardware`; **460800** para
  `adquisicion`. Debe estar CERRADO cuando Python usa el puerto.
- Teléfono con **DroidCam**; IP actual del teléfono **192.168.1.38**, puerto **4747**.
  Ping desde el PC responde pero con 250–550 ms (WiFi lenta/ahorro de energía; para baja
  latencia se recomendó el hotspot del teléfono). DroidCam atiende a UN cliente a la vez
  (cerrar el navegador antes de correr Python). Ya ve la cámara en el navegador.

## 3. Hardware

- ESP32 DevKit, 2× servo MG996R, 2× MPU-6050 (GY-521), fuente 5 V (cargador USB 68 W;
  sin confirmar la corriente real a 5 V; no ha habido reinicios).
- Pines (docs/02_conexiones.md): servo hombro GPIO25, codo GPIO26; I2C SDA GPIO21,
  SCL GPIO22 (las dos IMU en el mismo bus). 2026-11-10: ESP32 nuevo. Un error de subida decía "ESP32-S3" (tenía
  elegida la placa S3 en el IDE) y se asumió S3 → firmware v1.3 elige pines solo
  (`#if CONFIG_IDF_TARGET_ESP32S3`: S3 = servos 4/5, I2C 8/9). PERO la línea `# cfg` de
  la v1.4 confirmó **placa=ESP32 clásico, pines 25/26 y 21/22** (los de siempre), COM3,
  chip USB CP210x. Subir: BOOT presionado hasta "Writing", luego EN; Upload Speed 115200.
  En interfaz_imu (con v1.3) salieron `error_i2c` sueltos (imu1) y "perdidas 12" al mover
  servos → **firmware v1.4**: I2C 100 kHz, timeout 5 ms, 3 reintentos, reinicio del bus
  + IMU tras 5 fallos (`# i2c_reiniciado`); `# cfg` informa i2c_hz, reintentos y
  reinicios. v1.4 cargada: imu1_ok=1 imu2_ok=1. Pendiente: θ1 estimado más corto que la
  consigna en un escalón (45° de 63°): comprobar físicamente el hombro. IMU1 = 0x68 (AD0 a GND/sin conectar) en el
  eslabón 1; IMU2 = 0x69 (**AD0 a 3V3**) en el eslabón 2. GND de la fuente unido al ESP32.
  (Problema resuelto: con los dos AD0 sin conectar ambas eran 0x68 → NACK.)
- L1 = 105 mm, L2 = 85 mm (de eje a eje). Calibración en `python/parametros.py`:
  HOMBRO_OFFSET 0, SIGNO +1; CODO_OFFSET 90, **CODO_SIGNO −1** (servo del codo montado al
  revés; ya en GitHub). Offsets aún provisionales (falta verificación en papel).
- IMU pegadas en los eslabones del robot (la posición en el eslabón no importa para el
  giroscopio). `EJE_GIRO` = gz, signo +1 en ambas (los datos reales siguen a la consigna).
- **Brazo en plano HORIZONTAL** (sobre la mesa) → `PLANO_VERTICAL = False`: el
  acelerómetro no ve el ángulo; la deriva NO es observable con IMU solas (declararlo).

## 4. Proyecto y entregas (instrumentos PDS Lab, corte 3, v2.0)

- Objetivo final: brazo planar 2 GDL que copia en tiempo real un brazo humano.
- **Entrega 1** (C1 40 % métodos base, C2 40 % ejecución/trazabilidad, C3 20 %
  interpretación; evidencias E1–E4): cinemática directa/inversa con posiciones de
  referencia y errores, reposo ≥ 30 s + dinámico repetible con ambas IMU, media/varianza/R,
  correlación cruzada, Euler + media móvil (≥ 2 ventanas), gráficas + ≥ 2 métricas.
- **Entrega 2** (C1 50 % modelo/implementación Kalman, C2 20 % validación y demostración,
  C3 30 % interpretación y Q; evidencias E5–E9): estado, F, H, Q, R (de E1), x0/P0,
  ≥ 3 Q razonadas con ajuste/validación separados, comparación directa/MM/Kalman,
  aceleración angular numérica, **teleoperación del brazo usando la estimación** (C2-N3 lo
  exige; sin ella C2 queda en N2), límites de lo verificable. N5: tiempos de cómputo,
  latencia, contraste teleoperar crudo vs Kalman; fusión sensorial / rediseño.
- Localizadores de evidencias y respuestas modelo a las preguntas individuales:
  `docs/ENTREGAS.md`. Guía para hablar con los números reales: `docs/SUSTENTACION.md`.
- Ya sustentó una vez SIN IMU (con datos sintéticos, declarados como tales).

## 5. Código (qué es cada cosa)

Firmware (`firmware/`):
- `prueba_servos/` (115200, "h 90, c 45", varias órdenes por coma).
- `prueba_hardware/` (escáner I2C + IMU + servos, 115200).
- `adquisicion/` **v1.2** (460800): tarea de muestreo FreeRTOS en el **núcleo 0** con
  `vTaskDelayUntil` 10 ms, **Wire.begin dentro de esa tarea** (interrupción I2C en el
  núcleo 0), cola de muestras; loop() en núcleo 1: órdenes (h/c/s/p/x/?), perfiles
  (1 escalones, 2 seno lento, 3 seno rápido; 3 s reposo + mov + 3 s reposo), servos
  máx. 1 escritura/20 ms, envío "D,seq,t1_us,t2_us,perfil,fase,cmd_h,cmd_c,ax1..gz2".

Python (`python/`), todo se ejecuta desde la raíz con `python python/<archivo>.py`:
- Cinemática: `cinematica.py`, `simulador.py` (VistaBrazo reutilizable), `interfaz.py`
  (mueve el robot con prueba_servos), `servos.py`, `parametros.py`,
  `verificacion_cinematica.py` (`--plantilla` crea la hoja de 10 puntos ×2).
- Captura: `interfaz_imu.py` (IMU en vivo con blitting, botones: Ir a posición de inicio,
  Calibrar sesgo, Grabar reposo 40 s, Perfiles 1–3, Grabar libre; "Mover el brazo con"
  sliders/directa/MM/Kalman; sube cada captura sola), `tiempo_real.py`, `grabador.py`
  (CSV + JSON + manifiesto), `sincronizar.py` (add → commit → `pull --no-rebase -X ours` →
  rehace manifiesto → push), `conexion.py`, `blit.py`, `config_imu.py`.
- Análisis: `datos_imu.py` (descarta el 1.er s de la fase 0), `estimadores.py`
  (IntegracionDirecta, MediaMovilIntegracion, KalmanBrazo), `kalman.py` (Joseph, NIS),
  `modelo_kalman.py`, `config_kalman.py` (Q por frecuencia de corte 1.5/5/15 Hz a partir de
  R; RETRASO_MAX 40 ms), `metricas.py`, `validar_datos.py` (incluye "el brazo medido sigue
  a la consigna"), `analisis_e1.py` + `analisis_e1_extra.py`, `analisis_e2.py` (ruido de
  ω medido en REPOSO PURO; selección = menor ruido con retraso ≤ 40 ms), `reporte.py`
  (el manifiesto real se regenera solo al analizar).
- Teleoperación con cámara: `teleop_camara.py` (`--modo aruco|color`), `vision.py`
  (DetectorAruco por defecto: cuadros impresos DICT_4X4_50, ID 0 hombro / 1 codo / 2 muñeca,
  esquinas sub-píxel; DetectorColor = respaldo HSV con clic), `generar_marcadores.py`
  (crea `docs/marcadores_aruco.pdf`, 6 cm + repuestos de 4 cm, regla de 10 cm; imprime el
  patrón para dibujarlo a mano), `kalman_camara.py` (estado [θ1, ω1, θ2, ω2], H mide θ,
  **q = r·Δt·(2π f_n)^4** (2026-11-08: antes faltaba Δt y el filtro quedaba ~2.3× más rápido
  de lo nombrado, casi sin filtrar; `caracterizar_q` simula el filtro real) con
  f_n 1.5/3/6 Hz (ruido ×0.53/0.70/0.86; temblor 8 Hz ×0.27/0.49/0.83; retraso a 2 Hz
  58/16/2 ms), predice si no ve; **medición parcial**: NaN en θ2 → H solo con la fila
  de θ1; tras PREDICCION_LIBRE_S 0.2 s sin medir, la ω se frena con τ 0.15 s),
  `config_camara.py`, `video_rapido.py` (LectorVideo: hilo que guarda solo el cuadro más
  nuevo; para http lee el MJPEG directo con urllib buscando FFD8/FFD9 y decodifica solo el
  que se usa; respaldo cv2 con nobuffer; archivos a velocidad real), `analisis_teleop.py`
  (E8; se ejecuta y sube solo al salir con Q si hubo sesiones), `simular_teleop.py` (video
  sintético con verdad, temblor 9 Hz, JPEG, desenfoque, 2 oclusiones; procesa el MISMO
  video con crudo y Kalman; simula robot con retraso 120 ms + τ 70 ms y giroscopio),
  `prueba_latencia_video.py` (DroidCam falso: antes 75→2205 ms, ahora 15→17 ms).
  vision.DetectorAruco también **sigue por cercanía** candidatos rechazados (desenfoque) hasta
  8 cuadros (`ARUCO_SEGUIR_*`).
- Pantalla de teleop (2026-11-08): `panel_teleop.py` (video 640×480 + panel 300 px: fps,
  marcadores H/C/M, θ crudo/Kalman, 2 gráficas en vivo 6 s, robot `fw 1.2 IMU ok`, Q, R,
  teclas; pista amarilla del siguiente paso; banda REC con guía). `teleop_camara.py`:
  clase Robot (lee `# cfg`, arranque suave 1.5 s a 4°/orden desde 90/90, errores sin
  traceback), `--video IP` se completa, `--puerto auto`, tecla M espejo, teclas sin
  importar mayúsculas, cerrar con la X termina, mensajes temporales, Kalman se reinicia si
  pasan > 0.7 s sin video. `video_rapido.py` se reconecta solo (MJPEG sin proxy).
  `sincronizar.py`: GIT_TERMINAL_PROMPT=0 + timeout 120 s (no cuelga pidiendo contraseña).
  `analisis_teleop.py`: omite sesiones < 1 s o dañadas; tabla `configuraciones_q_camara.md`.
- Aprendizaje: `kalman_paso_a_paso.py`. Sintéticos: `generar_datos_sinteticos.py`,
  `perfiles.py` (copia de los perfiles del firmware).
- Pruebas: `python -m pytest python/` → **36 pasan**. Pruebas de punta a punta (no en el
  repo): DroidCam falso (MJPEG) + ESP32 falso en un pty, con teclas simuladas: OK.
- Docs: **`docs/GUIA_ENTREGA2.md`** (cada criterio E2 con evidencia, guion de 8 min, qué
  decir con números reales, preguntas difíciles, qué NO decir), `docs/PRUEBA_FINAL.md`,
  `docs/00_git…`, `01_cinematica`, `02_conexiones`, `03_interfaz`,
  `04_captura_y_entregas`, `05_teleoperacion_camara`, `ENTREGAS`, `SUSTENTACION`;
  `datos/DICCIONARIO.md`; `datos/crudos/descartados/LEEME.md`.

## 6. Datos reales (datos/crudos) y lo que se descubrió con ellos

- Capturas: estatico_01 (fw1.0), estatico_02, estatico_03 (fw1.1); escalones_01 (fw1.0),
  escalones_02/03/04 (fw1.1), escalones_05 (fw1.2); seno_lento_01/02 y seno_rapido_01/02
  (fw1.2). Todas 100.00 Hz, 0 pérdidas.
- Manifiesto automático (reglas fijas, `grabador.actualizar_manifiesto`):
  - Reposo para R = 1.º estacionario (Levene p > 0.05 en w1 y w2) → **estatico_03**
    (01 y 02 tenían movimientos: p ≈ 1e-36, ρ w1–w2 ≈ 0.85).
  - Perfiles = solo repeticiones que pasan `validar_datos`; ajuste = 1.ª válida,
    validación = 2.ª válida. **escalones_02 rechazada** (amplitud medida/consigna 0.47: el
    hombro NO se movió). Ajuste: escalones_01, seno_lento_01, seno_rapido_01. Validación:
    escalones_03, seno_lento_02, seno_rapido_02.
- `descartados/`: senos con fw1.0 (servo.write bloqueaba ~15 ms → 55 Hz) y fw1.1 (la
  interrupción I2C quedaba en el núcleo 1 → lecturas de 39 ms, 96–99 Hz). Documentado.
- Arranque de perfil: el servo venía de otra pose y se movía en el "reposo inicial" →
  sesgo y condición inicial malos (error 49°); se descarta el 1.er s (error 5.8°).
- Resultados reales (resultados/reales/e1, e2):
  - σ giro reposo 0.030 / 0.033 °/s; R diagonal (ρ = 0.00); sesgo ≈ +0.26 / −0.50 °/s.
  - Deriva sin compensar +15.6 / −30.2 °/min; compensada +0.56 / −0.10 °/min.
  - Retraso consigna → brazo ≈ 190 ms (servo). MM5/MM21: 20/98 ms (teoría 20/100).
  - Q elegida **Q_media** (f_c 5 Hz, q = 0.0097). Ruido ω reposo puro: directa 0.031,
    MM5 0.017, **Kalman 0.014**, MM21 0.009 °/s. Retraso ω (validación): MM5 19.7,
    **Kalman 17.3**, MM21 98 ms. Ruido α: directa 12.0 vs Kalman 3.3 °/s².
  - NIS en reposo ≈ 3.7 SOLO en seno_rapido_01 (en escalones/seno_lento el "reposo" da
    100–2000); en movimiento ~10⁵–10⁶ (modelo de velocidad no explica el servo): límite
    declarado (Q elegida por frecuencia, no por consistencia).
  - Retraso ω medido 17.6 ms (ajuste) vs 32 ms de diseño 1/(2πf_c): Kalman es IIR (retraso
    depende del movimiento); la MM (fase lineal) sí coincide con su teoría. Retraso de θ del
    Kalman 3.8 ms (corrige φ con la covarianza cruzada φ–ω) vs 19 ms MM5.
  - Aviso: el acelerómetro ay2 satura unas pocas muestras en los arranques de escalones.

## 7. Teleoperación (Entrega 2) — código listo, faltan las sesiones reales

- Decisión (2026-11-02): **opción 1 = solo cámara del teléfono** (DroidCam), el maestro es
  el brazo del usuario, vista desde ARRIBA de la mesa; IMU siguen en el robot. Opción 2
  (fusión cámara + giroscopios en el brazo humano) queda abierta según el profesor; el
  código está preparado (agregar filas de giro a H y R en `kalman_camara.py`).
- Marcadores: primero se probaron papeles de color (hombro azul, codo verde, muñeca fucsia).
  2026-11-03: el usuario reportó que el **azul claro del hombro casi no se detectaba** y pidió
  algo más robusto ("colores con recuadros") → se cambió a **ArUco** (modo por defecto).
  Imprimir `docs/marcadores_aruco.pdf` a tamaño real, cuadros de 6 cm con margen blanco,
  sobre cartón. Si el hombro no se ve, se usa su última posición (`RECORDAR_HOMBRO`).
  Tecla D = diagnóstico (dibuja en rojo los candidatos no leídos). Colores: `--modo color`.
- Comando: `python python/teleop_camara.py --video http://192.168.1.38:4747/video`
  (+ `--puerto COM3` para mover el robot; arranca en PAUSA, tecla R). Teclas: D diagnóstico
  ArUco, L colores (solo `--modo color`: clic hombro, codo, muñeca), C pose de referencia (brazo estirado al frente = (90, 0)),
  N medir R de la cámara (10 s quieto), F crudo↔Kalman, 1/2/3 Q, G grabar (datos/teleop,
  se sube solo), Q salir.
- 2026-11-03 (noche antes de entregar E2): el usuario reportó que con la cámara real el
  programa era **muy lento y se trababa** → causa: cv2.VideoCapture acumulaba cuadros (retraso
  creciente) + WiFi lenta. Arreglado con `video_rapido.py`; se recomienda el **hotspot del
  teléfono** (la IP de DroidCam cambia). No alcanzó a imprimir los ArUco: imprime y entrega
  el mismo día. Se dejó TODO listo para una prueba de 10 min: **`docs/PRUEBA_FINAL.md`**
  (protocolo: C, N, R; sesión 1 F=crudo y sesión 2 F=Kalman, 30 s cada una con guía en
  pantalla: lento/rápido/tapar muñeca; Q analiza y sube; luego `git tag entrega2`).
- Sesiones: `datos/teleop/sesion_XX.csv` (t_s, visto, solo_theta1, hombro_memoria, θ crudo y
  kf, ω kf, fuente, enviando, cmd, enviado, t_calc_kf_us, t_proc_ms, t_espera_ms) +
  `sesion_XX_robot.csv` (giroscopio del robot a 100 Hz; teleop manda "s 1" al conectar).
- Sintético (resultados/sinteticos/teleop, con q corregida): aspereza θ1 0.81→0.50, θ2
  1.88→0.93 (mismos cuadros); vs verdad en cuadros vistos Kalman NO es más exacto (0.38 vs
  0.33°: suavizar ≠ precisión); error θ1 en oclusión 19°→0.24° (medición parcial); Kalman
  ~0.25 ms, detección + Kalman ~3 ms (9 % de 33 ms); retraso orden→robot ≈ 175 ms
  recuperado del giroscopio. La métrica de "vibración del robot" no es concluyente.
- SIGUIENTE: que el usuario corra la prueba real y revisar `resultados/reales/teleop/`.
- 2026-11-10: teleop REAL funciona (el robot copia). Ya grabó sesion_01 (Kalman, 65 s, a
  ~4.8 fps por WiFi de casa); σ θ1 de R = 2.42° (repetir N quieto). Va a grabar crudo +
  Kalman de 30 s. Carpeta local "entrega2.2.0" (video + foto) aún NO subida.
- 2026-11-10 tarde: sesiones REALES subidas (hotspot iPhone 172.20.10.2, 11–15 fps; R cámara
  σ 0.73/0.64°). sesion_01 kalman 74 s, sesion_02 7 s sin robot (prueba), **sesion_03 CRUDO**
  y **sesion_04 KALMAN** (las buenas, según el usuario). Aspereza crudo→Kalman: s03 θ1
  0.86→0.67, θ2 2.20→1.65; s04 0.99→0.72, 2.82→2.09 (−22 a −27 %), retraso 5–10 ms; Kalman
  ~265 µs, detección+Kalman 6.5 ms. Robot: orden→robot 185–200 ms (hombro), 170–175 (codo).
  ⚠️ **IMU1 (hombro) del robot dejó de responder** a los 37.8 s de s03 y toda s04 (w1 = 0.000
  exacto) → `primera_falla_imu` en analisis_teleop las descarta; s04 sin métricas de robot.
  Pedir al usuario revisar el cable/soldadura de la IMU1 (0x68) antes de la demo.
- Informe: `python/generar_informe.py` → `docs/informe/Informe_Entrega2.docx/.pdf`
  (teleop marcada SINTÉTICA hasta que haya sesiones reales; `--foto RUTA`). El instrumento
  v2.0 dice que el informe NO se califica (0 %). Guía para el profesor: `docs/LOCALIZADORES_E2.md`.
- El usuario subió `Rubricas_Lab_3.pdf` (minisumo, EKF/UKF, informe IEEE): confirmó que
  NO aplica, ignorarla.

## 8. Pendientes (en orden)

1. Grabar las 2 sesiones reales de teleoperación con `docs/PRUEBA_FINAL.md` (E8, C2).
2. Verificación de la cinemática en papel milimetrado (`verificacion_cinematica.py
   --plantilla`, docs/04 §4b): punto 1 de E1 y referencia independiente de E2.
3. Practicar las preguntas de comprobación individual (docs/ENTREGAS.md).
4. Llenar los instrumentos (equipo, códigos, commit/tag `entrega1`/`entrega2`).
5. (Opcional) Opción 2 de fusión cámara + IMU si el profesor lo pide.
- Menores: confirmar corriente del cargador a 5 V; elegir "ESP32 Dev Module".

## 9. Trampas conocidas (no repetir)

- No poner `matplotlib.use("Agg")` en módulos que importa la interfaz (solo en scripts de
  análisis): la ventana no se abre.
- Redibujar la figura completa tarda ~230 ms: usar blitting (`blit.py`).
- El usuario a veces graba sin haber hecho `git pull` → nombres/versiones viejas; revisar la
  versión de firmware en el JSON de cada captura.
- Si el pull choca por `manifiesto.json`: `git restore datos/crudos/manifiesto.json` y
  repetir (o usar la subida automática, que lo resuelve sola).
- Nunca presentar datos sintéticos como reales (están en datos/sinteticos, marcados).
- No borrar datos del usuario: mover a `descartados/` con explicación.
- El .ino no se puede compilar aquí (no hay arduino-cli): revisar a mano y pedir errores.
- En OpenCV 5 el texto de `putText` con grosor 3 sale más ancho que con grosor 1: el truco
  de "contorno negro + texto blanco" se ve ilegible. Usar `_texto()` (fondo oscuro) de
  `teleop_camara.py`.
