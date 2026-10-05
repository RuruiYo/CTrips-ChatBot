"""Textos que el chatbot envia por WhatsApp. Aqui no hay logica, solo redaccion."""

from .datos import DESTINOS, NIVELES, NOMBRE_NIVEL, NOMBRE_TIPO, ORIGEN, PAISES, precio_desde

MENU = (
    "¿Qué querés hacer?\n"
    "*1* Recomendarme un destino\n"
    "*2* Ver hospedaje\n"
    "*3* Ver transporte\n"
    "*4* Ver actividades\n"
    "*5* Calcular presupuesto\n"
    "*6* Ayuda y privacidad\n\n"
    "También podés escribirlo con tus palabras, por ejemplo: _quiero una playa en Guatemala_."
)

AYUDA = (
    "*Así me usás:*\n"
    "- Respondé con el *número* de la opción o escribí con tus palabras.\n"
    "- Ejemplos: _quiero montaña en Costa Rica_, _hospedaje en Suchitoto_, "
    "_presupuesto para 3 días 2 personas_.\n"
    "- *menu* vuelve al inicio y *cancelar* detiene lo que estemos haciendo.\n"
    "- *destinos* muestra todos los lugares que conozco.\n"
    "- *privacidad* explica qué datos uso y *borrar mis datos* los elimina.\n\n"
    "Los precios que doy son aproximados: sirven para planificar, confirmalos antes de reservar."
)

PRIVACIDAD = (
    "*Tu privacidad:*\n"
    "- No guardo tu número: lo convierto en un código anónimo.\n"
    "- Solo recuerdo lo necesario para esta conversación (destino, días y personas). "
    "Se borra al despedirte o tras 30 minutos sin actividad.\n"
    "- No guardo el texto de tus mensajes ni comparto datos con nadie.\n"
    "- El mensaje viaja por WhatsApp y Twilio, que tienen sus propias políticas.\n"
    "- Escribí *borrar mis datos* y los elimino de inmediato."
)

PRESENTACION = "Soy *CTrips*, un asistente virtual de viajes por Centroamérica.\n\n"
SOLO_TEXTO = "Por ahora solo entiendo mensajes de texto. Escribime qué viaje tenés en mente o escribí *menu*."
DATOS_BORRADOS = "Listo, borré todo lo que recordaba de esta conversación. Escribí *hola* si querés empezar de nuevo."
CANCELADO = "Listo, cancelé lo que estábamos haciendo.\n\n"
ERROR_TECNICO = "Tuve un problema técnico, disculpá. Escribí *menu* para intentarlo de nuevo."
PISTA_MENU = "Escribí *menu* para ver las opciones."
NO_ENTENDI = "Disculpá, no te entendí."
NO_ENTENDI_OTRA_VEZ = "Sigo sin entenderte, disculpá."
REINICIO_POR_FALLOS = "No logro entenderte y no quiero hacerte perder el tiempo. Volvamos al inicio.\n\n"
SALIDAS = "\n\nSi preferís, escribí *menu* para volver al inicio o *ayuda* para ver ejemplos."
AVISO_PRECIOS = "Son precios de referencia en dólares; confirmalos antes de reservar."


def dinero(cantidad):
    return "gratis" if cantidad == 0 else f"${cantidad:,}"


def fuera_de_rango(maximo):
    return f"Esa opción no existe. Elegí un número del 1 al {maximo}."


def pedir_tipo():
    return "¿Qué tipo de viaje buscás?\n*1* Playa\n*2* Montaña\n*3* Ciudad"


def pedir_pais(tipo):
    lineas = [f"¿En qué país querés tu viaje de {NOMBRE_TIPO[tipo]}?"]
    lineas += [f"*{i}* {pais}" for i, pais in enumerate(PAISES, start=1)]
    lineas.append(f"*{len(PAISES) + 1}* Cualquiera, sorprendeme")
    return "\n".join(lineas)


def lista_destinos(destinos, tipo, pais):
    donde = f" en *{pais}*" if pais else " en Centroamérica"
    lineas = [f"Estas son mis opciones de *{NOMBRE_TIPO[tipo]}*{donde}:"]
    for i, d in enumerate(destinos, start=1):
        lugar = "" if pais else f" ({d['pais']})"
        lineas.append(f"*{i}* {d['nombre']}{lugar}: {d['resumen']}, desde {dinero(precio_desde(d))} la noche")
    lineas.append("\nRespondé con el número o con el nombre del destino.")
    return "\n".join(lineas)


def submenu(destino):
    return (
        f"¿Qué querés saber de {destino['nombre']}?\n"
        "*1* Hospedaje\n*2* Transporte\n*3* Actividades\n*4* Calcular presupuesto\n*5* Ver otro destino"
    )


def ficha(destino, entrada=""):
    return (
        f"{entrada}*{destino['nombre']}* ({destino['pais']}, {NOMBRE_TIPO[destino['tipo']]})\n"
        f"{destino['descripcion']}\n\n"
        f"Mejor época: {destino['mejor_epoca']}.\n"
        f"Hospedaje desde {dinero(precio_desde(destino))} la noche.\n\n"
        f"{submenu(destino)}"
    )


def hospedaje(destino):
    lineas = [f"*Hospedaje en {destino['nombre']}* (precio por noche)"]
    for h in destino["hospedaje"]:
        lineas.append(f"- {NOMBRE_NIVEL[h['nivel']].capitalize()}: {h['opcion']}, {dinero(h['precio'])}")
    lineas.append(f"\n{AVISO_PRECIOS}")
    return "\n".join(lineas)


def transporte(destino):
    t = destino["transporte"]
    texto = (
        f"*Cómo llegar a {destino['nombre']}* (desde {ORIGEN})\n"
        f"{t['como_llegar']}\n"
        f"Tiempo: {t['tiempo']}.\n"
        f"Costo aproximado ida y vuelta: {dinero(t['costo_ida_vuelta'])} por persona.\n\n"
        "Horarios y tarifas cambian; verificalos antes de salir."
    )
    if destino["pais"] != "El Salvador":
        texto += (
            "\nPara salir del país llevá tu documento de viaje vigente y confirmá "
            "los requisitos migratorios antes de viajar."
        )
    return texto


def actividades(destino):
    lineas = [f"*Qué hacer en {destino['nombre']}*"]
    lineas += [f"- {a['nombre']}: {dinero(a['precio'])}" for a in destino["actividades"]]
    lineas.append(f"\n{AVISO_PRECIOS}")
    return "\n".join(lineas)


def epoca(destino):
    return f"*Mejor época para ir a {destino['nombre']}:* {destino['mejor_epoca']}."


def catalogo():
    lineas = ["*Destinos que conozco:*"]
    for pais in PAISES:
        nombres = [f"{d['nombre']} ({NOMBRE_TIPO[d['tipo']]})" for d in DESTINOS if d["pais"] == pais]
        lineas.append(f"*{pais}:* " + ", ".join(nombres))
    lineas.append("\nEscribí el nombre del destino que te interesa.")
    return "\n".join(lineas)


def pedir_destino():
    return (
        "¿De qué destino? Escribí el nombre, por ejemplo _Suchitoto_ o _Antigua_.\n"
        "Si todavía no tenés uno, escribí *1* y te recomiendo, o *destinos* para ver la lista."
    )


def pedir_dias(destino):
    return f"Vamos con el presupuesto para *{destino['nombre']}*.\n¿Cuántos días dura el viaje? Escribí solo el número, por ejemplo: 3"


def pedir_personas():
    return "¿Cuántas personas viajan? Escribí solo el número, por ejemplo: 2"


def pedir_nivel():
    return (
        "¿Qué nivel de gasto preferís?\n"
        "*1* Económico (hostales y comida sencilla)\n"
        "*2* Medio (hotel cómodo y restaurantes)\n"
        "*3* Confort (los mejores hoteles)"
    )


def presupuesto(destino, dias, personas, nivel, calculo, comparacion):
    viajeros = "1 persona" if personas == 1 else f"{personas} personas"
    duracion = "1 día, sin noche de hotel" if dias == 1 else f"{dias} días ({calculo['noches']} noches)"
    cuartos = "1 habitación" if calculo["habitaciones"] == 1 else f"{calculo['habitaciones']} habitaciones"
    otros = [
        f"{NOMBRE_NIVEL[n]} ${comparacion[n]:,}" for n in NIVELES if n != nivel
    ]
    return (
        f"*Presupuesto estimado: {destino['nombre']}*\n"
        f"{duracion}, {viajeros}, nivel {NOMBRE_NIVEL[nivel]}\n\n"
        f"Hospedaje ({cuartos}): ${calculo['hospedaje']:,}\n"
        f"Comida: ${calculo['comida']:,}\n"
        f"Actividades: ${calculo['actividades']:,}\n"
        f"Transporte ida y vuelta: ${calculo['transporte']:,}\n"
        f"Imprevistos (10%): ${calculo['imprevistos']:,}\n"
        f"*Total: ${calculo['total']:,}* (unos ${calculo['por_persona']:,} por persona)\n\n"
        f"Para comparar, el mismo viaje en nivel {' y en nivel '.join(otros)}.\n"
        "Es una estimación para planificar, no una cotización."
    )


def dividir_mensaje(texto, limite=1500):
    """Parte un texto largo en bloques, porque WhatsApp por Twilio admite hasta 1600 caracteres."""
    partes, actual = [], ""
    for bloque in texto.split("\n\n"):
        if actual and len(actual) + len(bloque) + 2 > limite:
            partes.append(actual)
            actual = bloque
        else:
            actual = f"{actual}\n\n{bloque}" if actual else bloque
    partes.append(actual)
    return partes
