# Interfaz gráfica: cómo funciona por dentro

## 1. El recorrido de una orden

```
 Tú mueves un slider o haces clic
        │
        ▼
 VistaBrazo (simulador.py) ── calcula θ1, θ2 (directa o inversa) y dibuja
        │  al_mover(θ1, θ2)
        ▼
 servos.py ── traduce θ1, θ2 → ángulos de servo (0..180) con la calibración
        │
        ▼
 interfaz.py ── cada 40 ms: ¿cambió el objetivo? → envía "h 90, c 120\n"
        │
        ▼  cable USB (puerto serie COMx, 115200 baudios)
 ESP32 (prueba_servos.ino) ── lee la línea, la corta en comas, mueve los servos
        │                    y responde "Hombro -> 90°"
        ▼
 interfaz.py ── muestra la respuesta en "Lo que responde el ESP32"
```

Python hace **exactamente lo mismo que tú hacías a mano** en el Monitor Serie.

## 2. Calibración: del modelo al servo

El modelo usa θ1 y θ2 (θ2 = 0 cuando el brazo está estirado). El servo solo entiende
"de 0° a 180°", y su 0° depende de **cómo lo montaste**. La traducción es una recta:

```
ángulo_servo = OFFSET + SIGNO · θ
```

- **OFFSET**: el ángulo que tiene el servo cuando el eslabón está en θ = 0.
- **SIGNO**: +1 si al subir el ángulo del servo el eslabón gira antihorario (θ positivo);
  −1 si gira al revés.

Valores provisionales (`python/parametros.py`):

| Articulación | OFFSET | SIGNO | Significa |
|---|---|---|---|
| Hombro | 0 | +1 | servo 0° → eslabón 1 horizontal hacia la derecha (θ1 = 0°) |
| Codo | 90 | +1 | servo 90° → brazo estirado (θ2 = 0°) |

Con esos valores, el rango de cada articulación sale solo: θ1 ∈ [0°, 180°] y
θ2 ∈ [−90°, 90°]. Cuando montemos el brazo mediremos el OFFSET y el SIGNO reales.

**Ejemplo:** θ1 = 30° y θ2 = 45° → hombro = 0 + 30 = **30°**, codo = 90 + 45 = **135°**.

## 3. ¿Por qué se envía "como máximo cada 40 ms"?

Al arrastrar un slider, matplotlib genera **cientos** de eventos por segundo. Si cada
uno enviara una orden, la cola del puerto serie se llenaría y el brazo iría atrasado.

Por eso hay dos pasos separados:

1. Cada evento **solo anota** el objetivo (`self.objetivo`).
2. Un reloj, cada 40 ms (25 veces por segundo), mira si el objetivo cambió desde el
   último envío. Si cambió, envía **solo el más reciente**.

Esta idea, desacoplar "lo que se pide" de "lo que se envía", aparece en todos los
sistemas en tiempo real. La volverás a ver con la cámara.

## 4. Errores típicos

| Síntoma | Causa | Solución |
|---|---|---|
| "No se pudo abrir COM5" | El **Monitor Serie de Arduino** está abierto | Ciérralo: un puerto COM solo lo puede usar un programa a la vez |
| Al conectar, el brazo va a 90°/90° y después salta | Abrir el puerto **reinicia** el ESP32 | Normal. La interfaz espera 2 s y luego envía la posición del dibujo |
| No aparece ningún puerto | Cable USB de solo carga, o falta el driver CP210x/CH340 | Prueba otro cable; mira el Administrador de dispositivos → Puertos (COM y LPT) |
| El brazo se mueve al revés | SIGNO equivocado en la calibración | Cambia el SIGNO a −1 en `parametros.py` |
