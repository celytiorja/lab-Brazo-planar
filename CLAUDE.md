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

## Convenciones

- Pines: ver `docs/02_conexiones.md` (servos GPIO25/26, I2C GPIO21/22,
  IMU1=0x68 eslabón 1, IMU2=0x69 eslabón 2).
- Ángulos en grados en la interfaz; L1/L2 en mm en `python/parametros.py`.
- IMU2 mide el ángulo absoluto θ1+θ2 → θ2 = θ_IMU2 − θ_IMU1.
- Pruebas: `python -m pytest python/`.
