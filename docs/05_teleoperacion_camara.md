# Teleoperación con la cámara del teléfono (Entrega 2)

El robot copia **tu brazo**. El teléfono, arriba de la mesa, ve tres marcadores de color.
Python calcula tus ángulos θ1 y θ2, los filtra con **Kalman** y se los manda al robot.

```
Teléfono (DroidCam, WiFi) → PC: marcadores → θ1, θ2 → Kalman → ESP32 → servos
```

## 1. Materiales (5 minutos)

- **3 marcadores de colores bien distintos**: papel o cinta de unos 2–3 cm, de colores
  intensos y mates (que no brillen). Por ejemplo azul en el **hombro**, verde en el **codo** y
  rojo o rosado en la **muñeca**. Evita colores que haya en el fondo, en tu ropa o en tu piel.
- **El teléfono arriba de la mesa, mirando hacia abajo**, a unos 60–80 cm, con tu brazo
  completo en la imagen. Sirve un trípode, una lámpara o una caja.
- **Buena luz y pareja**, sin sombras fuertes.

## 2. El teléfono como cámara (una vez)

1. Instala **DroidCam** en el teléfono (Play Store o App Store).
2. El teléfono y el PC deben estar en la **misma red WiFi**.
3. Abre DroidCam: muestra una dirección como `WiFi IP: 192.168.1.23` y `Port: 4747`.
4. Tu fuente de video es `http://192.168.1.23:4747/video` (con tu IP).

## 3. Instalar OpenCV (una vez)

En la terminal de VS Code, con `(.venv)`:

```
git pull
pip install -r requirements.txt
```

## 4. Primera prueba, SIN robot

```
python python/teleop_camara.py --video http://192.168.1.23:4747/video
```

1. Tecla **L**: haz **clic** en el marcador del **hombro**, luego el del **codo** y luego el de la
   **muñeca**. El programa aprende cada color.
2. Pon el brazo **estirado hacia adelante** (alejándose de ti) y pulsa **C**. Esa pose pasa a
   valer (90°, 0°), igual que la posición de inicio del robot.
3. Brazo **quieto** y pulsa **N**: durante 10 s mide cuánto "tiembla" la detección. Esa es la
   **R de la cámara**, igual que hiciste con las IMU en la Entrega 1.
4. Mueve el brazo: arriba ves los ángulos **crudos** y los de **Kalman**.

Si un marcador no se detecta: mejora la luz, usa un color más intenso o repite la tecla **L**.

## 5. Con el robot

ESP32 con `firmware/adquisicion` y el Monitor Serie cerrado:

```
python python/teleop_camara.py --video http://192.168.1.23:4747/video --puerto COM3
```

- El robot **arranca en PAUSA**. Pulsa **R** para que empiece a copiarte. Hazlo con tu brazo en
  la pose de inicio, para que no dé un salto.
- **F** cambia lo que mueve al robot: **crudo** (la cámara tal cual) o **Kalman**.
- **1**, **2** y **3** cambian la configuración Q (baja, media o alta).

## 6. Grabar sesiones para la evidencia (E8 y C2)

**G** inicia y detiene la grabación. Queda en `datos/teleop/sesion_XX.csv` y **se sube sola a
GitHub**. Para comparar crudo contra Kalman en las mismas condiciones:

| Sesión | Fuente (F) | Q | Movimiento |
|---|---|---|---|
| 1 | crudo | — | el mismo movimiento lento, 20 s |
| 2 | Kalman | Q_media | el mismo movimiento lento, 20 s |
| 3 | crudo | — | movimiento rápido, 20 s |
| 4 | Kalman | Q_media | movimiento rápido, 20 s |
| 5 | Kalman | — | tapa la muñeca con la otra mano 1–2 s (oclusión) |

## 7. Qué decir (por qué Kalman ayuda aquí)

- **La cámara tiembla** (lo mide R) y llega a ~30 cuadros/s con Δt irregular. Kalman usa el Δt
  real de cada cuadro y entrega movimientos **más suaves** al servo.
- **Si un marcador se tapa**, la cámara cruda se queda congelada. Kalman **sigue
  prediciendo** con su modelo (velocidad casi constante) hasta que vuelve a verlo.
- **No hay deriva**: la cámara mide el ángulo directamente. Es el complemento perfecto de las
  IMU, que no tiemblan pero derivan. **Fusionarlas** (cámara + giroscopios en tu brazo) es el
  paso siguiente; el código ya está preparado (`python/kalman_camara.py`).
