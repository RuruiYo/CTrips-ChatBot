"""Carga el catalogo de destinos y ofrece funciones para consultarlo."""

import json
from pathlib import Path

RUTA_DESTINOS = Path(__file__).resolve().parent.parent / "datos" / "destinos.json"

with open(RUTA_DESTINOS, "r", encoding="utf-8") as archivo:
    _catalogo = json.load(archivo)

DESTINOS = _catalogo["destinos"]
ORIGEN = _catalogo["origen"]
POR_ID = {d["id"]: d for d in DESTINOS}

# El orden de estas listas define los numeros que ve el usuario en los menus
TIPOS = ["playa", "montana", "ciudad"]
PAISES = ["El Salvador", "Guatemala", "Honduras", "Nicaragua", "Costa Rica"]
NIVELES = ["economico", "medio", "confort"]

NOMBRE_TIPO = {"playa": "playa", "montana": "montaña", "ciudad": "ciudad"}
NOMBRE_NIVEL = {"economico": "económico", "medio": "medio", "confort": "confort"}


def obtener(destino_id):
    return POR_ID.get(destino_id)


def buscar(tipo=None, pais=None):
    """Filtra los destinos por tipo y pais; si un filtro es None, no se aplica."""
    return [
        d for d in DESTINOS
        if (tipo is None or d["tipo"] == tipo) and (pais is None or d["pais"] == pais)
    ]


def precio_desde(destino):
    """Precio por noche de la opcion de hospedaje mas barata."""
    return min(h["precio"] for h in destino["hospedaje"])
