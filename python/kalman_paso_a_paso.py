"""Kalman PASO A PASO, en su versión más simple (1 variable), para aprender.

Problema: el brazo gira a velocidad casi constante (10 °/s) y el giroscopio la
mide con ruido (σ = 0.06 °/s, el de tu MPU). Queremos la mejor estimación de ω.

Ejecutar:  python python/kalman_paso_a_paso.py

Imprime los primeros pasos con todos los números y luego dibuja el resultado.
Es EXACTAMENTE lo que hace python/kalman.py, pero con escalares en vez de
matrices (allí hay 4 variables: φ1, ω1, φ2, ω2).
"""
import matplotlib.pyplot as plt
import numpy as np

# ---------- DISEÑO (las decisiones que tomas tú) ----------
dt = 0.01            # 100 muestras por segundo
R = 0.06**2          # varianza del ruido del sensor (Entrega 1: σ = 0.06 °/s)
q = 0.0359           # cuánto puede cambiar ω sin avisar (Q_media, f_c = 5 Hz)
omega = 0.0          # estimación inicial: "creo que está quieto"...
P = 25.0             # ...pero dudo mucho: ±5 °/s  (P = 5²)

# ---------- Datos: velocidad real 10 °/s + ruido del giroscopio ----------
rng = np.random.default_rng(1)
n = 300
real = np.full(n, 10.0)
real[150:] = 20.0                       # a los 1.5 s el brazo acelera a 20 °/s
medido = real + rng.normal(0, 0.06, n)

estimado, ganancias = [], []
print(" k |  medición z | predicción | P antes |   K   | innovación | estimación | P después")
print("---+-------------+------------+---------+-------+------------+------------+----------")
for k, z in enumerate(medido):
    # 1) PREDICCIÓN: "si nada cambia, ω sigue igual... pero dudo un poco más"
    omega_pred = omega                  # modelo: ω_k = ω_{k−1}
    P_pred = P + q * dt                 # la duda crece por lo que no sé (Q)

    # 2) ACTUALIZACIÓN: comparar con lo que midió el giroscopio
    K = P_pred / (P_pred + R)           # ¿a quién le creo? 0 = al modelo, 1 = al sensor
    innovacion = z - omega_pred         # la "sorpresa": medición − predicción
    omega = omega_pred + K * innovacion # corrijo con una fracción K de la sorpresa
    P = (1 - K) * P_pred                # tras medir, dudo menos

    estimado.append(omega)
    ganancias.append(K)
    if k < 8 or k in (50, 149, 150, 151, 160):
        print(f"{k:3d}|  {z:10.4f} | {omega_pred:10.4f} | {P_pred:7.4f} | {K:5.3f} |"
              f" {innovacion:10.4f} | {omega:10.4f} | {P:8.5f}")

print(f"\nK se estabiliza en {ganancias[-1]:.3f}: en régimen, cada medición nueva pesa "
      f"{ganancias[-1]*100:.0f} % y la predicción {(1-ganancias[-1])*100:.0f} %.")
print(f"Ruido: medición σ = {np.std(medido[50:150] - 10):.4f} °/s  ->  "
      f"Kalman σ = {np.std(np.array(estimado[50:150]) - 10):.4f} °/s")

t = np.arange(n) * dt
fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
a1.plot(t, medido, ".", ms=3, color="0.6", label="giroscopio (medición con ruido)")
a1.plot(t, real, "k--", label="velocidad real")
a1.plot(t, estimado, "g", lw=2, label="Kalman")
a1.set_ylabel("ω [°/s]")
a1.legend()
a1.set_title("Kalman: al principio confía en el sensor (P grande), luego suaviza")
a2.plot(t, ganancias, "g")
a2.set_ylabel("ganancia K")
a2.set_xlabel("t [s]")
plt.tight_layout()
plt.show()
