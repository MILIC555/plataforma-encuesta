# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import func, case, distinct, and_
from app.db.models.encuesta import Encuesta
from app.db.models.curso import Curso
from app.db.models.pregunta import Pregunta
from app.db.models.respuesta import Respuesta
from app.ai.base import TOPIC_LABELS
from app.ai.analizador import analizador


def _filtrar_encuestas(query, id_curso=None, fecha_inicio=None, fecha_fin=None, plataforma=None):
    if id_curso:
        query = query.filter(Encuesta.id_curso == id_curso)
    if fecha_inicio:
        query = query.filter(Encuesta.fecha_envio >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Encuesta.fecha_envio <= fecha_fin)
    return query


def obtener_kpis_tablero(db: Session, id_curso: int = None, fecha_inicio = None, fecha_fin = None, plataforma: str = None) -> dict:
    """Calcula KPIs agregados por SQL para Campus Córdoba."""
    q_enc = _filtrar_encuestas(db.query(func.count(distinct(Encuesta.id))), id_curso, fecha_inicio, fecha_fin)
    total_encuestas = q_enc.scalar() or 0

    q_cur = db.query(func.count(distinct(Curso.id))).join(Encuesta, Curso.id == Encuesta.id_curso)
    total_cursos = q_cur.scalar() or 0

    if total_encuestas == 0:
        return {
            "total_surveys": 0,
            "overall_average": 0.0,
            "nps": 0.0,
            "satisfaction_pct": 0.0,
            "promoters_pct": 0.0,
            "detractors_pct": 0.0,
            "total_courses": total_cursos,
            "platform": "campus_cordoba",
        }

    # IDs de preguntas de referencia en Campus Córdoba (Q6 y Q8)
    p6 = db.query(Pregunta.id).filter(Pregunta.plataforma == "campus_cordoba", Pregunta.nro_pregunta == 6).scalar()
    p8 = db.query(Pregunta.id).filter(Pregunta.plataforma == "campus_cordoba", Pregunta.nro_pregunta == 8).scalar()

    q = (
        db.query(
            func.avg(Respuesta.valor_numerico).label("prom_gral"),
            func.sum(case((and_(Respuesta.id_pregunta == p8, Respuesta.valor_numerico >= 9), 1), else_=0)).label("promotores"),
            func.sum(case((and_(Respuesta.id_pregunta == p8, Respuesta.valor_numerico <= 6), 1), else_=0)).label("detractores"),
            func.sum(case((and_(Respuesta.id_pregunta == p8, Respuesta.valor_numerico.isnot(None)), 1), else_=0)).label("total_p8"),
            func.sum(case((and_(Respuesta.id_pregunta == p6, Respuesta.valor_numerico >= 8), 1), else_=0)).label("satisfechos"),
            func.sum(case((and_(Respuesta.id_pregunta == p6, Respuesta.valor_numerico.isnot(None)), 1), else_=0)).label("total_p6"),
        )
        .join(Encuesta, Respuesta.id_encuesta == Encuesta.id)
    )

    q = _filtrar_encuestas(q, id_curso, fecha_inicio, fecha_fin)
    res = q.first()

    prom_gral = round(float(res.prom_gral), 2) if res and res.prom_gral else 0.0
    
    total_p8 = res.total_p8 or 0 if res else 0
    promotores = res.promotores or 0 if res else 0
    detractores = res.detractores or 0 if res else 0
    nps_score = round(((promotores - detractores) / total_p8) * 100, 1) if total_p8 > 0 else 0.0
    promoters_pct = round((promotores / total_p8) * 100, 1) if total_p8 > 0 else 0.0
    detractors_pct = round((detractores / total_p8) * 100, 1) if total_p8 > 0 else 0.0

    total_p6 = res.total_p6 or 0 if res else 0
    satisfechos = res.satisfechos or 0 if res else 0
    satisfaction_pct = round((satisfechos / total_p6) * 100, 1) if total_p6 > 0 else 0.0

    return {
        "total_surveys": total_encuestas,
        "overall_average": prom_gral,
        "nps": nps_score,
        "satisfaction_pct": satisfaction_pct,
        "promoters_pct": promoters_pct,
        "detractors_pct": detractors_pct,
        "total_courses": total_cursos,
        "platform": "campus_cordoba",
    }


def obtener_desglose_preguntas(db: Session, id_curso: int = None, fecha_inicio = None, fecha_fin = None, plataforma: str = None) -> list[dict]:
    """Obtiene el desglose de promedios y distribución para las preguntas numéricas de Campus Córdoba."""
    preguntas = db.query(Pregunta).filter(Pregunta.tipo == "numerica").order_by(Pregunta.nro_pregunta).all()
    if not preguntas:
        return []

    # 1. Promedios y conteos numéricos
    q_avg = (
        db.query(
            Respuesta.id_pregunta,
            func.avg(Respuesta.valor_numerico).label("promedio"),
            func.count(Respuesta.id).label("conteo"),
        )
        .join(Encuesta, Respuesta.id_encuesta == Encuesta.id)
        .filter(Respuesta.valor_numerico.isnot(None))
    )
    q_avg = _filtrar_encuestas(q_avg, id_curso, fecha_inicio, fecha_fin)
    res_avg = {row.id_pregunta: (round(float(row.promedio), 2), row.conteo) for row in q_avg.group_by(Respuesta.id_pregunta).all()}

    # 2. Distribución de 1 a 10
    q_dist = (
        db.query(
            Respuesta.id_pregunta,
            Respuesta.valor_numerico,
            func.count(Respuesta.id).label("cant"),
        )
        .join(Encuesta, Respuesta.id_encuesta == Encuesta.id)
        .filter(Respuesta.valor_numerico.isnot(None))
    )
    q_dist = _filtrar_encuestas(q_dist, id_curso, fecha_inicio, fecha_fin)
    dist_map = {}
    for pid, val, cant in q_dist.group_by(Respuesta.id_pregunta, Respuesta.valor_numerico).all():
        if pid not in dist_map:
            dist_map[pid] = {str(i): 0 for i in range(1, 11)}
        if 1 <= val <= 10:
            dist_map[pid][str(val)] = cant

    resultados = []
    for p in preguntas:
        prom, total_num = res_avg.get(p.id, (0.0, 0))
        dist = dist_map.get(p.id, {str(i): 0 for i in range(1, 11)})

        resultados.append({
            "question_number": p.nro_pregunta,
            "platform": "campus_cordoba",
            "type": p.tipo,
            "short_label": p.etiqueta_corta,
            "description": p.descripcion,
            "average": prom,
            "count": total_num,
            "distribution": dist,
            "text_options": [],
            "text_count": 0,
            "total_answers": total_num,
        })

    return resultados


def obtener_comparativa_cursos(db: Session, fecha_inicio = None, fecha_fin = None, plataforma: str = None) -> list[dict]:
    """Compara todos los cursos en una sola consulta SQL agrupada."""
    p6 = db.query(Pregunta.id).filter(Pregunta.plataforma == "campus_cordoba", Pregunta.nro_pregunta == 6).scalar()
    p8 = db.query(Pregunta.id).filter(Pregunta.plataforma == "campus_cordoba", Pregunta.nro_pregunta == 8).scalar()

    q = (
        db.query(
            Curso.id,
            Curso.nombre,
            Curso.codigo,
            func.count(distinct(Encuesta.id)).label("total_encuestas"),
            func.avg(Respuesta.valor_numerico).label("prom_gral"),
            func.sum(case((and_(Respuesta.id_pregunta == p8, Respuesta.valor_numerico >= 9), 1), else_=0)).label("promotores"),
            func.sum(case((and_(Respuesta.id_pregunta == p8, Respuesta.valor_numerico <= 6), 1), else_=0)).label("detractores"),
            func.sum(case((and_(Respuesta.id_pregunta == p8, Respuesta.valor_numerico.isnot(None)), 1), else_=0)).label("total_p8"),
            func.sum(case((and_(Respuesta.id_pregunta == p6, Respuesta.valor_numerico >= 8), 1), else_=0)).label("satisfechos"),
            func.sum(case((and_(Respuesta.id_pregunta == p6, Respuesta.valor_numerico.isnot(None)), 1), else_=0)).label("total_p6"),
        )
        .join(Encuesta, Curso.id == Encuesta.id_curso)
        .join(Respuesta, Encuesta.id == Respuesta.id_encuesta)
    )

    q = _filtrar_encuestas(q, None, fecha_inicio, fecha_fin)
    filas = q.group_by(Curso.id).all()

    lista_resumen = []
    for r in filas:
        t8 = r.total_p8 or 0
        nps = round(((r.promotores - r.detractores) / t8) * 100, 1) if t8 > 0 else 0.0
        
        t6 = r.total_p6 or 0
        sat_pct = round((r.satisfechos / t6) * 100, 1) if t6 > 0 else 0.0

        lista_resumen.append({
            "id": r.id,
            "name": r.nombre,
            "code": r.codigo,
            "platform": "campus_cordoba",
            "platform_label": "Campus Córdoba",
            "total_surveys": r.total_encuestas,
            "overall_average": round(float(r.prom_gral), 2) if r.prom_gral else 0.0,
            "nps": nps,
            "satisfaction_pct": sat_pct,
        })

    lista_resumen.sort(key=lambda x: x["overall_average"], reverse=True)
    return lista_resumen


def obtener_tendencias_temporales(db: Session, id_curso: int = None, plataforma: str = None) -> list[dict]:
    """Genera serie temporal agrupada directamente por SQL."""
    q = (
        db.query(
            Encuesta.periodo_anio,
            Encuesta.periodo_mes,
            func.count(distinct(Encuesta.id)).label("cant_encuestas"),
            func.avg(Respuesta.valor_numerico).label("prom_calificacion"),
        )
        .join(Respuesta, Encuesta.id == Respuesta.id_encuesta)
        .filter(Respuesta.valor_numerico.isnot(None))
    )

    q = _filtrar_encuestas(q, id_curso, None, None)
    filas = q.group_by(Encuesta.periodo_anio, Encuesta.periodo_mes).order_by(Encuesta.periodo_anio, Encuesta.periodo_mes).all()

    return [
        {
            "period": f"{r.periodo_anio}-{r.periodo_mes:02d}",
            "total_surveys": r.cant_encuestas,
            "average_score": round(float(r.prom_calificacion), 2) if r.prom_calificacion else 0.0,
        }
        for r in filas
    ]


def obtener_insights_ia(db: Session, id_curso: int = None, fecha_inicio = None, fecha_fin = None, plataforma: str = None) -> dict:
    """Métricas de análisis de IA para comentarios de texto abierto unificados (Pregunta 9)."""
    p_text_ids = [p.id for p in db.query(Pregunta.id).filter(Pregunta.tipo == "texto").all()]
    if not p_text_ids:
        return {"sentiment": {}, "topics": [], "summary": "", "negative_insights": {}}

    q_sent = (
        db.query(Respuesta.ai_sentimiento, func.count(Respuesta.id))
        .join(Encuesta, Respuesta.id_encuesta == Encuesta.id)
        .filter(Respuesta.id_pregunta.in_(p_text_ids), Respuesta.ai_sentimiento.isnot(None))
    )
    q_sent = _filtrar_encuestas(q_sent, id_curso, fecha_inicio, fecha_fin)

    sentimientos = {"positivo": 0, "neutro": 0, "negativo": 0}
    for sent, cant in q_sent.group_by(Respuesta.ai_sentimiento).all():
        if sent in sentimientos:
            sentimientos[sent] = cant

    q_top = (
        db.query(Respuesta.ai_tema, func.count(Respuesta.id))
        .join(Encuesta, Respuesta.id_encuesta == Encuesta.id)
        .filter(Respuesta.id_pregunta.in_(p_text_ids), Respuesta.ai_tema.isnot(None), Respuesta.ai_tema != "sin_comentario")
    )
    q_top = _filtrar_encuestas(q_top, id_curso, fecha_inicio, fecha_fin)

    lista_topicos = [
        {"topic": topic, "label": TOPIC_LABELS.get(topic, topic), "count": cant}
        for topic, cant in q_top.group_by(Respuesta.ai_tema).order_by(func.count(Respuesta.id).desc()).all()
    ]

    q_neg_top = (
        db.query(Respuesta.ai_tema, func.count(Respuesta.id))
        .join(Encuesta, Respuesta.id_encuesta == Encuesta.id)
        .filter(
            Respuesta.id_pregunta.in_(p_text_ids),
            Respuesta.ai_sentimiento == "negativo",
            Respuesta.ai_tema.isnot(None),
            Respuesta.ai_tema != "sin_comentario"
        )
    )
    q_neg_top = _filtrar_encuestas(q_neg_top, id_curso, fecha_inicio, fecha_fin)

    negativos_por_tema = [
        {"topic": topic, "label": TOPIC_LABELS.get(topic, topic), "count": cant}
        for topic, cant in q_neg_top.group_by(Respuesta.ai_tema).order_by(func.count(Respuesta.id).desc()).all()
    ]

    total_comments = sum(sentimientos.values())
    pos = sentimientos.get("positivo", 0)
    neg = sentimientos.get("negativo", 0)
    top_destacados = [t["label"] for t in lista_topicos[:2]]

    if total_comments > 0:
        summary_text = f"Análisis semántico con Hugging Face ({total_comments} opiniones): {pos} valoraciones positivas y {neg} oportunidades de mejora."
        if top_destacados:
            summary_text += f" Las dimensiones con mayor volumen de comentarios fueron: {', '.join(top_destacados)}."
    else:
        summary_text = "No hay suficientes comentarios registrados."

    return {
        "sentiment": sentimientos,
        "topics": lista_topicos,
        "total_comments": total_comments,
        "total_classified": sum(sentimientos.values()),
        "summary": summary_text,
        "negative_insights": {
            "total_negatives": neg,
            "pct_of_total": round((neg / total_comments * 100), 1) if total_comments > 0 else 0.0,
            "by_topic": negativos_por_tema,
        }
    }


def obtener_lista_comentarios(db: Session, id_curso: int = None, tema: str = None, sentimiento: str = None, busqueda: str = None, plataforma: str = None, pagina: int = 1, tamanio_pagina: int = 50) -> dict:
    """Lista comentarios abiertos paginados de forma eficiente."""
    p_text_ids = [p.id for p in db.query(Pregunta.id).filter(Pregunta.tipo == "texto").all()]
    if not p_text_ids:
        return {"total": 0, "items": []}

    query = (
        db.query(Respuesta, Encuesta, Curso)
        .join(Encuesta, Respuesta.id_encuesta == Encuesta.id)
        .join(Curso, Encuesta.id_curso == Curso.id)
        .filter(
            Respuesta.id_pregunta.in_(p_text_ids),
            Respuesta.valor_texto.isnot(None),
            Respuesta.valor_texto != "",
        )
    )

    query = _filtrar_encuestas(query, id_curso, None, None)

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
            "platform": "campus_cordoba",
            "course_name": course.nombre,
            "submitted_at": survey.fecha_envio.isoformat() if survey.fecha_envio else None,
            "text": resp.valor_texto,
            "topic": resp.ai_tema or "otro",
            "topic_label": TOPIC_LABELS.get(resp.ai_tema, "Otro"),
            "sentiment": resp.ai_sentimiento or "neutro",
        })

    return {"total": total, "page": pagina, "page_size": tamanio_pagina, "items": items}


# Alias de exportación
_aplicar_filtros = _filtrar_encuestas
_apply_filters = _filtrar_encuestas
get_dashboard_kpis = obtener_kpis_tablero
get_questions_breakdown = obtener_desglose_preguntas
get_courses_comparison = obtener_comparativa_cursos
get_temporal_trends = obtener_tendencias_temporales
get_ai_insights = obtener_insights_ia
get_comments_list = obtener_lista_comentarios
