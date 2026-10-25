# Cinemática del brazo planar de 2 GDL

**GDL** = *grados de libertad*: cuántas cosas independientes puedes mover. Aquí son
dos: el giro del hombro (θ1) y el del codo (θ2).

## 1. La idea en una frase

| | Pregunta | Entra | Sale | Soluciones |
|---|---|---|---|---|
| **Directa** | Si giro así, ¿dónde queda la mano? | θ1, θ2 | x, y | siempre 1 |
| **Inversa** | Quiero la mano aquí, ¿cómo giro? | x, y | θ1, θ2 | 0, 1 o 2 |

Tu propio brazo hace la inversa todo el tiempo sin que lo pienses: decides "quiero
tocar la taza" (x, y) y el cerebro calcula los ángulos de hombro y codo.

## 2. Convención de ángulos (¡importa!)

```
            ● punta (x, y)
           /
       L2 /  θ2 = giro del eslabón 2 RESPECTO al eslabón 1
         /         (θ2 = 0 → brazo estirado en línea recta)
        ● codo
       /
   L1 /  θ1 = giro del eslabón 1 respecto al eje x
     /
    ■ hombro (0,0) ──────────── x
```

Los ángulos positivos van en sentido **antihorario**, como en trigonometría.

## 3. Cinemática directa: sumar dos flechas

Una flecha de largo L con ángulo α termina en (L·cos α, L·sin α). Eso es lo único
que necesitas de trigonometría.

- Flecha 1 (eslabón 1): largo L1, ángulo **θ1** → termina en el codo.
- Flecha 2 (eslabón 2): largo L2, ángulo **θ1 + θ2**. El eslabón 2 va montado sobre
  el 1, así que hereda su giro y le suma el suyo.

```
x = L1·cos(θ1) + L2·cos(θ1 + θ2)
y = L1·sin(θ1) + L2·sin(θ1 + θ2)
```

**Ejemplo a mano** (L1 = 10, L2 = 8, θ1 = 30°, θ2 = 45°):
- x = 10·cos 30° + 8·cos 75° = 8,660 + 2,071 = **10,731**
- y = 10·sin 30° + 8·sin 75° = 5,000 + 7,727 = **12,727**

## 4. Cinemática inversa: un triángulo

Hombro, codo y punta forman un triángulo con lados **L1**, **L2** y **r**, donde r es la
distancia del hombro a la punta: r² = x² + y².

**Paso 1, el codo (ley de cosenos).** Es Pitágoras generalizado para cualquier triángulo:

```
r² = L1² + L2² + 2·L1·L2·cos(θ2)     →     cos(θ2) = (r² − L1² − L2²) / (2·L1·L2)
```

> ¿Por qué "+" y no "−" como en la ley de cosenos del colegio? Porque θ2 no es el
> ángulo interior del triángulo, sino su **suplemento** (180° − ángulo interior), y
> cos(180° − α) = −cos α.

Dos ángulos tienen el mismo coseno: +θ2 y −θ2. Esas son las **dos soluciones**:
**codo abajo** y **codo arriba**. Para no perder el signo se usa `atan2`:

```
θ2 = atan2( ±√(1 − cos²θ2), cos θ2 )
```

**Paso 2, el hombro.** θ1 es el ángulo hacia la punta menos lo que el eslabón 2
"desvía" la dirección:

```
θ1 = atan2(y, x) − atan2( L2·sin θ2 , L1 + L2·cos θ2 )
```

**Comprobación con el ejemplo** (x = 10,731, y = 12,727):
- r² = 115,15 + 161,98 = 277,13
- cos θ2 = (277,13 − 100 − 64) / 160 = 0,7071 → θ2 = **45°** ✓
- θ1 = atan2(12,727; 10,731) − atan2(5,657; 15,657) = 49,86° − 19,86° = **30°** ✓

**¿Por qué `atan2` y no `atan`?** `atan(y/x)` no distingue (1, 1) de (−1, −1), porque
ambos dan y/x = 1. `atan2(y, x)` mira los signos por separado y devuelve el ángulo
correcto en los 4 cuadrantes.

## 5. ¿Cuándo NO hay solución?

Si |cos θ2| > 1 no existe ningún ángulo, porque el triángulo es imposible:
- r > L1 + L2: el brazo estirado no llega.
- r < |L1 − L2|: el brazo doblado al máximo no se encoge tanto.

El **espacio de trabajo** es el anillo entre esos dos radios (el gris del simulador),
recortado además por los límites reales de los servos (0°–180°).

## 6. Verificación con el brazo real (punto 1 de la entrega)

1. Elegir unas 8–10 posiciones de referencia (θ1, θ2) repartidas por el espacio de trabajo.
2. Mandarlas al brazo, medir la posición real de la punta sobre papel milimetrado
   y calcular la posición teórica con la cinemática directa.
3. Error de cada punto: e = √((x_real − x_teo)² + (y_real − y_teo)²). Resumen: RMSE y error máximo.
4. Repetir con cinemática inversa: pedir un (x, y), ver dónde llega realmente.

**Causas típicas del error:** el 0° del servo no coincide con el 0° del modelo
(*offset*), holgura de los engranajes (*backlash*), resolución del servo (~1°),
flexión de los eslabones y error al medir L1 y L2.

## 7. Pruébalo tú

```
python python/simulador.py
```

**Ejercicios** (respóndelos antes de mirar el simulador y luego compruébalos):
1. Con θ1 = 90° y θ2 = 0°, ¿dónde está la punta?
2. Con θ1 = 0° y θ2 = 180°, ¿dónde está? ¿Es alcanzable si L1 = L2?
3. Haz clic en un punto y alterna "codo arriba/abajo". ¿Qué cambia en θ1 y θ2?
   ¿Por qué θ2 cambia solo de signo y θ1 no?
4. ¿Por qué cerca del borde exterior del anillo las dos soluciones casi coinciden?
