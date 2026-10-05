"""Conversa con el chatbot desde la terminal, sin WhatsApp. Sirve para probar rapido."""

from chatbot.flujo import responder

USUARIO_DE_PRUEBA = "whatsapp:+50300000000"


def chat():
    print("CTrips en modo consola. Escribe 'fin' para cerrar.\n")
    while True:
        entrada = input("Tu: ")
        if entrada.strip().lower() == "fin":
            break
        print(f"\nCTrips:\n{responder(USUARIO_DE_PRUEBA, entrada)}\n")


if __name__ == "__main__":
    chat()
