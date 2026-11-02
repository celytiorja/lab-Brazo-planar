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
- `datos/crudos/manifiesto.json` se arma solo, con reglas fijas:
  - **Reposo para R:** el primero que pase la prueba de **estacionariedad** (Levene, p > 0.05).
  - **Perfiles:** solo las repeticiones que pasan **todos** los chequeos de `validar_datos.py`
    (muestreo a 100 Hz, sin pérdidas, y que **el brazo medido haya seguido a la consigna**).
    Ajuste = 1.ª válida y validación = 2.ª válida.
- **Subida automática:** al terminar cada captura, la interfaz hace sola
  `git add` → `git commit` → `git pull` → (rehace el manifiesto) → `git push`
  (`python/sincronizar.py`). En la terminal verás `Subido a GitHub ✓`. Si no hay internet,
  queda guardada en tu PC y se sube con la siguiente captura. Para desactivarla:
  `SUBIR_AUTOMATICO = False` en `python/interfaz_imu.py`.
- **Ajuste y validación son SIEMPRE capturas distintas**: las `_01` son de ajuste y las `_02`
  de validación.

## 4b. Verificación de la cinemática (punto 1 de la Entrega 1)

Aquí no hacen falta las IMU: se mide **dónde queda la punta** del brazo real.

1. Crea la hoja de medición: `python python/verificacion_cinematica.py --plantilla`.
   Se crea `datos/verificacion_cinematica.csv` con 10 puntos: 5 de **directa** (ángulos de
   servo elegidos) y 5 de **inversa** (punto (x, y) elegido, convertido a ángulos). Cada uno
   aparece **2 veces** (`repeticion` 1 y 2), para medir la repetibilidad.
2. Prepara el papel milimetrado:
   - **Origen (0, 0) = eje de giro del hombro.** Pega el papel de modo que el centro del eje
     caiga sobre una intersección.
   - **Eje x = dirección del eslabón 1 cuando θ1 = 0°.** Manda ese ángulo con la interfaz y traza
     la línea a lo largo del eslabón.
   - **Eje y** = perpendicular, hacia donde apunta el brazo con θ1 = 90°.
   - Marca en la punta del eslabón 2 un punto fino (la "punta" de las medidas L1 y L2).
3. Para cada fila, manda `servo_h` y `servo_c` (Monitor Serie con `prueba_servos`:
   `h 45, c 90`, o la interfaz). Espera 1 s y anota **x_med_mm** e **y_med_mm** de la punta.
   Para la repetición 2, mueve antes el brazo a otro punto y vuelve: así se ve el juego de los
   engranajes.
4. Guarda el CSV (en VS Code o Excel, **sin cambiar las columnas**) y ejecuta
   `python python/verificacion_cinematica.py`.

Resultado en `resultados/reales/e1/`:

- `verificacion_cinematica.md`: error por punto.
- `verificacion_cinematica_resumen.md`: RMSE, máximo, por tipo, repetibilidad, error esperado
  solo por la resolución de 1° y **offsets estimados** de cada articulación.
- `09_verificacion_cinematica.png`: el gráfico.

Si los offsets estimados son grandes (> 1°), corrígelos en `python/parametros.py` y vuelve a
medir.

## 5. Generar los resultados

```
python python/validar_datos.py      (opcional: analisis_e1 ya la ejecuta primero)
python python/analisis_e1.py
python python/analisis_e2.py
```

Los resultados salen en `resultados/reales/e1/` y `resultados/reales/e2/`. Los nombres de los
archivos son los mismos que con los datos sintéticos (ver `docs/SUSTENTACION.md`).

## 6. Guardar en Git (evidencia con versión identificada)

```
git add datos/crudos datos/verificacion_cinematica.csv resultados/reales python/config_imu.py
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
