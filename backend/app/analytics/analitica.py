from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models.encuesta import Encuesta
from app.db.models.curso import Curso
from app.db.models.pregunta import Pregunta
from app.db.models.respuesta import Respuesta
from app.ai.base import TOPIC_LABELS
from app.ai.analizador import analizador


def _aplicar_filtros(query, id_curso=None, fecha_inicio=None, fecha_fin=None):
    if id_curso:
        query = query.filter(Encuesta.id_curso == id_curso)
    if fecha_inicio:
        query = query.filter(Encuesta.fecha_envio >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Encuesta.fecha_envio <= fecha_fin)
    return query


def obtener_kpis_tablero(db: Session, id_curso: int = None, fecha_inicio = None, fecha_fin = None) -> dict:
    """Calcula los KPIs principales: total encuestas, promedio general, NPS y satisfacción."""
    query_base = _aplicar_filtros(db.query(Encuesta), id_curso, fecha_inicio, fecha_fin)
    total_encuestas = query_base.count()

    if total_encuestas == 0:
        return {
            "total_surveys": 0,
            "overall_average": 0.0,
            "nps": 0.0,
            "satisfaction_pct": 0.0,
            "promoters_pct": 0.0,
            "detractors_pct": 0.0,
            "total_courses": db.query(Curso).count(),
        }

    # Promedio general de todas las preguntas numéricas (Q1 a Q8)
    subquery_ids = _aplicar_filtros(db.query(Encuesta.id), id_curso, fecha_inicio, fecha_fin).subquery()
    
    prom_general_res = (
        db.query(func.avg(Respuesta.valor_numerico))
        .filter(
            Respuesta.id_encuesta.in_(subquery_ids),
            Respuesta.valor_numerico.isnot(None),
        )
        .scalar()
    )
    overall_average = round(float(prom_general_res), 2) if prom_general_res is not None else 0.0

    # Cálculo de NPS a partir de Pregunta 8 (Recomendación)
    p8 = db.query(Pregunta).filter(Pregunta.nro_pregunta == 8).first()
    nps_score = 0.0
    promoters_pct = 0.0
    detractors_pct = 0.0

    if p8:
        p8_respuestas = (
            db.query(Respuesta.valor_numerico)
            .filter(
                Respuesta.id_encuesta.in_(subquery_ids),
                Respuesta.id_pregunta == p8.id,
                Respuesta.valor_numerico.isnot(None),
            )
            .all()
        )
        p8_values = [r[0] for r in p8_respuestas]
        total_p8 = len(p8_values)
        if total_p8 > 0:
            promotores = sum(1 for v in p8_values if v >= 9)
            pasivos = sum(1 for v in p8_values if 7 <= v <= 8)
            detractores = sum(1 for v in p8_values if v <= 6)
            nps_score = round(((promotores - detractores) / total_p8) * 100, 1)
            promoters_pct = round((promotores / total_p8) * 100, 1)
            detractors_pct = round((detractores / total_p8) * 100, 1)

    # % Satisfacción general a partir de Pregunta 6 (Satisfacción General >= 8)
    p6 = db.query(Pregunta).filter(Pregunta.nro_pregunta == 6).first()
    satisfaction_pct = 0.0
    if p6:
        p6_respuestas = (
            db.query(Respuesta.valor_numerico)
            .filter(
                Respuesta.id_encuesta.in_(subquery_ids),
                Respuesta.id_pregunta == p6.id,
                Respuesta.valor_numerico.isnot(None),
            )
            .all()
        )
        p6_values = [r[0] for r in p6_respuestas]
        if p6_values:
            satisfechos = sum(1 for v in p6_values if v >= 8)
            satisfaction_pct = round((satisfechos / len(p6_values)) * 100, 1)

    total_courses = db.query(Curso).count()

    return {
        "total_surveys": total_encuestas,
        "overall_average": overall_average,
        "nps": nps_score,
        "satisfaction_pct": satisfaction_pct,
        "promoters_pct": promoters_pct,
        "detractors_pct": detractors_pct,
        "total_courses": total_courses,
    }


def obtener_desglose_preguntas(db: Session, id_curso: int = None, fecha_inicio = None, fecha_fin = None) -> list[dict]:
    """Obtiene promedios y distribución para cada una de las 8 preguntas cuantitativas."""
    subquery_ids = _aplicar_filtros(db.query(Encuesta.id), id_curso, fecha_inicio, fecha_fin).subquery()
    preguntas = db.query(Pregunta).filter(Pregunta.tipo == "numerica").order_by(Pregunta.nro_pregunta).all()

    resultados = []
    for p in preguntas:
        filas = (
            db.query(Respuesta.valor_numerico)
            .filter(
                Respuesta.id_encuesta.in_(subquery_ids),
                Respuesta.id_pregunta == p.id,
                Respuesta.valor_numerico.isnot(None),
            )
            .all()
        )
        valores = [r[0] for r in filas]
        total = len(valores)
        prom = round(sum(valores) / total, 2) if total > 0 else 0.0

        dist = {str(i): 0 for i in range(1, 11)}
        for v in valores:
            if 1 <= v <= 10:
                dist[str(v)] += 1

        resultados.append({
            "question_number": p.nro_pregunta,
            "short_label": p.etiqueta_corta,
            "description": p.descripcion,
            "average": prom,
            "count": total,
            "distribution": dist,
        })

    return resultados


def obtener_comparativa_cursos(db: Session, fecha_inicio = None, fecha_fin = None) -> list[dict]:
    """Compara métricas entre todos los cursos."""
    cursos = db.query(Curso).all()
    p6 = db.query(Pregunta).filter(Pregunta.nro_pregunta == 6).first()
    p8 = db.query(Pregunta).filter(Pregunta.nro_pregunta == 8).first()

    lista_resumen = []
    for c in cursos:
        query_encuestas = _aplicar_filtros(db.query(Encuesta), id_curso=c.id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        total_encuestas = query_encuestas.count()
        if total_encuestas == 0:
            continue

        ids_encuestas = [s.id for s in query_encuestas.all()]

        # Promedio general del curso
        avg_res = (
            db.query(func.avg(Respuesta.valor_numerico))
            .filter(
                Respuesta.id_encuesta.in_(ids_encuestas),
                Respuesta.valor_numerico.isnot(None),
            )
            .scalar()
        )
        overall_avg = round(float(avg_res), 2) if avg_res else 0.0

        # NPS del curso
        nps = 0.0
        if p8:
            p8_vals = [
                r[0] for r in db.query(Respuesta.valor_numerico)
                .filter(Respuesta.id_encuesta.in_(ids_encuestas), Respuesta.id_pregunta == p8.id, Respuesta.valor_numerico.isnot(None))
                .all()
            ]
            if p8_vals:
                promotores = sum(1 for v in p8_vals if v >= 9)
                detractores = sum(1 for v in p8_vals if v <= 6)
                nps = round(((promotores - detractores) / len(p8_vals)) * 100, 1)

        # Satisfacción del curso
        sat_pct = 0.0
        if p6:
            p6_vals = [
                r[0] for r in db.query(Respuesta.valor_numerico)
                .filter(Respuesta.id_encuesta.in_(ids_encuestas), Respuesta.id_pregunta == p6.id, Respuesta.valor_numerico.isnot(None))
                .all()
            ]
            if p6_vals:
                sat_pct = round((sum(1 for v in p6_vals if v >= 8) / len(p6_vals)) * 100, 1)

        lista_resumen.append({
            "id": c.id,
            "name": c.nombre,
            "code": c.codigo,
            "institution": c.institucion,
            "department": c.departamento,
            "total_surveys": total_encuestas,
            "overall_average": overall_avg,
            "nps": nps,
            "satisfaction_pct": sat_pct,
        })

    lista_resumen.sort(key=lambda x: x["overall_average"], reverse=True)
    return lista_resumen


def obtener_tendencias_temporales(db: Session, id_curso: int = None) -> list[dict]:
    """Genera serie temporal agrupada por año y mes."""
    query_encuestas = _aplicar_filtros(db.query(Encuesta), id_curso=id_curso)
    encuestas = query_encuestas.order_by(Encuesta.periodo_anio, Encuesta.periodo_mes).all()

    agrupados = {}
    for s in encuestas:
        period_key = f"{s.periodo_anio}-{s.periodo_mes:02d}"
        if period_key not in agrupados:
            agrupados[period_key] = {"surveys": [], "period": period_key}
        agrupados[period_key]["surveys"].append(s.id)

    tendencias = []
    for period_key in sorted(agrupados.keys()):
        s_ids = agrupados[period_key]["surveys"]
        avg_score = (
            db.query(func.avg(Respuesta.valor_numerico))
            .filter(
                Respuesta.id_encuesta.in_(s_ids),
                Respuesta.valor_numerico.isnot(None),
            )
            .scalar()
        )
        tendencias.append({
            "period": period_key,
            "total_surveys": len(s_ids),
            "average_score": round(float(avg_score), 2) if avg_score else 0.0,
        })

    return tendencias


def obtener_insights_ia(db: Session, id_curso: int = None, fecha_inicio = None, fecha_fin = None) -> dict:
    """Métricas de análisis de IA sobre comentarios (temas y sentimientos)."""
    subquery_ids = _aplicar_filtros(db.query(Encuesta.id), id_curso, fecha_inicio, fecha_fin).subquery()
    p9 = db.query(Pregunta).filter(Pregunta.nro_pregunta == 9).first()

    if not p9:
        return {"sentiment": {}, "topics": [], "summary": ""}

    respuestas = (
        db.query(Respuesta)
        .filter(
            Respuesta.id_encuesta.in_(subquery_ids),
            Respuesta.id_pregunta == p9.id,
            Respuesta.valor_texto.isnot(None),
        )
        .all()
    )

    sentimientos = {"positivo": 0, "neutro": 0, "negativo": 0}
    conteo_topicos = {}
    comentarios_para_resumen = []

    for r in respuestas:
        if r.ai_sentimiento and r.ai_sentimiento in sentimientos:
            sentimientos[r.ai_sentimiento] += 1

        topic = r.ai_tema or "otro"
        if topic != "sin_comentario":
            conteo_topicos[topic] = conteo_topicos.get(topic, 0) + 1
            if r.valor_texto and len(r.valor_texto.strip()) > 5:
                comentarios_para_resumen.append(r.valor_texto.strip())

    lista_topicos = [
        {
            "topic": t,
            "label": TOPIC_LABELS.get(t, t),
            "count": count,
        }
        for t, count in conteo_topicos.items()
    ]
    lista_topicos.sort(key=lambda x: x["count"], reverse=True)

    summary_text = analizador.summarize(comentarios_para_resumen[:30]) if comentarios_para_resumen else "No hay suficientes comentarios registrados."

    return {
        "sentiment": sentimientos,
        "topics": lista_topicos,
        "total_comments": len(respuestas),
        "total_classified": sum(sentimientos.values()),
        "summary": summary_text,
    }


def obtener_lista_comentarios(db: Session, id_curso: int = None, tema: str = None, sentimiento: str = None, busqueda: str = None, pagina: int = 1, tamanio_pagina: int = 50) -> dict:
    """Lista comentarios abiertos con filtros y paginación."""
    p9 = db.query(Pregunta).filter(Pregunta.nro_pregunta == 9).first()
    if not p9:
        return {"total": 0, "items": []}

    query = (
        db.query(Respuesta, Encuesta, Curso)
        .join(Encuesta, Respuesta.id_encuesta == Encuesta.id)
        .join(Curso, Encuesta.id_curso == Curso.id)
        .filter(
            Respuesta.id_pregunta == p9.id,
            Respuesta.valor_texto.isnot(None),
            Respuesta.valor_texto != "",
        )
    )

    if id_curso:
        query = query.filter(Encuesta.id_curso == id_curso)
    if tema and tema != "todos":
        query = query.filter(Respuesta.ai_tema == tema)
    if sentimiento and sentimiento != "todos":
        query = query.filter(Respuesta.ai_sentimiento == sentimiento)
    if busqueda:
        query = query.filter(Respuesta.valor_texto.ilike(f"%{busqueda}%"))

    total = query.count()
    items_crudos = query.order_by(Encuesta.fecha_envio.desc()).offset((pagina - 1) * tamanio_pagina).limit(tamanio_pagina).all()

    items = []
    for resp, survey, course in items_crudos:
        items.append({
            "id": resp.id,
            "survey_id": survey.id,
            "source_id": survey.id_respuesta_origen,
            "course_name": course.nombre,
            "submitted_at": survey.fecha_envio.isoformat() if survey.fecha_envio else None,
            "text": resp.valor_texto,
            "topic": resp.ai_tema or "otro",
            "topic_label": TOPIC_LABELS.get(resp.ai_tema, "Otro"),
            "sentiment": resp.ai_sentimiento or "neutro",
        })

    return {"total": total, "page": pagina, "page_size": tamanio_pagina, "items": items}


# Alias de compatibilidad
get_dashboard_kpis = obtener_kpis_tablero
get_questions_breakdown = obtener_desglose_preguntas
get_courses_comparison = obtener_comparativa_cursos
get_temporal_trends = obtener_tendencias_temporales
get_ai_insights = obtener_insights_ia
get_comments_list = obtener_lista_comentarios
_apply_filters = _aplicar_filtros
