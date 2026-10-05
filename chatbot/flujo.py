"""Flujo conversacional: decide que responder segun el estado, la intencion y las entidades."""

import random

from . import mensajes, sesiones
from .datos import NIVELES, PAISES, TIPOS, buscar, obtener
from .entidades import a_numero, extraer_entidades
from .nlp import cargar_intenciones, normalizar, predecir_intencion
from .presupuesto import MAX_DIAS, MAX_PERSONAS, calcular, comparar_niveles

# Respuestas fijas de las intenciones simples, leidas de intenciones.json
RESPUESTAS = {i["etiqueta"]: i["respuestas"] for i in cargar_intenciones()}

# Capa de reglas: frases exactas que funcionan en cualquier momento de la conversacion
REGLAS = {
    "menu": "menu", "inicio": "menu", "menu principal": "menu", "volver": "menu", "volver al menu": "menu",
    "cancelar": "cancelar", "cancela": "cancelar",
    "ayuda": "ayuda", "privacidad": "privacidad", "destinos": "destinos",
    "no gracias": "despedida", "salir": "despedida", "me voy": "despedida",
    "eso es todo": "despedida", "eso seria todo": "despedida", "nada mas": "despedida",
    "borrar mis datos": "borrar", "borrar datos": "borrar", "elimina mis datos": "borrar",
    "ok": "acuse", "okay": "acuse", "si": "acuse", "no": "acuse", "vaya": "acuse", "dale": "acuse",
    "bueno": "acuse", "listo": "acuse", "esta bien": "acuse", "jaja": "acuse", "jajaja": "acuse",
}

OPCIONES_MENU = {"1": "recomendar", "2": "hospedaje", "3": "transporte",
                 "4": "actividades", "5": "presupuesto", "6": "ayuda"}
OPCIONES_DESTINO = {"1": "hospedaje", "2": "transporte", "3": "actividades",
                    "4": "presupuesto", "5": "recomendar"}

# Estados en los que el chatbot espera un dato concreto. Ahi solo se acepta cambiar de tema
# si el clasificador esta bastante seguro; si no, lo mas probable es una respuesta mal escrita.
ESPERANDO_DATO = {"TIPO", "PAIS", "ELEGIR", "DIAS", "PERSONAS", "NIVEL"}
UMBRAL_DESVIO = 0.65
# Despedirse borra la conversacion, asi que se exige mas seguridad antes de hacerlo
UMBRAL_DESPEDIDA = 0.70

CONSULTAS = {
    "hospedaje": mensajes.hospedaje,
    "transporte": mensajes.transporte,
    "actividades": mensajes.actividades,
    "epoca": mensajes.epoca,
}


def _opcion(texto, lista):
    """Si el usuario escribio un numero valido de la lista, devuelve ese elemento."""
    if texto.isdigit() and 1 <= int(texto) <= len(lista):
        return lista[int(texto) - 1]
    return None


def _reiniciar(sesion):
    """Vuelve al menu principal olvidando el viaje que se estaba planificando."""
    limpia = sesiones.nueva_sesion()
    limpia["nueva"] = False
    sesion.update(limpia)


def _repreguntar(sesion):
    """Repite la pregunta pendiente para que el usuario sepa como continuar."""
    estado = sesion["estado"]
    destino = obtener(sesion["destino"])
    if estado == "TIPO":
        return mensajes.pedir_tipo()
    if estado == "PAIS":
        return mensajes.pedir_pais(sesion["tipo"])
    if estado == "ELEGIR":
        opciones = [obtener(i) for i in sesion["opciones"]]
        return mensajes.lista_destinos(opciones, sesion["tipo"], sesion["pais"])
    if estado == "CUAL_DESTINO":
        return mensajes.pedir_destino()
    if estado == "DIAS":
        return mensajes.pedir_dias(destino)
    if estado == "PERSONAS":
        return mensajes.pedir_personas()
    if estado == "NIVEL":
        return mensajes.pedir_nivel()
    if estado == "DESTINO":
        return mensajes.submenu(destino)
    return mensajes.PISTA_MENU


def _mostrar_ficha(sesion, destino_id, entrada=""):
    sesion["destino"] = destino_id
    sesion["estado"] = "DESTINO"
    return mensajes.ficha(obtener(destino_id), entrada)


def _avanzar_recomendacion(sesion):
    """Pide el dato que falte (tipo o pais) y, cuando estan completos, muestra los destinos."""
    if sesion["tipo"] is None:
        sesion["estado"] = "TIPO"
        return mensajes.pedir_tipo()
    if sesion["pais"] is None and not sesion["sin_pais"]:
        sesion["estado"] = "PAIS"
        return mensajes.pedir_pais(sesion["tipo"])

    encontrados = buscar(sesion["tipo"], sesion["pais"])
    if len(encontrados) == 1:
        return _mostrar_ficha(sesion, encontrados[0]["id"], "Tengo justo un destino así:\n\n")

    sesion["opciones"] = [d["id"] for d in encontrados]
    sesion["estado"] = "ELEGIR"
    return mensajes.lista_destinos(encontrados, sesion["tipo"], sesion["pais"])


def _avanzar_presupuesto(sesion, entidades):
    """Guarda los datos validos que llegaron y pregunta por el siguiente que falte."""
    aviso = ""
    if "dias" in entidades:
        if 1 <= entidades["dias"] <= MAX_DIAS:
            sesion["dias"] = entidades["dias"]
        else:
            aviso = f"Solo puedo calcular viajes de 1 a {MAX_DIAS} días.\n\n"
    if "personas" in entidades:
        if 1 <= entidades["personas"] <= MAX_PERSONAS:
            sesion["personas"] = entidades["personas"]
        else:
            aviso = f"Solo puedo calcular grupos de 1 a {MAX_PERSONAS} personas.\n\n"
    if "nivel" in entidades:
        sesion["nivel"] = entidades["nivel"]

    destino = obtener(sesion["destino"])
    if destino is None:
        sesion["estado"], sesion["pendiente"] = "CUAL_DESTINO", "presupuesto"
        return aviso + mensajes.pedir_destino()
    if sesion["dias"] is None:
        sesion["estado"] = "DIAS"
        return aviso + mensajes.pedir_dias(destino)
    if sesion["personas"] is None:
        sesion["estado"] = "PERSONAS"
        return aviso + mensajes.pedir_personas()
    if sesion["nivel"] is None:
        sesion["estado"] = "NIVEL"
        return aviso + mensajes.pedir_nivel()

    dias, personas, nivel = sesion["dias"], sesion["personas"], sesion["nivel"]
    texto = mensajes.presupuesto(
        destino, dias, personas, nivel,
        calcular(destino, dias, personas, nivel),
        comparar_niveles(destino, dias, personas),
    )
    # Se limpian los datos para que el siguiente calculo empiece desde cero
    sesion["dias"] = sesion["personas"] = sesion["nivel"] = None
    sesion["estado"] = "DESTINO"
    return f"{texto}\n\n{mensajes.submenu(destino)}"


def _atender(sesion, intencion, entidades):
    """Ejecuta la accion que corresponde a una intencion ya identificada."""
    if intencion == "saludo":
        _reiniciar(sesion)
        return f"{random.choice(RESPUESTAS['saludo'])}\n\n{mensajes.MENU}"
    if intencion == "menu":
        _reiniciar(sesion)
        return mensajes.MENU
    if intencion == "cancelar":
        _reiniciar(sesion)
        return mensajes.CANCELADO + mensajes.MENU

    if intencion == "recomendar":
        if "destino" in entidades:
            return _mostrar_ficha(sesion, entidades["destino"])
        sesion["tipo"] = entidades.get("tipo")
        sesion["pais"] = entidades.get("pais")
        sesion["sin_pais"] = entidades.get("sin_preferencia", False)
        return _avanzar_recomendacion(sesion)

    if intencion == "ficha":
        return _mostrar_ficha(sesion, entidades["destino"])

    if intencion in CONSULTAS:
        if "destino" in entidades:
            sesion["destino"] = entidades["destino"]
        destino = obtener(sesion["destino"])
        if destino is None:
            sesion["estado"], sesion["pendiente"] = "CUAL_DESTINO", intencion
            return mensajes.pedir_destino()
        sesion["estado"] = "DESTINO"
        return f"{CONSULTAS[intencion](destino)}\n\n{mensajes.submenu(destino)}"

    if intencion == "presupuesto":
        if "destino" in entidades:
            sesion["destino"] = entidades["destino"]
        return _avanzar_presupuesto(sesion, entidades)

    if intencion == "destinos":
        sesion["estado"], sesion["pendiente"] = "CUAL_DESTINO", "ficha"
        return mensajes.catalogo()

    if intencion == "acuse":
        return f"Vaya pues.\n\n{_repreguntar(sesion)}"
    if intencion == "ayuda":
        return f"{mensajes.AYUDA}\n\n{_repreguntar(sesion)}"
    if intencion == "privacidad":
        return f"{mensajes.PRIVACIDAD}\n\n{_repreguntar(sesion)}"

    # Intenciones simples (agradecimiento, identidad, fuera de tema): respuesta fija y se retoma el hilo
    return f"{random.choice(RESPUESTAS[intencion])}\n\n{_repreguntar(sesion)}"


def _segun_estado(sesion, texto, entidades):
    """Interpreta el mensaje como respuesta a la pregunta pendiente. Devuelve None si no encaja."""
    estado = sesion["estado"]

    if estado == "MENU":
        if texto in OPCIONES_MENU:
            return _atender(sesion, OPCIONES_MENU[texto], {})
        return mensajes.fuera_de_rango(len(OPCIONES_MENU)) if texto.isdigit() else None

    if estado == "TIPO":
        tipo = entidades.get("tipo") or _opcion(texto, TIPOS)
        if tipo is None:
            return mensajes.fuera_de_rango(len(TIPOS)) if texto.isdigit() else None
        sesion["tipo"] = tipo
        sesion["pais"] = entidades.get("pais")
        return _avanzar_recomendacion(sesion)

    if estado == "PAIS":
        pais = entidades.get("pais") or _opcion(texto, PAISES)
        cualquiera = texto == str(len(PAISES) + 1) or entidades.get("sin_preferencia")
        if pais is None and not cualquiera:
            return mensajes.fuera_de_rango(len(PAISES) + 1) if texto.isdigit() else None
        sesion["pais"], sesion["sin_pais"] = pais, pais is None
        return _avanzar_recomendacion(sesion)

    if estado == "ELEGIR":
        elegido = entidades.get("destino") or _opcion(texto, sesion["opciones"])
        if elegido is None:
            return mensajes.fuera_de_rango(len(sesion["opciones"])) if texto.isdigit() else None
        return _mostrar_ficha(sesion, elegido)

    if estado == "DESTINO":
        if texto in OPCIONES_DESTINO:
            return _atender(sesion, OPCIONES_DESTINO[texto], {})
        return mensajes.fuera_de_rango(len(OPCIONES_DESTINO)) if texto.isdigit() else None

    if estado == "CUAL_DESTINO":
        if "destino" in entidades:
            return _atender(sesion, sesion["pendiente"], entidades)
        if texto == "1" or "tipo" in entidades or "pais" in entidades:
            return _atender(sesion, "recomendar", entidades)
        return None

    # Estados del presupuesto: un numero suelto responde a la pregunta que se acaba de hacer
    if estado in ("DIAS", "PERSONAS"):
        numero = a_numero(texto)
        if numero is not None:
            entidades = {**entidades, estado.lower(): numero}
    if estado == "NIVEL" and _opcion(texto, NIVELES):
        entidades = {**entidades, "nivel": _opcion(texto, NIVELES)}
    if estado in ("DIAS", "PERSONAS", "NIVEL"):
        if any(clave in entidades for clave in ("dias", "personas", "nivel")):
            return _avanzar_presupuesto(sesion, entidades)
        return mensajes.fuera_de_rango(len(NIVELES)) if estado == "NIVEL" and texto.isdigit() else None

    return None


def _por_entidades(sesion, entidades):
    """Cuando no hay intencion clara, las entidades indican que quiere el usuario."""
    if "destino" in entidades:
        return _atender(sesion, "ficha", entidades)
    if "tipo" in entidades or "pais" in entidades:
        return _atender(sesion, "recomendar", entidades)
    if "dias" in entidades or "personas" in entidades:
        return _atender(sesion, "presupuesto", entidades)
    return None


def _no_entendido(sesion):
    """Respuesta de respaldo: cada fallo seguido ofrece mas ayuda que el anterior."""
    if sesion["nueva"]:
        return f"{random.choice(RESPUESTAS['saludo'])}\n\n{mensajes.MENU}"
    sesion["fallos"] += 1
    if sesion["fallos"] >= 3:
        _reiniciar(sesion)
        return mensajes.REINICIO_POR_FALLOS + mensajes.MENU
    if sesion["estado"] == "MENU":
        return f"{mensajes.NO_ENTENDI} Probá con una de estas opciones.\n\n{mensajes.MENU}"
    if sesion["fallos"] == 2:
        return f"{mensajes.NO_ENTENDI_OTRA_VEZ}\n\n{_repreguntar(sesion)}{mensajes.SALIDAS}"
    return f"{mensajes.NO_ENTENDI}\n\n{_repreguntar(sesion)}"


def responder(numero, mensaje):
    """Punto de entrada del chatbot: recibe el mensaje de un usuario y devuelve la respuesta."""
    sesion, anonimo = sesiones.obtener(numero)
    texto = normalizar(mensaje)
    if not texto:
        return mensajes.SOLO_TEXTO

    entidades = extraer_entidades(texto)
    estado_inicial = sesion["estado"]
    intencion, confianza, respuesta = None, 0.0, None

    # 1. Reglas exactas (menu, cancelar, borrar mis datos...)
    if texto in REGLAS:
        intencion, confianza = REGLAS[texto], 1.0
    # 2. Respuesta a la pregunta que el chatbot acaba de hacer
    else:
        respuesta = _segun_estado(sesion, texto, entidades)
        if respuesta is not None:
            intencion, confianza = "respuesta_esperada", 1.0
        # 3. Clasificador SVM para los mensajes escritos con palabras propias
        else:
            esperando = estado_inicial in ESPERANDO_DATO
            intencion, confianza = predecir_intencion(texto, estricto=esperando)
            if esperando and confianza < UMBRAL_DESVIO:
                intencion = None
            if intencion == "despedida" and confianza < UMBRAL_DESPEDIDA:
                intencion = None

    # El registro no incluye ni el numero ni el texto del mensaje
    print(f"[{anonimo}] estado={estado_inicial} intencion={intencion} "
          f"confianza={confianza:.2f} entidades={sorted(entidades)}")

    if intencion == "borrar":
        sesiones.borrar(numero)
        return mensajes.DATOS_BORRADOS
    if intencion == "despedida":
        sesiones.borrar(numero)
        return random.choice(RESPUESTAS["despedida"])

    if respuesta is None and intencion is not None:
        respuesta = _atender(sesion, intencion, entidades)
    # 4. Sin intencion clara: se intenta deducir la accion a partir de las entidades
    if respuesta is None:
        respuesta = _por_entidades(sesion, entidades)

    if respuesta is None:
        respuesta = _no_entendido(sesion)
    else:
        sesion["fallos"] = 0
        # En el primer mensaje el chatbot se presenta, salvo que el saludo ya lo haya hecho
        if sesion["nueva"] and intencion != "saludo":
            respuesta = mensajes.PRESENTACION + respuesta

    sesion["nueva"] = False
    return respuesta
