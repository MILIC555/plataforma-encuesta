# pyrefly: ignore [missing-import]
from datetime import datetime
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Query
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.analytics.analitica import (
    obtener_kpis_tablero,
    obtener_desglose_preguntas,
    obtener_comparativa_cursos,
    obtener_tendencias_temporales,
    obtener_insights_ia,
    obtener_lista_comentarios,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


def _parsear_fecha(date_str: str | None):
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return None


@router.get("/kpis")
def kpis(
    course_id: int | None = Query(None, description="Filtrar por ID de curso"),
    platform: str | None = Query(None, description="Filtrar por plataforma (campus_cordoba | campus_empleados)"),
    start_date: str | None = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Devuelve los indicadores clave de rendimiento (KPIs)."""
    return obtener_kpis_tablero(
        db,
        id_curso=course_id,
        fecha_inicio=_parsear_fecha(start_date),
        fecha_fin=_parsear_fecha(end_date),
        plataforma=platform,
    )


@router.get("/questions")
def preguntas_desglose(
    course_id: int | None = Query(None, description="Filtrar por ID de curso"),
    platform: str | None = Query(None, description="Filtrar por plataforma (campus_cordoba | campus_empleados)"),
    start_date: str | None = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Devuelve promedios y distribución para las preguntas (9 de Córdoba o 5 de Empleados)."""
    return obtener_desglose_preguntas(
        db,
        id_curso=course_id,
        fecha_inicio=_parsear_fecha(start_date),
        fecha_fin=_parsear_fecha(end_date),
        plataforma=platform,
    )


@router.get("/courses")
def comparativa_cursos(
    platform: str | None = Query(None, description="Filtrar por plataforma (campus_cordoba | campus_empleados)"),
    start_date: str | None = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Devuelve la tabla comparativa de desempeño entre cursos."""
    return obtener_comparativa_cursos(
        db,
        fecha_inicio=_parsear_fecha(start_date),
        fecha_fin=_parsear_fecha(end_date),
        plataforma=platform,
    )


@router.get("/trends")
def tendencias_temporales(
    course_id: int | None = Query(None, description="Filtrar por ID de curso"),
    platform: str | None = Query(None, description="Filtrar por plataforma (campus_cordoba | campus_empleados)"),
    db: Session = Depends(get_db),
):
    """Devuelve la evolución temporal de encuestas y calificaciones promedio."""
    return obtener_tendencias_temporales(db, id_curso=course_id, plataforma=platform)


@router.get("/ai-insights")
def insights_ia(
    course_id: int | None = Query(None, description="Filtrar por ID de curso"),
    platform: str | None = Query(None, description="Filtrar por plataforma (campus_cordoba | campus_empleados)"),
    start_date: str | None = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Devuelve la distribución de sentimientos, tópicos y resumen de IA."""
    return obtener_insights_ia(
        db,
        id_curso=course_id,
        fecha_inicio=_parsear_fecha(start_date),
        fecha_fin=_parsear_fecha(end_date),
        plataforma=platform,
    )


@router.get("/comments")
def listar_comentarios(
    course_id: int | None = Query(None, description="Filtrar por ID de curso"),
    platform: str | None = Query(None, description="Filtrar por plataforma (campus_cordoba | campus_empleados)"),
    topic: str | None = Query(None, description="Filtrar por tópico"),
    sentiment: str | None = Query(None, description="Filtrar por sentimiento"),
    search: str | None = Query(None, description="Búsqueda por texto"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Devuelve los comentarios abiertos (pregunta 9 de Córdoba o 5 de Empleados) con filtros aplicables."""
    return obtener_lista_comentarios(
        db,
        id_curso=course_id,
        tema=topic,
        sentimiento=sentiment,
        busqueda=search,
        plataforma=platform,
        pagina=page,
        tamanio_pagina=page_size,
    )
