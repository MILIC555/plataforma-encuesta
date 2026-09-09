import json
import logging
import urllib.request
import urllib.error
from typing import List
from app.ai.base import CommentAnalyzer, ClassificationResult, TOPICS
from app.config import settings

logger = logging.getLogger(__name__)

# Etiquetas candidatas optimizadas para zero-shot en español
ETIQUETAS_CANDIDATAS_MAPA = {
    "tutor, profesor o docente": "tutor_docente",
    "material didáctico, videos o contenidos": "contenidos_material",
    "plataforma web, campus o aula virtual": "aula_virtual_plataforma",
    "atención administrativa, trámites o certificados": "administracion_gestion",
    "felicitaciones, elogios o agradecimientos": "felicitaciones_general",
    "sugerencias, propuestas o pedidos de cambio": "sugerencias_mejora",
}

ETIQUETAS_CANDIDATAS_LISTA = list(ETIQUETAS_CANDIDATAS_MAPA.keys())

# Patrones léxicos de alta sensibilidad para detección de quejas y reclamos (Negativo)
PATRONES_NEGATIVOS = [
    "no me gustó", "no me gusto", "no sirvió", "no sirvio", "pérdida de tiempo", "perdida de tiempo",
    "deja mucho que desear", "decepción", "decepcion", "desilusión", "desilusion", "muy flojo", "muy pobre",
    "muy básico", "muy basico", "desorganizado", "desactualizado", "no se entiende", "poco claro",
    "muy confuso", "no aprendí", "no aprendi", "pésimo", "pesimo", "malo", "mala", "horrible",
    "desastre", "tutor ausente", "nunca respondió", "nunca respondio", "se caía", "se caia",
    "no funcionaba", "no funciona", "errores", "muchos errores", "tardaron", "demoraron",
    "falta de respeto", "una lástima", "una lastima", "insatisfecho", "insatisfecha", "faltó explicación",
    "falto explicacion", "faltó práctica", "falto practica", "sin soporte", "incompleto", "inadecuado",
    "desprolijo", "no recomiendo", "aburrido", "enlatado", "lento", "difícil y sin ayuda", "dificil y sin ayuda",
    "nunca me llegó", "nunca me llego", "no contestan", "no responden", "pésima atención", "pesima atencion",
    "no actualizan", "examen muy largo", "muy largo el examen", "confusa"
]

PATRONES_POSITIVOS = [
    "excelente", "muy bueno", "muy buena", "buenísimo", "buenisimo", "me gustó mucho", "me gusto mucho",
    "me gustó", "me gusto", "me encantó", "me encanto", "muchas gracias", "felicitaciones", "genial", "completo",
    "muy útil", "muy util", "llevadero", "muy claro", "super claro", "recomiendo", "ameno", "satisfecho",
    "satisfecha", "impecable", "gran curso", "gran tutor", "gran docente", "excelente oportunidad",
    "muy linda", "muy lindo", "formidable", "hermoso", "hermosa", "de diez", "de diez!", "excelentes",
    "buenas explicaciones", "muy práctico", "muy practico", "muy conforme", "gracias", "super util",
    "util y claro", "agradezco", "aprendi muchisimo", "aprendí muchísimo"
]


class AnalizadorReglas(CommentAnalyzer):
    """
    Analizador basado en reglas y heurísticas en español.
    Garantiza disponibilidad instantánea como motor o como respaldo (fallback).
    """

    def classify(self, comment: str) -> ClassificationResult:
        texto = comment.strip().lower()
        if not texto or len(texto) <= 1:
            return {"topic": "sin_comentario", "sentiment": "neutro"}

        conteo_pos = sum(1 for w in PATRONES_POSITIVOS if w in texto)
        conteo_neg = sum(1 for w in PATRONES_NEGATIVOS if w in texto)

        sentimiento = "neutro"
        if conteo_neg > 0 and conteo_neg >= conteo_pos:
            sentimiento = "negativo"
        elif conteo_pos > conteo_neg:
            sentimiento = "positivo"

        # Tópicos
        if any(w in texto for w in ["sugiero", "sugerencia", "estaría bueno", "estaria bueno", "sería bueno", "seria bueno", "agregaría", "agregaria", "más clases", "mas clases", "más ejemplos", "mas ejemplos", "más casos", "podrían", "podrian", "deberían", "deberian", "se podría", "se podria", "propuesta", "ampliar", "profundizar"]):
            tema = "sugerencias_mejora"
        elif any(w in texto for w in ["docente", "tutor", "profesor", "profe", "tutoría", "tutora", "tutores"]):
            tema = "tutor_docente"
        elif any(w in texto for w in ["plataforma", "aula virtual", "campus", "web", "sistema", "acceso", "login", "pagina", "página", "foro"]):
            tema = "aula_virtual_plataforma"
        elif any(w in texto for w in ["administrativa", "administracion", "administración", "consulta", "tramite", "trámite", "certificado", "secretaría", "subdirección"]):
            tema = "administracion_gestion"
        elif any(w in texto for w in ["material", "contenido", "video", "videos", "módulo", "modulo", "textos", "teoria", "lectura", "pdf", "audio", "audios", "diapositivas"]):
            tema = "contenidos_material"
        elif sentimiento == "positivo" or any(w in texto for w in ["gracias", "felicitaciones", "excelente", "encantó", "encanto", "buen curso", "oportunidad", "lindo curso", "hermoso", "genial"]):
            tema = "felicitaciones_general"
        else:
            tema = "otro"

        return {"topic": tema, "sentiment": sentimiento}

    def summarize(self, comments: list[str]) -> str:
        comentarios_validos = [c for c in comments if len(c.strip()) > 3]
        if not comentarios_validos:
            return "No hay comentarios suficientes para elaborar un resumen."
        return f"Se registraron {len(comentarios_validos)} comentarios de alumnos. Los principales temas abarcan calidad de contenidos, dinámica tutorial y sugerencias para incorporar más instancias prácticas o clases sincrónicas."


class AnalizadorHuggingFace(CommentAnalyzer):
    """
    Analizador de IA basado en Hugging Face Transformers con calibración avanzada de respuestas críticas/negativas:
    - Sentimiento: Clasificador RoBERTa/BETO en español (positivo, neutro, negativo).
    - Temáticas: Clasificador Zero-Shot en español (BETO XNLI) con resolución semántica.
    """

    def __init__(self):
        self.fallback = AnalizadorReglas()
        self._sentiment_pipe = None
        self._topic_pipe = None
        self._init_attempted = False
        self.hf_api_key = settings.HUGGINGFACE_API_KEY.strip() if settings.HUGGINGFACE_API_KEY else ""

    def _init_local_pipelines(self):
        """Inicializa los pipelines locales de Transformers bajo demanda."""
        if self._init_attempted:
            return
        self._init_attempted = True

        try:
            from transformers import pipeline
            logger.info("Cargando pipeline de Sentimiento en español de Hugging Face...")
            self._sentiment_pipe = pipeline(
                "sentiment-analysis",
                model=settings.HF_MODEL_SENTIMENT,
                tokenizer=settings.HF_MODEL_SENTIMENT,
                truncation=True,
                max_length=256,
            )
            logger.info("Pipeline de Sentimiento cargado exitosamente.")
        except Exception as e:
            logger.warning(f"No se pudo cargar pipeline local de Sentimiento HF ({e}). Usando fallback por reglas.")
            self._sentiment_pipe = None

        try:
            from transformers import pipeline
            logger.info("Cargando pipeline de Clasificación Temática Zero-Shot de Hugging Face...")
            self._topic_pipe = pipeline(
                "zero-shot-classification",
                model=settings.HF_MODEL_TOPIC,
                tokenizer=settings.HF_MODEL_TOPIC,
                truncation=True,
                max_length=256,
            )
            logger.info("Pipeline Zero-Shot cargado exitosamente.")
        except Exception as e:
            logger.warning(f"No se pudo cargar pipeline local Zero-Shot HF ({e}). Usando fallback por reglas.")
            self._topic_pipe = None

    def _mapear_sentimiento(self, label: str) -> str:
        """Normaliza la etiqueta del modelo de Hugging Face a ('positivo', 'neutro', 'negativo')."""
        l = str(label).upper().strip()
        if any(term in l for term in ["POS", "POSITIVE", "5 STARS", "4 STARS", "LABEL_2"]):
            return "positivo"
        elif any(term in l for term in ["NEG", "NEGATIVE", "1 STAR", "2 STARS", "LABEL_0"]):
            return "negativo"
        elif any(term in l for term in ["NEU", "NEUTRAL", "3 STARS", "LABEL_1"]):
            return "neutro"
        return "neutro"

    def _calibrar_sentimiento(self, texto: str, sentimiento_modelo: str) -> str:
        """
        Calibra el sentimiento combinando el modelo neuronal con detección sensible de quejas/críticas y elogios.
        """
        t_low = texto.lower()
        conteo_neg = sum(1 for p in PATRONES_NEGATIVOS if p in t_low)
        conteo_pos = sum(1 for p in PATRONES_POSITIVOS if p in t_low)

        if conteo_neg > 0 and conteo_neg >= conteo_pos:
            return "negativo"
        if sentimiento_modelo == "negativo":
            return "negativo"
        if sentimiento_modelo == "positivo" and conteo_neg == 0:
            return "positivo"
        if conteo_pos > 0 and conteo_neg == 0:
            return "positivo"

        return sentimiento_modelo or "neutro"

    def _detectar_topico_con_prioridad(self, texto: str, prediccion_zero_shot: str | None = None) -> str:
        """Combina reglas de alta certeza léxica con inferencia semántica Zero-Shot."""
        t_low = texto.lower()
        if any(w in t_low for w in ["sugiero", "sugerencia", "estaría bueno", "estaria bueno", "sería bueno", "seria bueno", "agregaría", "agregaria", "más clases", "mas clases", "más ejemplos", "mas ejemplos", "más casos", "podrían", "podrian", "deberían", "deberian", "se podría", "se podria", "propuesta", "ampliar", "profundizar"]):
            return "sugerencias_mejora"
        if any(w in t_low for w in ["docente", "tutor", "profesor", "profe", "tutora", "tutoría", "tutores"]):
            return "tutor_docente"
        if any(w in t_low for w in ["plataforma", "aula virtual", "campus", "sitio web", "caída de la página", "no me dejaba ingresar", "foro"]):
            return "aula_virtual_plataforma"
        if any(w in t_low for w in ["certificado", "tramite", "trámite", "administracion", "administración", "secretaría", "subdirección"]):
            return "administracion_gestion"
        if any(w in t_low for w in ["material", "videos", "video", "lecturas", "pdf", "módulos", "modulos", "contenido", "contenidos", "audio", "audios", "diapositivas"]):
            return "contenidos_material"
        if any(w in t_low for w in ["excelente", "gracias", "muchas gracias", "felicitaciones", "genial", "muy bueno", "muy buena", "hermoso", "lindo curso", "buen curso"]):
            return "felicitaciones_general"
        
        if prediccion_zero_shot:
            return prediccion_zero_shot

        return "otro"

    def _clasificar_con_api_hf(self, text: str) -> ClassificationResult | None:
        """Ejecuta clasificación a través de la Hugging Face Inference API si hay API Key configurada."""
        if not self.hf_api_key or not self.hf_api_key.startswith("hf_"):
            return None

        headers = {
            "Authorization": f"Bearer {self.hf_api_key}",
            "Content-Type": "application/json",
        }
        try:
            # 1. Sentimiento
            url_sent = f"https://api-inference.huggingface.co/models/{settings.HF_MODEL_SENTIMENT}"
            req_s = urllib.request.Request(url_sent, data=json.dumps({"inputs": text}).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req_s, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                sentimiento = "neutro"
                if isinstance(data, list) and len(data) > 0:
                    primer_elem = data[0]
                    if isinstance(primer_elem, list) and len(primer_elem) > 0:
                        top_label = max(primer_elem, key=lambda x: x.get("score", 0)).get("label", "")
                        sentimiento = self._mapear_sentimiento(top_label)

            sentimiento_final = self._calibrar_sentimiento(text, sentimiento)

            # 2. Temática Zero-Shot
            url_topic = f"https://api-inference.huggingface.co/models/{settings.HF_MODEL_TOPIC}"
            payload_topic = {
                "inputs": text,
                "parameters": {"candidate_labels": ETIQUETAS_CANDIDATAS_LISTA},
            }
            req_t = urllib.request.Request(url_topic, data=json.dumps(payload_topic).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req_t, timeout=10) as resp:
                data_t = json.loads(resp.read().decode("utf-8"))
                labels = data_t.get("labels", [])
                scores = data_t.get("scores", [])
                tema_zs = None
                if labels and scores and scores[0] >= 0.25:
                    tema_zs = ETIQUETAS_CANDIDATAS_MAPA.get(labels[0], "otro")
                
                tema = self._detectar_topico_con_prioridad(text, tema_zs)

            return {"topic": tema, "sentiment": sentimiento_final}
        except Exception as e:
            logger.warning(f"Error llamando a Hugging Face Inference API: {e}")
            return None

    def classify(self, comment: str) -> ClassificationResult:
        """Clasifica un comentario individual."""
        texto = comment.strip()
        if not texto or len(texto) <= 1:
            return {"topic": "sin_comentario", "sentiment": "neutro"}

        res_api = self._clasificar_con_api_hf(texto)
        if res_api:
            return res_api

        self._init_local_pipelines()

        sentimiento_modelo = None
        tema_zs = None

        if self._sentiment_pipe:
            try:
                res_s = self._sentiment_pipe(texto[:256])[0]
                sentimiento_modelo = self._mapear_sentimiento(res_s.get("label", ""))
            except Exception as e:
                logger.debug(f"Fallo en sentiment_pipe: {e}")

        if self._topic_pipe:
            try:
                res_t = self._topic_pipe(
                    texto[:256],
                    candidate_labels=ETIQUETAS_CANDIDATAS_LISTA,
                    hypothesis_template="Este texto es sobre {}.",
                )
                if res_t.get("scores") and res_t["scores"][0] >= 0.25:
                    top_label = res_t["labels"][0]
                    tema_zs = ETIQUETAS_CANDIDATAS_MAPA.get(top_label, "otro")
            except Exception as e:
                logger.debug(f"Fallo en topic_pipe: {e}")

        sentimiento = self._calibrar_sentimiento(texto, sentimiento_modelo)
        tema = self._detectar_topico_con_prioridad(texto, tema_zs)

        return {"topic": tema, "sentiment": sentimiento}

    def classify_batch(self, comments: List[str]) -> List[ClassificationResult]:
        """Clasifica un lote de comentarios de manera optimizada."""
        if not comments:
            return []

        resultados = []
        indices_para_modelo = []
        textos_para_modelo = []

        for idx, c in enumerate(comments):
            txt = (c or "").strip()
            if not txt or len(txt) <= 1:
                resultados.append({"topic": "sin_comentario", "sentiment": "neutro"})
            else:
                resultados.append(None)
                indices_para_modelo.append(idx)
                textos_para_modelo.append(txt)

        if not textos_para_modelo:
            return resultados

        self._init_local_pipelines()

        # Inferencia de sentimiento en lote
        sentimientos_batch = []
        if self._sentiment_pipe:
            try:
                preds_s = self._sentiment_pipe([t[:256] for t in textos_para_modelo], batch_size=32)
                sentimientos_batch = [
                    self._calibrar_sentimiento(txt, self._mapear_sentimiento(p["label"]))
                    for txt, p in zip(textos_para_modelo, preds_s)
                ]
            except Exception as e:
                logger.warning(f"Error en batch de sentimiento HF: {e}")
                sentimientos_batch = [self.fallback.classify(t)["sentiment"] for t in textos_para_modelo]
        else:
            sentimientos_batch = [self.fallback.classify(t)["sentiment"] for t in textos_para_modelo]

        # Inferencia de tópicos en lote
        topicos_batch = []
        if self._topic_pipe:
            try:
                preds_t = self._topic_pipe(
                    [t[:256] for t in textos_para_modelo],
                    candidate_labels=ETIQUETAS_CANDIDATAS_LISTA,
                    hypothesis_template="Este texto es sobre {}.",
                    batch_size=16,
                )
                for txt_orig, pt in zip(textos_para_modelo, preds_t):
                    tema_zs = None
                    if pt.get("scores") and pt["scores"][0] >= 0.25:
                        tema_zs = ETIQUETAS_CANDIDATAS_MAPA.get(pt["labels"][0], "otro")
                    tema_final = self._detectar_topico_con_prioridad(txt_orig, tema_zs)
                    topicos_batch.append(tema_final)
            except Exception as e:
                logger.warning(f"Error en batch de tópicos HF: {e}")
                topicos_batch = [self._detectar_topico_con_prioridad(t) for t in textos_para_modelo]
        else:
            topicos_batch = [self._detectar_topico_con_prioridad(t) for t in textos_para_modelo]

        # Ensamblar resultados
        for sub_idx, orig_idx in enumerate(indices_para_modelo):
            resultados[orig_idx] = {
                "topic": topicos_batch[sub_idx],
                "sentiment": sentimientos_batch[sub_idx],
            }

        return resultados

    def summarize(self, comments: list[str]) -> str:
        """Genera un resumen analítico basado en las observaciones."""
        validos = [c.strip() for c in comments if c and len(c.strip()) > 3]
        if not validos:
            return "No hay comentarios suficientes para elaborar un resumen."

        lote_clasif = self.classify_batch(validos[:50])
        positivos = sum(1 for r in lote_clasif if r["sentiment"] == "positivo")
        negativos = sum(1 for r in lote_clasif if r["sentiment"] == "negativo")
        
        from collections import Counter
        top_temas = Counter(r["topic"] for r in lote_clasif if r["topic"] not in ["sin_comentario", "otro"]).most_common(2)

        temas_desc = []
        from app.ai.base import TOPIC_LABELS
        for t_k, count in top_temas:
            temas_desc.append(f"{TOPIC_LABELS.get(t_k, t_k)} ({count} menciones)")

        resumen = f"Análisis de {len(validos)} opiniones con Hugging Face: {positivos} valoraciones positivas y {negativos} oportunidades de mejora."
        if temas_desc:
            resumen += f" Las áreas con mayor interacción de los participantes fueron: {', '.join(temas_desc)}."
        return resumen


# Instancia singleton
analizador = AnalizadorHuggingFace()
analyzer = analizador  # alias
