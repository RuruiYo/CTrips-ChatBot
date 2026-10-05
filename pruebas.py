"""Pruebas de interaccion: simula conversaciones completas y comprueba cada respuesta.

Ejecutar con:  python pruebas.py
"""

import contextlib
import io
import os

# Las pruebas no deben enviar mensajes reales: se fuerza el modo TwiML antes de cargar el servidor
os.environ.pop("TWILIO_ACCOUNT_SID", None)
os.environ.pop("TWILIO_AUTH_TOKEN", None)

from app import app
from chatbot.flujo import responder

resultados = []


def conversar(usuario, pasos):
    """Envia cada mensaje y verifica que la respuesta contenga los textos esperados."""
    for mensaje, esperados in pasos:
        # Se oculta el registro de consola para que el reporte de pruebas quede limpio
        with contextlib.redirect_stdout(io.StringIO()):
            respuesta = responder(usuario, mensaje)
        faltantes = [e for e in esperados if e.lower() not in respuesta.lower()]
        resultados.append((usuario, mensaje, not faltantes))
        if faltantes:
            print(f"  FALLO [{usuario}] '{mensaje}': falta {faltantes}\n  Respondio: {respuesta[:200]}")


def prueba(nombre, pasos):
    antes = len(resultados)
    conversar(nombre, pasos)
    correctas = sum(1 for r in resultados[antes:] if r[2])
    print(f"{'OK   ' if correctas == len(pasos) else 'FALLO'} {nombre}: {correctas}/{len(pasos)} respuestas correctas")


prueba("Flujo guiado por menu", [
    ("hola", ["CTrips", "*1* Recomendarme"]),
    ("1", ["tipo de viaje"]),
    ("1", ["país"]),
    ("1", ["El Tunco", "El Cuco"]),
    ("1", ["*El Tunco*", "Mejor época"]),
    ("1", ["Hospedaje en El Tunco", "$15"]),
    ("2", ["ruta 102"]),
    ("3", ["Clase de surf"]),
])

prueba("Frase libre con dos entidades", [
    ("quiero una montaña en Costa Rica", ["Monteverde"]),
    ("donde me puedo quedar", ["Hospedaje en Monteverde"]),
])

prueba("Presupuesto en un solo mensaje", [
    ("presupuesto para Suchitoto 3 dias 2 personas economico", ["Presupuesto estimado: Suchitoto", "Total: $183"]),
])

prueba("Presupuesto con datos incompletos", [
    ("cuanto cuesta el viaje", ["¿De qué destino?"]),
    ("antigua", ["Cuántos días"]),
    ("ayuda", ["Así me usás", "Cuántos días"]),
    ("un monton", ["no te entendí", "Cuántos días"]),
    ("0", ["de 1 a 30"]),
    ("5", ["Cuántas personas"]),
    ("cuatro", ["nivel de gasto"]),
    ("9", ["del 1 al 3"]),
    ("2", ["Presupuesto estimado: Antigua Guatemala", "2 habitaciones"]),
])

prueba("Errores de escritura", [
    ("ospedaje en suchitto", ["Hospedaje en Suchitoto"]),
    ("como yego a rotan", ["Cómo llegar a Roatán"]),
    ("actibidades en copan", ["Qué hacer en Copán Ruinas"]),
])

prueba("Desvio a mitad del flujo", [
    ("recomiendame un destino", ["tipo de viaje"]),
    ("privacidad", ["Tu privacidad", "tipo de viaje"]),
    ("ciudad", ["país"]),
    ("gracias", ["país"]),
    ("guatemala", ["Antigua Guatemala"]),
])

prueba("Mensajes no reconocidos", [
    ("hola", ["CTrips"]),
    ("asdfgh", ["no te entendí", "*1* Recomendarme"]),
    ("9", ["del 1 al 6"]),
    ("cuentame un chiste", ["Centroamérica"]),
])

prueba("Tres fallos seguidos reinician", [
    ("actividades", ["¿De qué destino?"]),
    ("zzzz", ["no te entendí"]),
    ("qqqq", ["Sigo sin entenderte", "*menu*"]),
    ("wwww", ["Volvamos al inicio", "*1* Recomendarme"]),
])

prueba("Comandos globales y privacidad", [
    ("quiero ir a granada", ["*Granada*"]),
    ("4", ["Cuántos días"]),
    ("cancelar", ["cancelé", "*1* Recomendarme"]),
    ("destinos", ["Destinos que conozco", "Roatán"]),
    ("ometepe", ["*Isla de Ometepe*"]),
    ("borrar mis datos", ["borré todo"]),
    ("3", ["CTrips"]),
])

prueba("Identidad y despedida", [
    ("eres una persona?", ["chatbot"]),
    ("adios", ["datos"]),
])

# Prueba del servidor: se envia un mensaje con el mismo formato que usa Twilio
with contextlib.redirect_stdout(io.StringIO()):
    cliente = app.test_client()
    respuesta_http = cliente.post("/", data={"From": "whatsapp:+50370000000", "Body": "Hola"})
    vacio = cliente.post("/", data={"From": "whatsapp:+50370000000", "Body": ""})
cuerpo = respuesta_http.get_data(as_text=True)
servidor_ok = (
    respuesta_http.status_code == 200
    and "<Response><Message>" in cuerpo
    and "CTrips" in cuerpo
    and "solo entiendo mensajes de texto" in vacio.get_data(as_text=True)
)
resultados.append(("servidor", "POST /", servidor_ok))
print(f"{'OK   ' if servidor_ok else 'FALLO'} Servidor Flask: responde en formato TwiML")

aprobadas = sum(1 for r in resultados if r[2])
print(f"\nTotal: {aprobadas}/{len(resultados)} comprobaciones correctas")
