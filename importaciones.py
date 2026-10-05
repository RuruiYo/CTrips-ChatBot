"""Descarga unica de los recursos de NLTK que usa el chatbot. Ejecutar una sola vez."""

import nltk

# Tokenizador que separa una oracion en palabras
nltk.download("punkt_tab")
# Lista de palabras vacias en espanol ("el", "de", "que"...)
nltk.download("stopwords")
