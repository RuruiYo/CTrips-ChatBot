"""Servidor Flask que conecta el chatbot con WhatsApp por medio de Twilio."""

import os

from flask import Flask, Response, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from chatbot import mensajes
from chatbot.flujo import responder
from chatbot.nlp import cargar_modelo

app = Flask(__name__)

# El modelo se carga al arrancar para que el primer mensaje no tarde
cargar_modelo()

# Las credenciales nunca se escriben en el codigo: se leen de variables de entorno.
# Con credenciales, la respuesta se envia por la API de Twilio; sin ellas, se devuelve TwiML.
ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
client = Client(ACCOUNT_SID, AUTH_TOKEN) if ACCOUNT_SID and AUTH_TOKEN else None


@app.route("/", methods=["GET"])
def estado():
    """Permite comprobar desde el navegador que el servidor y el tunel funcionan."""
    return "CTrips esta activo."


@app.route("/", methods=["POST"])
def whatsapp_reply():
    """Twilio llama a esta ruta cada vez que llega un mensaje de WhatsApp."""
    # Twilio envia un formulario; se acepta tambien JSON por si la consola cambia el formato
    datos = request.form or request.get_json(silent=True) or {}
    incoming_msg = str(datos.get("Body", "")).strip()
    from_number = datos.get("From", "desconocido")
    to_number = datos.get("To", "")

    try:
        texto = responder(from_number, incoming_msg)
    except Exception as error:
        # Pase lo que pase, el usuario siempre recibe una respuesta
        print(f"Error al procesar un mensaje: {error!r}")
        texto = mensajes.ERROR_TECNICO

    partes = mensajes.dividir_mensaje(texto)

    # Modo API: el chatbot envia la respuesta como un mensaje nuevo desde el numero de Twilio
    if client is not None:
        try:
            for parte in partes:
                client.messages.create(body=parte, from_=to_number, to=from_number)
            print("Respuesta enviada por la API de Twilio.")
        except Exception as error:
            print(f"Twilio rechazo el envio: {error}")
        return Response("", status=200)

    # Modo TwiML: la respuesta viaja en el cuerpo de la misma peticion
    response = MessagingResponse()
    for parte in partes:
        response.message(parte)
    return Response(str(response), mimetype="application/xml")


if __name__ == "__main__":
    modo = "API de Twilio" if client is not None else "TwiML"
    print(f"CTrips responde en modo: {modo}")
    # Puerto 5000: el mismo que se expone con cloudflared
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
