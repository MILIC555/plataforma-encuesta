from datetime import datetime
import logging
from sqlalchemy.orm import Session
from app.db.models.respuesta import Respuesta
from app.db.models.pregunta import Pregunta
from app.ai.analizador import analizador

logger = logging.getLogger(__name__)


def procesar_comentarios_pendientes(db: Session, limite: int = 500) -> dict:
    """
    Busca comentarios de la pregunta 9 que aún no hayan sido clasificados
    y los procesa en lote con el analizador de Hugging Face.
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

    textos = [resp.valor_texto for resp in pendientes]
    
    # Inferencia en lote optimizada
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
