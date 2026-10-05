# CTrips

Chatbot de WhatsApp para planificar viajes por Centroamérica. Recomienda destinos de playa, montaña o ciudad, informa sobre hospedaje, transporte y actividades, y calcula el presupuesto del viaje.

Actividad #13 de DAI, Período IV 2026. Autor: José Steven Menéndez Benítez (Tercer Año DS "C", n.º 12).

## Archivos

| Archivo | Para qué sirve |
| --- | --- |
| `app.py` | Servidor Flask que recibe los mensajes de Twilio y devuelve la respuesta |
| `chatbot/nlp.py` | Limpieza del texto y clasificador de intenciones (TF-IDF + SVM) |
| `chatbot/entidades.py` | Detecta destino, tipo, país, días, personas y nivel de gasto |
| `chatbot/flujo.py` | Estados de la conversación y decisión de qué responder |
| `chatbot/presupuesto.py` | Cálculo del costo estimado del viaje |
| `chatbot/sesiones.py` | Memoria temporal y anónima de cada conversación |
| `chatbot/mensajes.py` | Textos que se envían por WhatsApp |
| `chatbot/datos.py` | Carga y consulta del catálogo de destinos |
| `datos/intenciones.json` | Intenciones, frases de entrenamiento y respuestas |
| `datos/destinos.json` | 18 destinos de 5 países con precios de referencia |
| `importaciones.py` | Descarga los recursos de NLTK (una sola vez) |
| `entrenar.py` | Entrena el modelo y crea `model.pkl` |
| `pruebas.py` | Pruebas automáticas de conversación |
| `probar_consola.py` | Chat en la terminal, sin WhatsApp |
| `enviar.py` | Prueba de envío de un mensaje con Twilio |

## Cómo ejecutarlo

Se necesita Python 3.12, una cuenta de Twilio con el Sandbox de WhatsApp y `cloudflared`.

1. Instalar las librerías:

   ```
   pip install -r requirements.txt
   ```

2. Descargar los recursos de NLTK y entrenar el modelo:

   ```
   python importaciones.py
   python entrenar.py
   ```

3. Comprobar que todo funciona (opcional):

   ```
   python pruebas.py
   python probar_consola.py
   ```

4. Iniciar el servidor (queda en el puerto 5000):

   ```
   python app.py
   ```

5. En otra terminal, abrir el túnel:

   ```
   cd C:\cloudflared
   .\cloudflared.exe tunnel --url http://localhost:5000
   ```

6. Copiar la dirección `https://....trycloudflare.com` que aparece y pegarla en Twilio: Messaging, Try it out, Send a WhatsApp message, pestaña Sandbox settings, campo "When a message comes in", método POST, Save.

7. Desde WhatsApp, enviar el código `join ...` del Sandbox al número +1 415 523 8886 y luego escribir `hola`.

## Si algo falla

- El bot no responde: revisar que `app.py` y `cloudflared` sigan abiertos. Cada vez que se reinicia `cloudflared` cambia la dirección y hay que pegarla otra vez en Twilio.
- Twilio dejó de reenviar mensajes: la sesión del Sandbox vence a los tres días; se vuelve a enviar el código `join ...`.
- Abrir la dirección del túnel en el navegador debe mostrar "CTrips esta activo."

## Cómo se usa

Se puede responder con el número de cada opción o escribir con palabras propias, por ejemplo:

- `quiero una playa en Guatemala`
- `hospedaje en Suchitoto`
- `presupuesto para Antigua 3 días 2 personas económico`

Comandos que funcionan en cualquier momento: `menu`, `cancelar`, `ayuda`, `destinos`, `privacidad`, `borrar mis datos`.

Los precios del catálogo son aproximados y sirven solo para planificar.
