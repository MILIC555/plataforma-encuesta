from datetime import datetime
import logging
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from app.db.models.respuesta import Respuesta
# pyrefly: ignore [missing-import]
from app.db.models.pregunta import Pregunta
from app.ai.analizador import analizador

logger = logging.getLogger(__name__)


def procesar_comentarios_pendientes(db: Session, limite: int = 500) -> dict:
    """
    Busca comentarios de preguntas abiertas (Q9 Córdoba o Q5 Empleados)
    que aún no hayan sido clasificados y los procesa con Hugging Face.
    """
    text_p_ids = [p.id for p in db.query(Pregunta.id).filter(Pregunta.tipo == "texto").all()]
    if not text_p_ids:
        return {"processed": 0, "message": "Preguntas de texto no encontradas en catálogo"}

    pendientes = (
        db.query(Respuesta)
        .filter(
            Respuesta.id_pregunta.in_(text_p_ids),
            Respuesta.valor_texto.isnot(None),
            Respuesta.ai_tema.is_(None),
        )
        .limit(limite)
        .all()
    )

    if not pendientes:
        return {"processed": 0, "message": "No hay comentarios pendientes de clasificación"}

    textos = [resp.valor_texto for resp in pendientes]
    
    # Inferencia en lote con Hugging Face
    if hasattr(analizador, "classify_batch"):
        clasificaciones = analizador.classify_batch(textos)
    else:
        clasificaciones = [analizador.classify(t) for t in textos]

    ahora = datetime.utcnow()
    for resp, resultado in zip(pendientes, clasificaciones):
        resp.ai_tema = resultado["topic"]
        resp.ai_sentimiento = resultado["sentiment"]
        resp.ai_procesado_en = ahora

    db.commit()
    logger.info(f"Se procesaron {len(pendientes)} comentarios con Hugging Face.")
    return {
        "processed": len(pendientes),
        "message": f"Se procesaron {len(pendientes)} comentarios exitosamente con Hugging Face.",
    }


# Alias de compatibilidad
process_pending_comments = procesar_comentarios_pendientes
