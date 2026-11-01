# Capturar datos reales y generar las Entregas 1 y 2

Todo se hace con **dos programas**:

| Programa | Dónde corre | Para qué |
|---|---|---|
| `firmware/adquisicion/adquisicion.ino` | ESP32 (súbelo con Arduino IDE) | Lee las 2 MPU a 100 Hz, mueve los servos y envía los datos |
| `python/interfaz_imu.py` | PC | Muestra las MPU en vivo, mueve el brazo y **graba** las capturas |

> `prueba_servos` + `interfaz.py` siguen sirviendo para mover el brazo sin IMU.

## 1. Cargar el firmware (una vez)

1. En Arduino IDE abre `firmware/adquisicion/adquisicion.ino` y súbelo.
2. **Cierra el Monitor Serie.** Si lo abres para mirar, ponlo en **460800** baudios.

## 2. Abrir la interfaz

En la terminal de VS Code, con `(.venv)` al inicio de la línea:

```
git pull
python python/interfaz_imu.py
```

Pulsa **Conectar**. Arriba a la derecha debe aparecer *"Firmware OK, IMU1 e IMU2 responden"*.

## 3. Verificar el montaje (una vez, ¡importante!)

1. Con **"Mover el brazo con: Sliders"**, gira **solo el hombro** con el slider θ1, en sentido
   antihorario (θ1 aumentando).
2. En la gráfica de arriba, **giro 1** debe ser **positivo** mientras gira.
   - Si sale **negativo**, en `python/config_imu.py` cambia el signo: `EJE_GIRO = {1: ("gz", -1), ...}`.
   - Si **no se mueve**, el eje no es z: prueba `"gx"` o `"gy"`, según lo que viste con
     `prueba_hardware`.
3. Repite con el codo: con el codo quieto, **giro 2** debe moverse igual que giro 1, porque IMU2
   gira con todo el brazo. Con el hombro quieto y el codo girando antihorario, giro 2 debe ser
   positivo.
4. Si cambiaste `config_imu.py`, cierra la interfaz y ábrela de nuevo, para que Python lea el
   cambio.

Comprobación visual: con el sesgo calibrado, los brazos **gris, naranja y verde** (estimados por
las IMU) deben moverse **junto al negro punteado** (la consigna).

## 4. Capturar (unos 10 minutos)

**Antes de cada captura:** brazo quieto, luego **"Calibrar sesgo"** y espera 3 s.

| Orden | Botón | Archivo que crea | Para qué |
|---|---|---|---|
| 1 | Grabar reposo 40 s (¡no tocar la mesa!) | `estatico_01` | E1: media, varianza, matriz R |
| 2 | Perfil 1: escalones | `escalones_01` | E1 dinámico + ajuste E2 |
| 3 | Perfil 2: seno lento | `seno_lento_01` | ajuste E2 |
| 4 | Perfil 3: seno rápido | `seno_rapido_01` | ajuste E2 |
| 5 | Perfil 1 otra vez | `escalones_02` | **validación** E2 |
| 6 | Perfil 2 otra vez | `seno_lento_02` | **validación** E2 |
| 7 | Perfil 3 otra vez | `seno_rapido_02` | **validación** E2 |

- Los archivos quedan en `datos/crudos/` (un `.csv` crudo y un `.json` con la configuración).
- `datos/crudos/manifiesto.json` se arma solo.
- **Ajuste y validación son SIEMPRE capturas distintas**: las `_01` son de ajuste y las `_02`
  de validación.

## 5. Generar los resultados

```
python python/analisis_e1.py
python python/analisis_e2.py
```

Los resultados salen en `resultados/reales/e1/` y `resultados/reales/e2/`. Los nombres de los
archivos son los mismos que con los datos sintéticos (ver `docs/SUSTENTACION.md`).

## 6. Guardar en Git (evidencia con versión identificada)

```
git add datos/crudos resultados/reales python/config_imu.py
git commit -m "Capturas reales y resultados de las Entregas 1 y 2"
git push
```

## 7. Teleoperación (Entrega 2)

**"Mover el brazo con:"** decide de dónde salen las órdenes a los servos:

- **Sliders:** el brazo va a donde tú pides. Las IMU solo observan.
- **Integración directa / Media móvil / Kalman:** el brazo copia el ángulo **estimado con las
  IMU**.

⚠️ Para teleoperar de verdad, las IMU deben ir sobre **otro brazo**: el tuyo (IMU1 en el brazo,
IMU2 en el antebrazo) o un brazo maestro. Si van sobre el mismo robot, este se persigue a sí
mismo y la deriva lo arrastra.

Abajo de la ventana se ve el tiempo de cómputo de Kalman por muestra (µs), la frecuencia real
de muestreo y las muestras perdidas: son datos para el criterio C2.
