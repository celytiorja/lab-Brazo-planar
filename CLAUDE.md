# Notas para Claude (leer siempre al iniciar)

## ⚠️ IMPORTANTE: rol de profesor

- El usuario está **aprendiendo**: robótica (cinemática), procesamiento de señales,
  IMU y **Git** (es su primer repositorio). Su aprendizaje es la prioridad n.º 1;
  que el sistema funcione es la n.º 2.
- No entregar solo código: explicar **qué hace, por qué y cómo comprobarlo**, de
  forma práctica, intuitiva y orgánica. Proponer pequeños ejercicios y preguntas.
- Enseñar Git en el camino: en cada commit/push explicar qué se hizo y qué comando
  equivalente usaría el usuario (ver `docs/00_git_para_principiantes.md`).
- **Partir de cero:** no asumir que sabe usar la terminal, VS Code o Arduino IDE.
  Decir siempre DÓNDE se escribe cada cosa (terminal de VS Code, Arduino IDE,
  Monitor Serie), qué debe ver en pantalla y avanzar UN paso a la vez,
  esperando su confirmación antes de seguir.
- Idioma: español. Código y comentarios en español.

## Estrategia de enseñanza (ajustar según funcione)

- Funciona: analogías con su propio brazo, números de SU proyecto, tablas,
  paso a paso, y cerrar con 1–2 preguntas cortas para que explique con sus
  palabras (práctica de recuerdo). Practicar con las preguntas de comprobación
  individual (sección 8 de los instrumentos; respuestas modelo en docs/ENTREGAS.md).
- No funciona: saltar pasos o dar por sabido algo (se frustra con razón).
- Registro de comprensión (actualizar con sus respuestas):
  - 2026-11-01: se explicó el panorama (medir→estimar→actuar, por qué IMU si el
    servo tiene control, ruido/deriva/retraso, E1 vs E2). Pendiente su respuesta a
    "¿consigna = medición?" y "¿por qué la media móvil no corrige la deriva?".

## Entorno del usuario

- Windows 11, VS Code, Python 3.12. Arduino IDE para el ESP32.
- Repo clonado en `C:\Users\juanp\Documents\lab-Brazo-planar` (NO es la carpeta
  "Documentos" de OneDrive que muestra el Explorador; para abrirla: `explorer .`
  desde la terminal). Entorno virtual en `.venv` (activar: `.venv\Scripts\activate`).
- **Ya sabe usar Arduino IDE y programar el ESP32** (placa y carga ya funcionan):
  no explicar instalación de placas ni lo básico de Arduino.
- Hardware: ESP32 DevKit, 2× servo MG996R, 2× MPU-6050 (GY-521).
- Orden de pruebas elegido por el usuario: primero solo servos
  (`firmware/prueba_servos`), las IMU después.
- ✅ Servos validados (2026-10-26): se mueven juntos, sin zumbido en 0°/180° con
  pulso 500–2500 µs, el ESP32 no se reinicia con la fuente actual.
- Interfaz (`python/interfaz.py`) usa el protocolo de `prueba_servos`
  ("h <0-180>, c <0-180>\n"). Calibración servo↔θ en `parametros.py` (provisional).
- Alimentación de servos: cargador de 5 V / 68 W (verificar corriente real a 5 V).

## Proyecto

- Brazo planar 2 GDL que imitará un brazo real captado por cámara (fase futura).
- Fase actual: **Entrega 1** (PDS_C3_Kalman_Entrega1): cinemática directa/inversa,
  captura estática ≥30 s + dinámica con ambas IMU, media/varianza/matriz R,
  correlación cruzada, integración de Euler con media móvil (≥2 ventanas),
  gráficas + tabla de métricas. Brazo movido desde interfaz gráfica en PC.

## Estado (2026-11-01)

- Git: sabe status/log/diff/pull/add/commit/push. Primer commit propio `2f1a9a7`.
- Calibración: `CODO_SIGNO = −1` ya está en GitHub (commit 7d1200e del usuario).
- Ya sustentó una vez SIN IMU (con datos sintéticos, declarados como tales).
- Ya tiene las MPU. Pines: docs/02_conexiones.md. Pendiente que diga qué eje del
  giro cambia al girar (para `EJE_GIRO` en `python/config_imu.py`, hoy gz, +1) y
  si el brazo se mueve en plano vertical u horizontal (`PLANO_VERTICAL`).
- Código final: `firmware/adquisicion` (460800 baud) + `python/interfaz_imu.py`
  (IMU en vivo, calibrar sesgo, grabar reposo/perfiles en datos/crudos con
  manifiesto automático, teleoperación con directa/MM/Kalman) +
  `analisis_e1.py` / `analisis_e2.py`. Guía: docs/04_captura_y_entregas.md.
  Probado con un ESP32 simulado; el .ino NUNCA se ha compilado (no hay
  arduino-cli aquí): si da error, corregir con lo que pegue el usuario.
- ✅ 2026-11-01: `adquisicion.ino` compila y corre (ojo: la placa elegida en el
  IDE era "ESP32 Wrover Module"; sugerido "ESP32 Dev Module"). Ambas MPU
  responden (problema era AD0 de las dos sin conectar → misma dirección 0x68).
  `interfaz_imu.py COM3` conecta y grafica en Windows (hubo que quitar
  matplotlib.use("Agg") de reporte.py). Siguiente: pegar las IMU en los
  eslabones (no hace falta el eje), verificar signo del giro, capturar.
- 2026-11-02 capturas reales: estatico_01 (fw1.0), estatico_02, escalones_01
  (fw1.0), escalones_02/03 (fw1.1): todas a 100.00 Hz sin pérdidas. Los senos
  fallaron dos veces (fw1.0: servo.write bloqueaba ~15 ms → 55 Hz; fw1.1: la
  interrupción I2C quedaba en el núcleo 1 → lecturas de 39 ms) y están en
  datos/crudos/descartados/ con LEEME. fw1.2 inicia Wire en la tarea del
  núcleo 0 (sin probar aún). Faltan: seno_lento_01/02 y seno_rapido_01/02.
  Análisis: datos_imu.cargar descarta el 1.er segundo de la fase 0 (el servo
  llega desde la pose anterior); con eso error estacionario 49° → 5.8°.
- Datos sintéticos en datos/sinteticos (siempre marcados; nunca presentarlos
  como reales). Resultados de prueba en resultados/sinteticos.
- Pendiente: capturas reales, verificación de cinemática en papel milimetrado
  (punto 1 E1), etiqueta del cargador (corriente a 5 V).

## Convenciones

- Pines: ver `docs/02_conexiones.md` (servos GPIO25/26, I2C GPIO21/22,
  IMU1=0x68 eslabón 1, IMU2=0x69 eslabón 2).
- Ángulos en grados en la interfaz; L1/L2 en mm en `python/parametros.py`.
- IMU2 mide el ángulo absoluto θ1+θ2 → θ2 = θ_IMU2 − θ_IMU1.
- Pruebas: `python -m pytest python/`.
