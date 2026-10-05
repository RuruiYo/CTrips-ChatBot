"""Extraccion de entidades: tipo de viaje, pais, destino, dias, personas y nivel de gasto."""

import re
from difflib import get_close_matches

from .datos import DESTINOS

# Palabras que delatan cada entidad (todas ya normalizadas: minusculas y sin tildes)
PALABRAS_TIPO = {
    "playa": ["playa", "playas", "mar", "surf", "oceano", "arena", "isla"],
    "montana": ["montana", "montanas", "volcan", "volcanes", "bosque", "senderismo",
                "naturaleza", "lago", "cerro", "frio", "caminata"],
    "ciudad": ["ciudad", "ciudades", "colonial", "cultura", "historia", "museo",
               "museos", "pueblo", "ruinas", "arquitectura"],
}

PALABRAS_PAIS = {
    "El Salvador": ["el salvador", "salvador", "salvadoreno", "guanaco"],
    "Guatemala": ["guatemala", "guate"],
    "Honduras": ["honduras"],
    "Nicaragua": ["nicaragua", "nica"],
    "Costa Rica": ["costa rica", "tico"],
}

# Frases con las que el usuario dice que el pais le da igual
SIN_PREFERENCIA = ["cualquiera", "cualquier", "todos", "da igual", "no importa", "donde sea", "sorprendeme"]

PALABRAS_NIVEL = {
    "economico": ["economico", "economica", "barato", "barata", "mochilero", "bajo", "ahorrar", "poco dinero"],
    "medio": ["medio", "moderado", "normal", "intermedio", "estandar"],
    "confort": ["confort", "lujo", "lujoso", "comodo", "alto", "premium", "caro"],
}

NUMEROS = {
    "un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
    "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "doce": 12, "quince": 15,
}
_NUM = r"(\d+|" + "|".join(NUMEROS) + r")"

# Alias de destinos ordenados del mas largo al mas corto para que
# "volcan de santa ana" gane sobre "santa ana"
_ALIAS = sorted(
    ((alias, d["id"]) for d in DESTINOS for alias in d["alias"]),
    key=lambda par: len(par[0]),
    reverse=True,
)
_ALIAS_DE_UNA_PALABRA = {alias: destino_id for alias, destino_id in _ALIAS if " " not in alias}


def _contiene(texto, frase):
    """Busca la frase como palabra completa, para que 'mar' no aparezca dentro de 'marzo'."""
    return re.search(rf"\b{re.escape(frase)}\b", texto) is not None


def a_numero(palabra):
    """Convierte '3' o 'tres' en 3; devuelve None si no es un numero."""
    if palabra.isdigit():
        return int(palabra)
    return NUMEROS.get(palabra)


def _buscar_en(texto, diccionario):
    for valor, palabras in diccionario.items():
        if any(_contiene(texto, p) for p in palabras):
            return valor
    return None


def _ubicar_destino(texto):
    """Devuelve (id del destino, fragmento del texto donde se menciona)."""
    for alias, destino_id in _ALIAS:
        if _contiene(texto, alias):
            return destino_id, alias
    # Tolerancia a errores de escritura: 'suchitto' se parece lo suficiente a 'suchitoto'
    for palabra in texto.split():
        if len(palabra) >= 5:
            parecidos = get_close_matches(palabra, _ALIAS_DE_UNA_PALABRA, n=1, cutoff=0.85)
            if parecidos:
                return _ALIAS_DE_UNA_PALABRA[parecidos[0]], palabra
    return None, None


def extraer_destino(texto):
    return _ubicar_destino(texto)[0]


def quitar_destino(texto):
    """Quita el nombre del destino para que el clasificador se fije solo en la intencion."""
    _, fragmento = _ubicar_destino(texto)
    if fragmento is None:
        return texto
    return re.sub(rf"\b{re.escape(fragmento)}\b", " ", texto).strip()


def extraer_dias(texto):
    if _contiene(texto, "fin de semana"):
        return 2
    semanas = re.search(rf"\b{_NUM}\s+semanas?\b", texto)
    if semanas:
        return a_numero(semanas.group(1)) * 7
    dias = re.search(rf"\b{_NUM}\s+dias?\b", texto)
    if dias:
        return a_numero(dias.group(1))
    # Quien dice "2 noches" viaja 3 dias
    noches = re.search(rf"\b{_NUM}\s+noches?\b", texto)
    if noches:
        return a_numero(noches.group(1)) + 1
    return None


def extraer_personas(texto):
    grupo = re.search(rf"\b{_NUM}\s+(?:personas?|adultos?|amigos|amigas|viajeros|pax)\b", texto)
    if grupo:
        return a_numero(grupo.group(1))
    somos = re.search(rf"\b(?:somos|vamos|iremos|seremos)\s+{_NUM}\b", texto)
    if somos:
        return a_numero(somos.group(1))
    if any(_contiene(texto, f) for f in ("en pareja", "mi pareja", "mi novia", "mi novio", "mi esposa", "mi esposo")):
        return 2
    if any(_contiene(texto, f) for f in ("voy solo", "voy sola", "viajo solo", "viajo sola", "yo solo", "yo sola")):
        return 1
    return None


def extraer_entidades(texto):
    """Recibe el texto normalizado y devuelve solo las entidades que encontro."""
    encontradas = {
        "destino": extraer_destino(texto),
        "tipo": _buscar_en(texto, PALABRAS_TIPO),
        "pais": _buscar_en(texto, PALABRAS_PAIS),
        "dias": extraer_dias(texto),
        "personas": extraer_personas(texto),
        "nivel": _buscar_en(texto, PALABRAS_NIVEL),
    }
    if any(_contiene(texto, f) for f in SIN_PREFERENCIA):
        encontradas["sin_preferencia"] = True
    return {clave: valor for clave, valor in encontradas.items() if valor is not None}
