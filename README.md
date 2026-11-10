# Brazo planar 2 GDL: PDS C3 (Kalman), Entrega 1

Brazo planar de dos articulaciones (hombro y codo) que, en la fase final, imitará en
tiempo real el movimiento de un brazo humano captado por cámara. En esta etapa el
brazo se mueve desde una interfaz gráfica en el PC y se caracterizan las dos IMU.

**Hardware:** ESP32 DevKit · 2× servo MG996R · 2× MPU-6050 (GY-521) · fuente 5 V.

## Estructura

```
docs/
  00_git_para_principiantes.md   ← empieza aquí si es tu primera vez con Git
  01_cinematica.md               ← teoría de cinemática directa e inversa
  02_conexiones.md               ← pines, diagrama y alimentación
  03_interfaz.md                 ← cómo funciona la interfaz y la calibración
  04_captura_y_entregas.md       ← capturar datos reales y generar E1 y E2
  05_teleoperacion_camara.md     ← el robot copia tu brazo (cámara del teléfono)
  SUSTENTACION.md                ← qué mostrar y qué decir
  ENTREGAS.md                    ← localizadores E1–E9 y respuestas de comprobación individual
  PRUEBA_FINAL.md                ← ⭐ los 10 minutos antes de entregar la E2 (teleoperación)
  GUIA_ENTREGA2.md               ← ⭐ cada criterio de la E2: evidencia, qué decir, preguntas
  LOCALIZADORES_E2.md            ← ⭐ texto para el instrumento E2: archivo de cada evidencia y nivel
firmware/
  prueba_servos/                 ← sketch para probar solo los dos servos
  prueba_hardware/               ← sketch para probar servos + IMU juntos
  adquisicion/                   ← firmware final: 2 IMU a 100 Hz + servos + perfiles
python/
  parametros.py                  ← L1, L2 y calibración de los servos
  cinematica.py                  ← cinemática directa e inversa
  servos.py                      ← traducción θ del modelo ↔ ángulo del servo
  conexion.py                    ← comunicación serie con el ESP32
  simulador.py                   ← simulador interactivo (sin hardware)
  interfaz.py                    ← interfaz gráfica que mueve el brazo real (sin IMU)
  interfaz_imu.py                ← interfaz con las IMU en vivo y grabación de capturas
  teleop_camara.py               ← teleoperación con cámara + Kalman (vision.py, kalman_camara.py)
  generar_marcadores.py          ← hoja de cuadros ArUco para imprimir (docs/marcadores_aruco.pdf)
  video_rapido.py                ← lectura del video sin retraso acumulado (se reconecta solo)
  panel_teleop.py                ← pantalla de la teleoperación (panel + gráficas en vivo)
  analisis_teleop.py             ← E8: crudo vs Kalman, oclusiones, tiempos, retraso del robot
  simular_teleop.py              ← prueba completa con video sintético (verdad conocida)
  prueba_latencia_video.py       ← mide por qué "se trababa" (antes 2 s, ahora ~17 ms)
  generar_informe_ieee.py        ← informe de la Entrega 2 en formato IEEE (docs/informe/Informe_Entrega2_IEEE.docx/.pdf)
  generar_informe.py             ← lectura de resultados para el informe (y versión larga no IEEE)
  analisis_e1.py / analisis_e2.py← resultados de la Entrega 1 y 2 (Kalman)
  analisis_e1_extra.py           ← sensibilidad, sesgo, Δt, estructura de R, repetibilidad...
  verificacion_cinematica.py     ← punto 1: error del brazo real medido en papel
  validar_datos.py               ← integridad automática de las capturas crudas
  kalman.py, modelo_kalman.py    ← filtro de Kalman y modelo del brazo
  estimadores.py, metricas.py    ← directa / media móvil / Kalman y métricas
  test_*.py                      ← pruebas automáticas
datos/DICCIONARIO.md             ← columnas, unidades, sensor, eje y articulación
datos/sinteticos/                ← datos de PRUEBA (no son mediciones)
datos/crudos/                    ← capturas reales (las crea interfaz_imu.py)
resultados/<origen>/e1, e2/      ← gráficas y tablas generadas por código
requirements.txt                 ← dependencias de Python
```

## Puesta en marcha (Windows 11 + VS Code)

### Python

```
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest python/          # deben pasar todas las pruebas
python python/simulador.py        # simulador interactivo
python python/interfaz.py         # mover el brazo real (ESP32 con prueba_servos)
```

Un *entorno virtual* (`.venv`) es una instalación de Python solo para este proyecto,
para que sus librerías no choquen con las de otros proyectos. Si PowerShell no deja
ejecutar `activate`, ejecuta una vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### ESP32 (Arduino IDE)

1. `Archivo → Preferencias → URLs adicionales de gestor de placas`:
   `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
2. `Herramientas → Placa → Gestor de placas` → instalar **esp32** (Espressif).
3. `Herramientas → Gestionar librerías` → instalar **ESP32Servo** (Kevin Harrington).
4. Abrir `firmware/prueba_hardware/prueba_hardware.ino`, elegir placa
   **ESP32 Dev Module** y el puerto COM, y subir.
5. Abrir el Monitor Serie a **115200** baudios con fin de línea **Nueva línea**.

## Avance

| Trabajo | Estado |
|---|---|
| Cinemática directa/inversa, simulador, brazo real con interfaz | ✅ |
| Firmware de adquisición + interfaz con IMU en vivo y grabación | ✅ código y pruebas con ESP32 simulado; falta probar con las IMU reales |
| Análisis E1 (estadística, R, Δt, correlación cruzada, Euler + media móvil, métricas) | ✅ probado con datos sintéticos |
| Análisis E2 (Kalman, 3 Q, ajuste/validación, NIS, P, K, Q/R, aceleración angular) | ✅ probado con datos sintéticos |
| Capturas reales y resultados reales | ⏳ ver `docs/04_captura_y_entregas.md` |
| Verificación de la cinemática con medidas en papel | ✅ código (`verificacion_cinematica.py`); ⏳ medir en el brazo real |
