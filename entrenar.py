"""Entrena el clasificador de intenciones y lo guarda en model.pkl."""

from collections import Counter

from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVC

from chatbot.nlp import crear_vectorizador, entrenar_modelo, preparar_datos


def evaluar():
    """Validacion cruzada: entrena con una parte de las frases y prueba con las que no vio."""
    oraciones, etiquetas = preparar_datos()
    modelo = make_pipeline(crear_vectorizador(), SVC(kernel="linear"))
    pliegues = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    return cross_val_score(modelo, oraciones, etiquetas, cv=pliegues).mean(), Counter(etiquetas)


if __name__ == "__main__":
    total, clases = entrenar_modelo()
    exactitud, conteo = evaluar()

    print("Modelo entrenado y guardado exitosamente en model.pkl")
    print(f"Frases de entrenamiento: {total} | Intenciones: {clases}")
    for etiqueta, cantidad in sorted(conteo.items()):
        print(f"  {etiqueta}: {cantidad} frases")
    print(f"Exactitud en validacion cruzada: {exactitud:.0%}")
