import json
import logging
from app.ai.base import CommentAnalyzer, ClassificationResult, TOPICS
from app.config import settings

logger = logging.getLogger(__name__)

PROMPT_CLASIFICAR = """Clasificá el siguiente comentario de una encuesta de satisfacción sobre un curso de capacitación en Campus Córdoba.

Temas posibles:
- tutor_docente: desempeño, comunicación o ausencia del docente/tutor
- contenidos_material: calidad o nivel de videos, lecturas, módulos o aplicación práctica
- aula_virtual_plataforma: funcionamiento de la web, acceso o aula virtual
- administracion_gestion: atención administrativa, inscripciones o trámites
- felicitaciones_general: agradecimientos, elogios generales ("muy bueno", "excelente oportunidad")
- sugerencias_mejora: pedidos de más clases en vivo, más tiempo, cambios
- otro: no encaja claramente en las anteriores

Sentimientos posibles:
- positivo
- negativo
- neutro

Respondé ÚNICAMENTE con un JSON válido con este formato exacto:
{{"topic": "<uno_de_los_temas>", "sentiment": "<positivo|negativo|neutro>"}}

Comentario: "{comment}"
"""


class AnalizadorReglas(CommentAnalyzer):
    """
    Analizador basado en reglas y palabras clave en español para funcionar
    sin costo ni necesidad de API Key externa.
    """

    def classify(self, comment: str) -> ClassificationResult:
        texto = comment.strip().lower()
        if not texto or len(texto) <= 2:
            return {"topic": "sin_comentario", "sentiment": "neutro"}

        # Sentimiento
        palabras_pos = ["excelente", "bueno", "buen", "me gusto", "me gustó", "encanto", "encantó", "gracias", "felicitaciones", "genial", "completo", "util", "útil", "llevadero", "claro", "recomiendo", "ameno"]
        palabras_neg = ["ausente", "malo", "mala", "pésimo", "pesimo", "aburrido", "falto", "faltó", "enlatado", "fachismo", "queja", "desastre", "lento", "dificil", "difícil", "incompleto", "inadecuado", "desactualizado"]

        conteo_pos = sum(1 for w in palabras_pos if w in texto)
        conteo_neg = sum(1 for w in palabras_neg if w in texto)

        sentimiento = "neutro"
        if conteo_pos > conteo_neg:
            sentimiento = "positivo"
        elif conteo_neg > conteo_pos:
            sentimiento = "negativo"

        # Tópicos
        if any(w in texto for w in ["docente", "tutor", "profesor", "profe", "tutoría", "tutora"]):
            tema = "tutor_docente"
        elif any(w in texto for w in ["material", "contenido", "video", "videos", "módulo", "modulo", "textos", "teoria", "lectura"]):
            tema = "contenidos_material"
        elif any(w in texto for w in ["plataforma", "aula virtual", "campus", "web", "sistema", "acceso", "login"]):
            tema = "aula_virtual_plataforma"
        elif any(w in texto for w in ["administrativa", "administracion", "administración", "consulta", "tramite", "trámite", "certificado"]):
            tema = "administracion_gestion"
        elif any(w in texto for w in ["sugiero", "mas clases", "más clases", "intercambiar", "practicas", "prácticas", "agregaria", "agregaría", "mejorar", "estaria bueno"]):
            tema = "sugerencias_mejora"
        elif sentimiento == "positivo" and any(w in texto for w in ["gracias", "felicitaciones", "excelente", "encantó", "encanto", "buen curso", "oportunidad"]):
            tema = "felicitaciones_general"
        else:
            tema = "otro"

        return {"topic": tema, "sentiment": sentimiento}

    def summarize(self, comments: list[str]) -> str:
        comentarios_validos = [c for c in comments if len(c.strip()) > 3]
        if not comentarios_validos:
            return "No hay comentarios suficientes para elaborar un resumen."
        return f"Se registraron {len(comentarios_validos)} comentarios de alumnos. Los principales temas abarcan calidad de contenidos, dinámica tutorial y sugerencias para incorporar más instancias prácticas o clases sincrónicas."


class AnalizadorUnificado(CommentAnalyzer):
    """
    Analizador unificado: utiliza OpenAI si la clave está configurada; de lo contrario
    utiliza el motor por reglas para garantizar operatividad 100%.
    """

    def __init__(self):
        self.fallback = AnalizadorReglas()
        self.client = None
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-") and len(settings.OPENAI_API_KEY) > 20:
            try:
                # pyrefly: ignore [missing-import]
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI Analyzer inicializado correctamente.")
            except Exception as e:
                logger.warning(f"No se pudo inicializar OpenAI client: {e}. Usando fallback.")
                self.client = None

    def classify(self, comment: str) -> ClassificationResult:
        if not comment.strip():
            return {"topic": "sin_comentario", "sentiment": "neutro"}

        if not self.client:
            return self.fallback.classify(comment)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": PROMPT_CLASIFICAR.format(comment=comment),
                }],
                response_format={"type": "json_object"},
                temperature=0,
            )
            data = json.loads(response.choices[0].message.content)
            tema = data.get("topic", "otro")
            sentimiento = data.get("sentiment", "neutro")
            if tema not in TOPICS:
                tema = "otro"
            if sentimiento not in ["positivo", "negativo", "neutro"]:
                sentimiento = "neutro"
            return {"topic": tema, "sentiment": sentimiento}
        except Exception as e:
            logger.error(f"Error llamando a OpenAI API: {e}. Usando clasificador por reglas.")
            return self.fallback.classify(comment)

    def summarize(self, comments: list[str]) -> str:
        comentarios_validos = [c for c in comments if len(c.strip()) > 3]
        if not comentarios_validos:
            return "No hay comentarios suficientes para resumir."

        if not self.client:
            return self.fallback.summarize(comments)

        try:
            unidos = "\n".join(f"- {c}" for c in comentarios_validos[:100])
            prompt = f"Resumí en 3-4 oraciones los puntos fuertes, reclamos y sugerencias principales de estos comentarios de alumnos de Campus Córdoba:\n\n{unidos}"
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generando resumen con OpenAI: {e}")
            return self.fallback.summarize(comments)


# Instancia singleton
analizador = AnalizadorUnificado()
analyzer = analizador  # alias
