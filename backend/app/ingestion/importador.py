import logging
from sqlalchemy.orm import Session
from app.db.models.curso import Curso
from app.db.models.pregunta import Pregunta
from app.db.models.encuesta import Encuesta
from app.db.models.respuesta import Respuesta
from app.ingestion.normalizador import leer_archivo_a_dataframe, normalizar_datos_encuesta

logger = logging.getLogger(__name__)


def importar_archivo_encuesta(db: Session, contenido_archivo: bytes, nombre_archivo: str) -> dict:
    """
    Lee un archivo, normaliza su estructura e importa las encuestas y respuestas
    en la base de datos relacional (cursos, encuestas, preguntas, respuestas).
    Ignora automáticamente registros duplicados basándose en id_respuesta_origen.
    """
    try:
        df = leer_archivo_a_dataframe(contenido_archivo, nombre_archivo)
        lista_normalizada = normalizar_datos_encuesta(df)
    except Exception as e:
        logger.error(f"Error al leer/normalizar archivo {nombre_archivo}: {e}")
        return {
            "archivo": nombre_archivo,
            "success": False,
            "error": f"Error de lectura: {str(e)}",
            "total_rows": 0,
            "imported_surveys": 0,
            "skipped_duplicates": 0,
            "courses_affected": [],
        }

    if not lista_normalizada:
        return {
            "archivo": nombre_archivo,
            "success": False,
            "message": "No se encontraron filas válidas para importar en el archivo.",
            "total_rows": len(df) if 'df' in locals() else 0,
            "imported_surveys": 0,
            "skipped_duplicates": 0,
            "courses_affected": [],
        }

    # Cargar preguntas oficiales indexadas por número
    preguntas = db.query(Pregunta).all()
    mapa_preguntas = {p.nro_pregunta: p.id for p in preguntas}

    # Cargar cursos existentes indexados por nombre
    cursos = db.query(Curso).all()
    mapa_cursos = {c.nombre.strip().lower(): c for c in cursos}

    # Obtener lista de IDs de respuesta origen existentes para evitar duplicados
    ids_origen_existentes = set(
        sid[0] for sid in db.query(Encuesta.id_respuesta_origen).all()
    )

    importadas_count = 0
    omitidas_count = 0
    cursos_afectados = set()

    for item in lista_normalizada:
        src_id = item["id_respuesta_origen"]
        if src_id in ids_origen_existentes:
            omitidas_count += 1
            continue

        c_name = item["nombre_curso"].strip()
        c_key = c_name.lower()
        cursos_afectados.add(c_name)

        if c_key in mapa_cursos:
            curso = mapa_cursos[c_key]
            if item["institucion"] and not curso.institucion:
                curso.institucion = item["institucion"]
            if item["departamento"] and not curso.departamento:
                curso.departamento = item["departamento"]
        else:
            curso = Curso(
                nombre=c_name,
                institucion=item["institucion"],
                departamento=item["departamento"],
            )
            db.add(curso)
            db.flush()
            mapa_cursos[c_key] = curso

        # Crear Encuesta
        encuesta = Encuesta(
            id_respuesta_origen=src_id,
            id_curso=curso.id,
            fecha_envio=item["fecha_envio"],
            periodo_anio=item["periodo_anio"],
            periodo_mes=item["periodo_mes"],
            periodo_semana=item["periodo_semana"],
        )
        db.add(encuesta)
        db.flush()
        ids_origen_existentes.add(src_id)

        # Crear Respuestas para cada pregunta
        for ans in item["respuestas"]:
            q_num = ans["nro_pregunta"]
            p_id = mapa_preguntas.get(q_num)
            if not p_id:
                continue

            resp = Respuesta(
                id_encuesta=encuesta.id,
                id_pregunta=p_id,
                valor_numerico=ans["valor_numerico"],
                valor_texto=ans["valor_texto"],
            )

            # Si es pregunta 9 y es comentario trivial o vacío, preclasificar como neutro
            if q_num == 9:
                if not ans["valor_texto"] or ans.get("es_ruido", False):
                    resp.ai_tema = "sin_comentario"
                    resp.ai_sentimiento = "neutro"

            db.add(resp)

        importadas_count += 1

    db.commit()

    return {
        "archivo": nombre_archivo,
        "success": True,
        "message": f"Se importaron {importadas_count} encuestas ({omitidas_count} duplicadas ignoradas).",
        "total_rows": len(df),
        "imported_surveys": importadas_count,
        "skipped_duplicates": omitidas_count,
        "courses_affected": list(cursos_afectados),
    }


def importar_archivos_masivos(db: Session, lista_archivos: list[tuple[bytes, str]]) -> dict:
    """
    Procesa de forma masiva una lista de archivos (CSV o Excel).
    Consolida las métricas de importación y omite duplicados transparentemente.
    """
    total_filas = 0
    total_importadas = 0
    total_duplicadas = 0
    cursos_totales = set()
    detalles_archivos = []

    for contenido, nombre in lista_archivos:
        res = importar_archivo_encuesta(db, contenido, nombre)
        detalles_archivos.append(res)
        total_filas += res.get("total_rows", 0)
        total_importadas += res.get("imported_surveys", 0)
        total_duplicadas += res.get("skipped_duplicates", 0)
        for c in res.get("courses_affected", []):
            cursos_totales.add(c)

    return {
        "success": True,
        "message": f"Proceso masivo finalizado: {len(lista_archivos)} archivo(s) procesados. {total_importadas} encuestas nuevas importadas ({total_duplicadas} duplicadas ignoradas).",
        "total_files": len(lista_archivos),
        "total_rows": total_filas,
        "imported_surveys": total_importadas,
        "skipped_duplicates": total_duplicadas,
        "courses_affected": list(cursos_totales),
        "files_details": detalles_archivos,
    }


import_survey_file = importar_archivo_encuesta
