# Prueba final de la teleoperación (10 minutos antes de entregar)

Todo el código ya está listo y probado con un video sintético y un "DroidCam falso".
Solo falta grabar **tus** sesiones reales. El análisis y la subida a GitHub son automáticos.

## ¿Qué tiene ya la Entrega 2?

| Criterio | Evidencia | Estado |
|---|---|---|
| C1 (50 %) modelo e implementación de Kalman | E5: `kalman.py`, `modelo_kalman.py`, `config_kalman.py`, R de la E1 | ✅ con datos reales |
| C1 | E6: ≥ 3 Q razonadas, ajuste ≠ validación (`manifiesto.json`, `seleccion_Q.json`) | ✅ con datos reales |
| C1/C3 | E7: métricas, gráficas, aceleración angular, NIS, límites (`resultados/reales/e2/`) | ✅ con datos reales |
| C2 (20 %) validación y **teleoperación usando la estimación** | E8: `teleop_camara.py` + `analisis_teleop.py` → `resultados/reales/teleop/` | ⏳ **falta grabar las 2 sesiones (esta guía)** |
| C2-N5 | tiempos de cómputo, latencia, crudo vs Kalman | ⏳ sale solo del análisis de esas sesiones |
| C3 (30 %) interpretación y elección de Q | `resumen_seleccion_Q.md`, `docs/SUSTENTACION.md` | ✅ |
| E9 | preguntas de comprobación individual | practicar `docs/ENTREGAS.md` |

## Antes (en casa o apenas llegues)

1. **Imprime** `docs/marcadores_aruco.pdf` a **tamaño real (100 %)** y comprueba que la línea mida 10 cm.
   Recorta los **3 cuadros grandes** dejando el margen blanco y pégalos sobre cartón.
   *Sin impresora:* `python python/generar_marcadores.py` muestra cada cuadro para dibujarlo
   a mano en papel cuadriculado (6×6 casillas, 1 cm cada una, rellenas con marcador negro).
2. Pégalos con cinta **encima** del brazo: **ID 0 hombro, ID 1 codo, ID 2 muñeca**.
3. ESP32 con `firmware/adquisicion` (ya lo tiene cargado), cable USB y fuente de 5 V conectados.

## Los 10 minutos

### 1. Red rápida (1 min)

En el ping de antes la WiFi tardaba 250–550 ms: **demasiado** para teleoperar.
- En el teléfono: activa el **punto de acceso (hotspot)**.
- En el PC: conéctate a la red WiFi del teléfono.
- Abre **DroidCam** y anota la nueva **IP** (cambia al usar el hotspot), p. ej. `192.168.43.1`.
- **Cierra el navegador** si tenía DroidCam abierto (DroidCam atiende a un solo programa).

### 2. Terminal de VS Code (1 min)

```
.venv\Scripts\activate
git pull
python python/teleop_camara.py --video http://IP_DEL_TELEFONO:4747/video --puerto COM3
```

En la terminal debe decir `Video abierto con: MJPEG directo (sin búfer)`.
Se abre la ventana **Teleoperacion**. Los 3 cuadros salen enmarcados en azul, verde y rojo,
unidos por una línea amarilla, y debajo dice `aruco: hombro:si codo:si muneca:si`.

### 3. Calibrar (1 min)

| Tecla | Qué haces | Qué ves |
|---|---|---|
| **C** | brazo **estirado al frente**, quieto | "Pose de referencia guardada": ahora vale (90, 0) |
| **N** | brazo **quieto 10 s** | "Midiendo ruido…" y luego `R camara: sigma = …` (medido) |
| **R** | con el brazo en la pose de inicio | `ENVIANDO`: el robot empieza a copiarte |

### 4. Sesión 1: robot movido con la cámara CRUDA (1 min)

1. Pulsa **F** hasta que arriba diga `robot <- CRUDO`.
2. Pulsa **G** (empieza a grabar) y sigue la guía de la pantalla:
   - 0–10 s: brazo **lento**
   - 10–20 s: brazo **rápido**
   - 20–30 s: **tapa la muñeca** con la otra mano 2 veces (1 s cada vez)
3. Pulsa **G** para terminar. Se guarda `sesion_XX.csv` y se sube sola.

### 5. Sesión 2: robot movido con KALMAN (1 min)

Pulsa **F** hasta que diga `robot <- KALMAN` y repite **lo mismo** (G, 30 s, G).

### 6. Salir (1 min)

Pulsa **Q**. En la terminal sale `Analizando las sesiones…` y después `[git] Subido a GitHub ✓`.
Los resultados quedan en `resultados/reales/teleop/`:
- `resumen_teleop.md`: la tabla de crudo vs Kalman, para leer en voz alta.
- `20_teleop_sesion_XX.png`: tus ángulos, crudos y con Kalman, y las oclusiones en gris.
- `21_robot_sesion_XX.png`: lo que se le ordenó al robot vs lo que hizo (medido con sus IMU).

### 7. Marcar la versión entregada (30 s)

```
git pull
git tag entrega2
git push origin entrega2
```

## Planes B

| Problema | Qué hacer |
|---|---|
| No pude imprimir | Dibuja los 3 cuadros a mano, o usa papeles de color: `--modo color` y tecla **L** (clic en hombro, codo y muñeca) |
| La cámara no abre | ¿DroidCam abierto? ¿navegador cerrado? ¿pusiste `:4747`? ¿la IP es la nueva? |
| Va lento o atrasado | Usa el hotspot (paso 1). Mira `proceso X ms` arriba: debe ser mucho menor que 33 ms |
| Un cuadro se pierde | Tecla **D**: se dibujan en rojo los cuadros que ve pero no lee. Acerca el teléfono, más luz, sin brillo |
| El robot no se conecta | Monitor Serie de Arduino **cerrado**; ¿COM3? Sin robot igual se puede grabar (quita `--puerto COM3`): el análisis sale sin la parte del robot |
| Nada funciona con la cámara | Demostración con **video sintético** (decirlo así): `python python/simular_teleop.py --video` y luego `python python/teleop_camara.py --video datos/sinteticos/teleop/video_sintetico.mp4 --puerto COM3`. El robot copia el brazo simulado |

## Qué decir (E8, C2)

1. **"El robot me copia usando la estimación de Kalman."** La cámara mide θ1 y θ2. Kalman usa
   el mismo modelo de velocidad casi constante de la E1/E2, con el Δt real de cada cuadro, y le
   manda θ̂ al servo (`modelo_a_servo`).
2. **Crudo vs Kalman en las mismas condiciones.** Las dos estimaciones salen de los mismos cuadros.
   En `resumen_teleop.md` mira la *aspereza* (temblor) y los *cambios de dirección/s* del servo.
3. **Oclusión.** Al tapar la muñeca, la cámara cruda se congela. Kalman **sigue midiendo θ1**
   (el hombro y el codo sí se ven: se usa solo esa fila de H) y **predice θ2**. Si la oclusión
   dura mucho, frena la predicción para que el robot no siga de largo.
4. **Tiempos (N5).** Cuánto tarda Kalman por cuadro (µs) y detección + Kalman (ms), comparado con
   los 33 ms entre cuadros. El retraso orden → robot y cámara → robot sale **medido con los
   giroscopios del robot**, las IMU de la E1.
5. **Latencia del video:** `python python/prueba_latencia_video.py`. Antes, OpenCV acumulaba
   cuadros y el retraso crecía hasta más de 2 s (por eso "se trababa"). Ahora siempre se usa
   el cuadro más nuevo: unos 17 ms.
6. **Límites.** La latencia teléfono → PC por WiFi no se mide con estos datos (la estimas con
   `ping`). La cámara mide en píxeles del plano de la mesa: si el teléfono no está paralelo a
   la mesa, los ángulos salen deformados por la perspectiva.
