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
firmware/
  prueba_servos/                 ← sketch para probar solo los dos servos
  prueba_hardware/               ← sketch para probar servos + IMU juntos
python/
  parametros.py                  ← L1, L2 y límites de las articulaciones
  cinematica.py                  ← cinemática directa e inversa
  simulador.py                   ← simulador interactivo
  test_cinematica.py             ← pruebas automáticas
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

## Avance de la Entrega 1

| # | Trabajo | Estado |
|---|---|---|
| 1 | Cinemática directa e inversa + verificación con posiciones de referencia | 🟡 Teoría, código y pruebas listos; falta medir el brazo real |
| 2 | Captura ≥30 s en reposo + movimiento dinámico repetible (ambas IMU) | ⚪ Pendiente (firmware de adquisición + interfaz) |
| 3 | Media, varianza, matriz R, alineación temporal, correlación cruzada | ⚪ Pendiente |
| 4 | Integración de Euler + media móvil (≥2 ventanas) | ⚪ Pendiente |
| 5 | Gráficas + tabla de métricas (ruido, deriva, retraso) | ⚪ Pendiente |
