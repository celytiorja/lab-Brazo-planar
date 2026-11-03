# Teleoperación con la cámara del teléfono (Entrega 2)

El robot copia **tu brazo**. El teléfono, arriba de la mesa, ve tres marcadores impresos
(cuadros ArUco) en tu hombro, codo y muñeca.
Python calcula tus ángulos θ1 y θ2, los filtra con **Kalman** y se los manda al robot.

```
Teléfono (DroidCam, WiFi) → PC: marcadores → θ1, θ2 → Kalman → ESP32 → servos
```

## 1. Materiales (10 minutos)

### Por qué cuadros ArUco y no papeles de color

Con papeles de color el programa busca "píxeles parecidos al azul que aprendió". Eso falla
fácil: con poca luz el azul claro se vuelve **gris**, con mucha luz se vuelve **blanco**, y si
algo del fondo tiene un color parecido, lo confunde. (Fue lo que pasó con el hombro.)

Un **ArUco** es como un código QR pequeñito: borde negro y 4×4 casillas blanco/negro.

| | Papel de color | Cuadro ArUco |
|---|---|---|
| Qué busca | un tono de color | un cuadrado con borde negro y casillas |
| Con poca o mucha luz | el color cambia y se pierde | blanco y negro se distinguen siempre |
| ¿Cuál es cuál? | depende de dónde estaba antes | el cuadro **dice su número** (ID 0, 1, 2) |
| Fondo parecido | lo confunde | imposible: el código tiene bits de verificación |
| Precisión del centro | mancha de bordes difusos | 4 esquinas exactas (sub-píxel) → menos R |
| Hay que calibrar | sí (clic en cada color) | no |

Su punto débil: si te mueves **muy rápido** la imagen sale borrosa y ese cuadro no se lee.
Ahí es justo donde ayuda **Kalman**: predice con su modelo hasta que lo vuelve a ver.

### Lo que necesitas

1. **Imprimir la hoja** `docs/marcadores_aruco.pdf` a **tamaño real** (100 %, sin "ajustar
   a la página"). Mide con una regla la línea de 10 cm de la hoja. Si no tienes impresora,
   `python python/generar_marcadores.py` muestra cada cuadro para dibujarlo a mano en papel
   cuadriculado (6×6 casillas con marcador negro).
2. Recortar los **3 cuadros grandes (6 cm)** por la línea gris punteada, **dejando el margen
   blanco**, y pegarlos sobre cartón para que queden **planos**.
3. Pegarlos (cinta) **encima** de tu brazo, mirando hacia la cámara:
   **ID 0 → hombro**, **ID 1 → codo**, **ID 2 → muñeca**. Da igual cómo queden girados.
4. **El teléfono arriba de la mesa, mirando hacia abajo**, a unos 60–80 cm, con tu brazo
   completo en la imagen. Sirve un trípode, una lámpara o una caja.

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

1. Muestra los 3 cuadros a la cámara. Cada uno aparece **enmarcado** con su color (azul
   hombro, verde codo, rojo muñeca) y unidos por una **línea amarilla**. Abajo de los
   ángulos dice `aruco: hombro:si codo:si muneca:si`.
2. Pon el brazo **estirado hacia adelante** (alejándose de ti) y pulsa **C**. Esa pose pasa a
   valer (90°, 0°), igual que la posición de inicio del robot.
3. Brazo **quieto** y pulsa **N**: durante 10 s mide cuánto "tiembla" la detección. Esa es la
   **R de la cámara**, igual que hiciste con las IMU en la Entrega 1.
4. Mueve el brazo: arriba ves los ángulos **crudos** y los de **Kalman**.

Si un cuadro no se detecta, pulsa **D** (diagnóstico): se dibujan en **rojo fino** los
cuadrados que la cámara ve pero no logra leer.

| Lo que ves | Causa probable | Arreglo |
|---|---|---|
| Ni siquiera un recuadro rojo | muy pequeño en la imagen | acerca el teléfono o usa cuadros más grandes |
| Recuadro rojo pero no se lee | borroso, doblado, brillo o sin margen blanco | pégalo en cartón, deja el margen, evita el reflejo de la lámpara |
| Se pierde solo al moverte rápido | desenfoque de movimiento | más luz (la cámara expone menos tiempo); Kalman cubre esos cuadros |
| Dice `hombro (memoria)` | el hombro no se vio en ese cuadro | normal: el hombro casi no se mueve y se usa su última posición |

Respaldo con papeles de color: `--modo color` y la tecla **L** (clic en hombro, codo y muñeca).

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
