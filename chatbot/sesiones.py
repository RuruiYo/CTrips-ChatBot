"""Memoria de la conversacion de cada usuario, pensada para guardar lo minimo posible."""

import hashlib
import time

MINUTOS_EXPIRACION = 30

_sesiones = {}


def _clave(numero):
    """El numero de telefono nunca se guarda: se usa su huella SHA-256 como identificador."""
    return hashlib.sha256(numero.encode("utf-8")).hexdigest()[:16]


def nueva_sesion():
    return {
        "estado": "MENU",
        "tipo": None,
        "pais": None,
        "sin_pais": False,
        "destino": None,
        "dias": None,
        "personas": None,
        "nivel": None,
        "opciones": [],
        "pendiente": None,
        "fallos": 0,
        "nueva": True,
        "ultima": time.time(),
    }


def _limpiar_expiradas():
    """Borra las conversaciones que llevan mas de 30 minutos sin actividad."""
    limite = time.time() - MINUTOS_EXPIRACION * 60
    for clave in [c for c, s in _sesiones.items() if s["ultima"] < limite]:
        del _sesiones[clave]


def obtener(numero):
    """Devuelve la sesion del usuario y su identificador anonimo (para los registros)."""
    _limpiar_expiradas()
    clave = _clave(numero)
    if clave not in _sesiones:
        _sesiones[clave] = nueva_sesion()
    sesion = _sesiones[clave]
    sesion["ultima"] = time.time()
    return sesion, clave[:6]


def borrar(numero):
    """Elimina todo lo que el chatbot recuerda de ese usuario."""
    _sesiones.pop(_clave(numero), None)
