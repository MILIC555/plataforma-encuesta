from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.ai.servicio import procesar_comentarios_pendientes

router = APIRouter(prefix="/ai", tags=["Módulo de Inteligencia Artificial"])


@router.post("/analyze-comments")
def analizar_comentarios(
    limit: int = 200,
    db: Session = Depends(get_db),
):
    """
    Ejecuta el clasificador de Inteligencia Artificial sobre comentarios
    que aún no cuenten con clasificación de tema o sentimiento.
    """
    return procesar_comentarios_pendientes(db, limite=limit)
