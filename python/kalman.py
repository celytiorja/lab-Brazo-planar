"""Filtro de Kalman lineal discreto, escrito "a mano" (sin bibliotecas) para que
cada ecuación se pueda señalar en la sustentación.

    PREDICCIÓN                         ACTUALIZACIÓN
    x̂⁻ = F x̂                           y  = z − H x̂⁻          (innovación)
    P⁻ = F P Fᵀ + Q                    S  = H P⁻ Hᵀ + R       (covarianza de y)
                                       K  = P⁻ Hᵀ S⁻¹         (ganancia)
                                       x̂  = x̂⁻ + K y
                                       P  = (I−KH) P⁻ (I−KH)ᵀ + K R Kᵀ   (forma de Joseph)

La forma de Joseph da el mismo resultado que P = (I−KH)P⁻ en aritmética exacta,
pero conserva P simétrica y positiva aunque haya errores de redondeo.
"""
import numpy as np


class FiltroKalman:
    def __init__(self, x0, P0):
        self.x = np.array(x0, dtype=float)
        self.P = np.array(P0, dtype=float)

    def predecir(self, F, Q):
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + Q

    def actualizar(self, z, H, R):
        """Devuelve un diccionario con lo necesario para el diagnóstico."""
        y = z - H @ self.x
        S = H @ self.P @ H.T + R
        S_inv = np.linalg.inv(S)
        K = self.P @ H.T @ S_inv
        self.x = self.x + K @ y
        I_KH = np.eye(len(self.x)) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ R @ K.T
        return {
            "innovacion": y,
            "S": S,
            "K": K,
            # NIS = yᵀ S⁻¹ y. Si el filtro es consistente sigue una χ² con m grados
            # de libertad (m = número de mediciones): su media debe ser ≈ m.
            "nis": float(y @ S_inv @ y),
        }

    def chequeo_P(self):
        """(asimetría máxima, autovalor mínimo): P debe ser simétrica y positiva."""
        asimetria = float(np.max(np.abs(self.P - self.P.T)))
        min_autovalor = float(np.min(np.linalg.eigvalsh((self.P + self.P.T) / 2)))
        return asimetria, min_autovalor
