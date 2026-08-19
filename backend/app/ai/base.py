from abc import ABC, abstractmethod
from typing import TypedDict

TOPICS = [
    "tutor_docente",
    "contenidos_material",
    "aula_virtual_plataforma",
    "administracion_gestion",
    "felicitaciones_general",
    "sugerencias_mejora",
    "otro",
    "sin_comentario",
]

TOPIC_LABELS = {
    "tutor_docente": "Tutoría y Docencia",
    "contenidos_material": "Contenidos y Material Didáctico",
    "aula_virtual_plataforma": "Aula Virtual y Plataforma",
    "administracion_gestion": "Atención Administrativa",
    "felicitaciones_general": "Felicitaciones y Agradecimientos",
    "sugerencias_mejora": "Sugerencias de Mejora",
    "otro": "Otros",
    "sin_comentario": "Sin comentarios",
}


class ClassificationResult(TypedDict):
    topic: str
    sentiment: str  # "positivo" | "negativo" | "neutro"


class CommentAnalyzer(ABC):
    """
    Interfaz común para el análisis de comentarios abiertos.
    """

    @abstractmethod
    def classify(self, comment: str) -> ClassificationResult:
        """Clasifica un comentario individual por tema y sentimiento."""
        ...

    @abstractmethod
    def summarize(self, comments: list[str]) -> str:
        """Genera un resumen ejecutivo a partir de una lista de comentarios."""
        ...
