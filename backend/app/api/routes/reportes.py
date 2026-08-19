from datetime import datetime
from fastapi import APIRouter, Depends, Query, Response as FastAPIResponse
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.db.models.curso import Curso
from app.analytics.analitica import (
    obtener_kpis_tablero,
    obtener_desglose_preguntas,
    obtener_insights_ia,
    obtener_lista_comentarios,
)
from app.reports.generador_pdf import generar_pdf_encuestas
from app.reports.generador_excel import generar_excel_encuestas

router = APIRouter(prefix="/reports", tags=["Exportación de Reportes"])


def _parsear_fecha(date_str: str | None):
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return None


@router.get("/pdf")
def exportar_pdf(
    course_id: int | None = Query(None, description="ID del curso"),
    start_date: str | None = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Genera y descarga el informe ejecutivo institucional en formato PDF (WeasyPrint)."""
    parsed_start = _parsear_fecha(start_date)
    parsed_end = _parsear_fecha(end_date)

    course_obj = db.query(Curso).filter(Curso.id == course_id).first() if course_id else None
    course_name = course_obj.nombre if course_obj else "Reporte General (Todos los Cursos)"

    kpis = obtener_kpis_tablero(db, id_curso=course_id, fecha_inicio=parsed_start, fecha_fin=parsed_end)
    questions = obtener_desglose_preguntas(db, id_curso=course_id, fecha_inicio=parsed_start, fecha_fin=parsed_end)
    ai_insights = obtener_insights_ia(db, id_curso=course_id, fecha_inicio=parsed_start, fecha_fin=parsed_end)
    comments_res = obtener_lista_comentarios(db, id_curso=course_id, pagina=1, tamanio_pagina=20)

    pdf_bytes = generar_pdf_encuestas(
        kpis=kpis,
        preguntas=questions,
        insights_ia=ai_insights,
        comentarios=comments_res.get("items", []),
        nombre_curso=course_name,
        fecha_inicio=start_date,
        fecha_fin=end_date,
    )

    filename = f"reporte_encuestas_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return FastAPIResponse(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/excel")
def exportar_excel(
    course_id: int | None = Query(None, description="ID del curso"),
    start_date: str | None = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Genera y descarga la base de datos y matriz de respuestas en formato Excel (.xlsx)."""
    parsed_start = _parsear_fecha(start_date)
    parsed_end = _parsear_fecha(end_date)

    excel_bytes = generar_excel_encuestas(
        db=db,
        id_curso=course_id,
        fecha_inicio=parsed_start,
        fecha_fin=parsed_end,
    )

    filename = f"datos_encuestas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return FastAPIResponse(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
