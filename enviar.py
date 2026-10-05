"""Prueba de conexion con Twilio: envia un mensaje de WhatsApp a tu numero.

Las credenciales se leen de variables de entorno para no dejarlas escritas en el codigo.
"""

import os

from twilio.rest import Client

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)

from_whatsapp_number = "whatsapp:+14155238886"
to_whatsapp_number = os.environ["MI_WHATSAPP"]

client.messages.create(
    body="Hola, soy CTrips. La conexion con Twilio funciona.",
    from_=from_whatsapp_number,
    to=to_whatsapp_number,
)
print("Mensaje enviado.")
