"""Calculo del presupuesto estimado de un viaje."""

import math

from .datos import NIVELES

MAX_DIAS = 30
MAX_PERSONAS = 20
PORCENTAJE_IMPREVISTOS = 0.10


def calcular(destino, dias, personas, nivel):
    """Devuelve el desglose del costo del viaje en dolares.

    Se asume una habitacion por cada dos personas y una noche menos que los dias de viaje.
    """
    noches = dias - 1
    habitaciones = math.ceil(personas / 2)
    precio_noche = next(h["precio"] for h in destino["hospedaje"] if h["nivel"] == nivel)

    hospedaje = precio_noche * noches * habitaciones
    comida = destino["comida_dia"][nivel] * dias * personas
    actividades = destino["actividades_dia"] * dias * personas
    transporte = destino["transporte"]["costo_ida_vuelta"] * personas

    subtotal = hospedaje + comida + actividades + transporte
    imprevistos = round(subtotal * PORCENTAJE_IMPREVISTOS)
    total = subtotal + imprevistos

    return {
        "noches": noches,
        "habitaciones": habitaciones,
        "hospedaje": hospedaje,
        "comida": comida,
        "actividades": actividades,
        "transporte": transporte,
        "imprevistos": imprevistos,
        "total": total,
        "por_persona": round(total / personas),
    }


def comparar_niveles(destino, dias, personas):
    """Total del mismo viaje en los tres niveles de gasto, para que el usuario compare."""
    return {nivel: calcular(destino, dias, personas, nivel)["total"] for nivel in NIVELES}
