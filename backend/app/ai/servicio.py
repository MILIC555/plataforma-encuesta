from datetime import datetime
import logging
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from app.db.models.respuesta import Respuesta
from app.db.models.pregunta import Pregunta
from app.ai.analizador import analizador

logger = logging.getLogger(__name__)


def procesar_comentarios_pendientes(db: Session, limite: int = 200) -> dict:
    """
    Busca comentarios de la pregunta 9 que aún no hayan sido clasificados
    y los procesa con el analizador de IA.
    """
    p9 = db.query(Pregunta).filter(Pregunta.nro_pregunta == 9).first()
    if not p9:
        return {"processed": 0, "message": "Pregunta 9 no encontrada en catálogo"}

    pendientes = (
        db.query(Respuesta)
        .filter(
            Respuesta.id_pregunta == p9.id,
            Respuesta.valor_texto.isnot(None),
            Respuesta.ai_tema.is_(None),
        )
        .limit(limite)
        .all()
    )

    if not pendientes:
        return {"processed": 0, "message": "No hay comentarios pendientes de clasificación"}

    procesados_count = 0
    for resp in pendientes:
        comment_text = resp.valor_texto.strip() if resp.valor_texto else ""
        if not comment_text:
            resp.ai_tema = "sin_comentario"
            resp.ai_sentimiento = "neutro"
        else:
            result = analizador.classify(comment_text)
            resp.ai_tema = result["topic"]
            resp.ai_sentimiento = result["sentiment"]

        resp.ai_procesado_en = datetime.utcnow()
        procesados_count += 1

    db.commit()
    logger.info(f"Se procesaron {procesados_count} comentarios pendientes con IA.")
    return {"processed": procesados_count, "message": f"Se procesaron {procesados_count} comentarios exitosamente."}


# Alias de compatibilidad
process_pending_comments = procesar_comentarios_pendientes
