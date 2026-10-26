"""Pruebas de la calibración servo <-> modelo y del texto que se envía al ESP32."""
import parametros as P
from conexion import ConexionESP32, orden_servos
from servos import modelo_a_servo, servo_a_modelo


def test_ida_y_vuelta_servo_modelo():
    for s_h in range(0, 181, 15):
        for s_c in range(0, 181, 15):
            assert modelo_a_servo(*servo_a_modelo(s_h, s_c)) == (s_h, s_c)


def test_limites_coinciden_con_el_servo():
    # Los extremos de θ deben caer justo en 0° y 180° del servo.
    assert sorted(modelo_a_servo(P.THETA1_MIN, P.THETA2_MIN) +
                  modelo_a_servo(P.THETA1_MAX, P.THETA2_MAX)) == [0, 0, 180, 180]


def test_servo_nunca_sale_de_0_a_180():
    assert modelo_a_servo(-500, 500) in [(0, 180), (180, 0), (0, 0), (180, 180)]


def test_orden_igual_a_la_del_monitor_serie():
    assert orden_servos(45, 120) == "h 45, c 120\n"


def test_lineas_que_llegan_partidas():
    # El ESP32 envía "Hombro -> 45°\n", pero puede llegar en dos pedazos.
    c = ConexionESP32()
    assert c._separar_lineas("Hombro -> 4".encode()) == []
    assert c._separar_lineas("5°\nCodo -".encode()) == ["Hombro -> 45°"]
    assert c._separar_lineas("> 120°\r\n".encode()) == ["Codo -> 120°"]
