"""Procesamiento de lenguaje natural: limpia el texto y clasifica la intencion con un modelo SVM."""

import json
import pickle
import string
import unicodedata
from pathlib import Path

import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_union
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

from .entidades import quitar_destino

RAIZ = Path(__file__).resolve().parent.parent
RUTA_INTENCIONES = RAIZ / "datos" / "intenciones.json"
RUTA_MODELO = RAIZ / "model.pkl"

# Si la confianza del modelo queda por debajo de este valor, el chatbot admite que no entendio
UMBRAL_CONFIANZA = 0.40
# Parecido minimo (de 0 a 1) entre el mensaje y la frase de entrenamiento mas cercana
UMBRAL_PARECIDO = 0.30

PUNTUACION = string.punctuation + "¿¡"
raiz_palabras = SnowballStemmer("spanish")
_modelo = None


def _asegurar_recursos():
    """Descarga los recursos de NLTK solo si todavia no estan en la computadora."""
    for carpeta, paquete in (("tokenizers/punkt_tab", "punkt_tab"), ("corpora/stopwords", "stopwords")):
        try:
            nltk.data.find(carpeta)
        except LookupError:
            nltk.download(paquete, quiet=True)


def normalizar(texto):
    """Pasa a minusculas y quita tildes y signos: 'Montaña, ¿cuánto?' queda 'montana cuanto'."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = "".join(" " if c in PUNTUACION else c for c in texto)
    return " ".join(texto.split())


_asegurar_recursos()

# De las stopwords de NLTK solo se eliminan articulos, preposiciones y conjunciones.
# Palabras como "que", "como" o "cuanto" se conservan: en una pregunta corta definen la intencion.
SIN_SIGNIFICADO = {"el", "la", "los", "las", "un", "una", "unos", "de", "del", "al", "a",
                   "en", "y", "o", "por", "con", "lo", "le", "se", "su", "sus"}
PALABRAS_VACIAS = {normalizar(p) for p in stopwords.words("spanish")} & SIN_SIGNIFICADO


def preproceso(oracion):
    """Quita el nombre del destino, tokeniza, elimina stopwords y reduce cada palabra a su raiz."""
    texto = quitar_destino(normalizar(oracion))
    tokens = nltk.word_tokenize(texto, language="spanish")
    return " ".join(raiz_palabras.stem(t) for t in tokens if t not in PALABRAS_VACIAS)


def crear_vectorizador():
    """TF-IDF de palabras (y pares de palabras) mas TF-IDF de trozos de letras.

    Los trozos de 2 a 4 letras hacen que "ospedaje" siga pareciendose a "hospedaje".
    """
    return make_union(
        TfidfVectorizer(ngram_range=(1, 2)),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4)),
    )


def crear_clasificador():
    """SVM lineal calibrado para que entregue una probabilidad por cada intencion."""
    return CalibratedClassifierCV(SVC(kernel="linear"), ensemble=False, cv=5)


def cargar_intenciones():
    with open(RUTA_INTENCIONES, "r", encoding="utf-8") as archivo:
        return json.load(archivo)["intenciones"]


def preparar_datos():
    """Devuelve las oraciones ya preprocesadas y la etiqueta de cada una."""
    oraciones, etiquetas = [], []
    for intencion in cargar_intenciones():
        for patron in intencion["patrones"]:
            oraciones.append(preproceso(patron))
            etiquetas.append(intencion["etiqueta"])
    return oraciones, etiquetas


def entrenar_modelo():
    """Vectoriza las frases, entrena el SVM y guarda todo en model.pkl."""
    global _modelo
    oraciones, etiquetas = preparar_datos()

    vectorizar = crear_vectorizador()
    X = vectorizar.fit_transform(oraciones)

    le = LabelEncoder()
    y = le.fit_transform(etiquetas)

    model = crear_clasificador()
    model.fit(X, y)

    # Las frases vectorizadas tambien se guardan: sirven para medir que tan conocido es un mensaje
    _modelo = (vectorizar, le, model, X)
    with open(RUTA_MODELO, "wb") as archivo:
        pickle.dump(_modelo, archivo)

    return len(oraciones), len(le.classes_)


def cargar_modelo():
    """Carga model.pkl una sola vez; si no existe o no es compatible, lo entrena de nuevo."""
    global _modelo
    if _modelo is None:
        try:
            with open(RUTA_MODELO, "rb") as archivo:
                _modelo = pickle.load(archivo)
            _modelo[0].transform(["prueba"])
        except Exception:
            entrenar_modelo()
    return _modelo


def predecir_intencion(texto, estricto=False):
    """Devuelve (etiqueta, confianza). La etiqueta es None cuando el modelo no esta seguro.

    Con estricto=True se exige que al menos una palabra completa sea conocida,
    es decir, se desactiva la tolerancia a errores de escritura.
    """
    vectorizar, le, model, frases = cargar_modelo()
    procesado = preproceso(texto)
    X = vectorizar.transform([procesado])

    por_palabras = vectorizar.transformer_list[0][1]
    if estricto and por_palabras.transform([procesado]).nnz == 0:
        return None, 0.0

    # Un mensaje que no se parece a ninguna frase conocida no se clasifica: mejor preguntar que adivinar.
    # Cada mitad del vector (palabras y letras) tiene longitud 1, por eso el producto se divide entre 2.
    parecido = (X @ frases.T).max() / 2 if X.nnz else 0.0
    if parecido < UMBRAL_PARECIDO:
        return None, 0.0

    confianza = model.predict_proba(X)[0]
    indice = confianza.argmax()
    etiqueta = str(le.inverse_transform([indice])[0])
    maxima = float(confianza[indice])

    if maxima < UMBRAL_CONFIANZA:
        return None, maxima
    return etiqueta, maxima
