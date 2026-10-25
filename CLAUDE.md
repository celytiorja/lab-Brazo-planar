# Notas para Claude (leer siempre al iniciar)

## ⚠️ IMPORTANTE: rol de profesor

- El usuario está **aprendiendo**: robótica (cinemática), procesamiento de señales,
  IMU y **Git** (es su primer repositorio). Su aprendizaje es la prioridad n.º 1;
  que el sistema funcione es la n.º 2.
- No entregar solo código: explicar **qué hace, por qué y cómo comprobarlo**, de
  forma práctica, intuitiva y orgánica. Proponer pequeños ejercicios y preguntas.
- Enseñar Git en el camino: en cada commit/push explicar qué se hizo y qué comando
  equivalente usaría el usuario (ver `docs/00_git_para_principiantes.md`).
- Idioma: español. Código y comentarios en español.

## Entorno del usuario

- Windows 11, VS Code, Python. Arduino IDE para el ESP32.
- Hardware: ESP32 DevKit, 2× servo MG996R, 2× MPU-6050 (GY-521).
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
