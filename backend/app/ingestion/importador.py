import unicodedata
import re
import logging
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import text
from app.db.models.curso import Curso
from app.db.models.pregunta import Pregunta
from app.db.models.encuesta import Encuesta
from app.db.models.respuesta import Respuesta
from app.ingestion.normalizador import leer_archivo_a_dataframe, normalizar_datos_encuesta

logger = logging.getLogger(__name__)


def _normalizar_clave_curso(texto: str) -> str:
    """
    Normaliza el nombre de un curso removiendo acentos, diacríticos
    y espacios múltiples para coincidir exactamente con la colación de MySQL (ai_ci).
    """
    if not texto:
        return ""
    s = unicodedata.normalize("NFKD", str(texto))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def importar_archivos_masivos(db: Session, lista_archivos: list[tuple[bytes, str]]) -> dict:
    """
    Procesa de forma ultra-rápida, segura y masiva una lista de archivos (CSV o Excel).
    Aplica consultas raw de alta velocidad, inserción masiva directa y normalización de acentos.
    """
    if not lista_archivos:
        return {
            "success": True,
            "message": "No se enviaron archivos para procesar.",
            "total_files": 0,
            "total_rows": 0,
            "imported_surveys": 0,
            "skipped_duplicates": 0,
            "courses_affected": [],
            "files_details": [],
        }

    # 1. Catálogo de preguntas oficiales
    preguntas_raw = db.connection().execute(text("SELECT id_pregunta, nro_pregunta FROM preguntas")).fetchall()
    mapa_preguntas = {nro: pid for pid, nro in preguntas_raw}

    # 2. Cursos existentes indexados por clave normalizada (sin acentos)
    cursos_raw = db.connection().execute(text("SELECT id_curso, nombre_curso FROM cursos")).fetchall()
    mapa_cursos = {}
    for cid, cnombre in cursos_raw:
        key = _normalizar_clave_curso(cnombre)
        mapa_cursos[key] = {"id": cid, "nombre": cnombre}

    # 3. IDs de respuesta origen existentes (consulta directa ultra rápida)
    ids_raw = db.connection().execute(text("SELECT id_respuesta_origen FROM encuestas")).fetchall()
    ids_origen_existentes = set(r[0] for r in ids_raw)

    total_filas = 0
    total_importadas = 0
    total_duplicadas = 0
    cursos_totales = set()
    detalles_archivos = []

    # 4. Fase 1: Parsear todos los archivos en memoria
    archivos_procesados_data = []
    cursos_nuevos_a_crear = {}

    for contenido, nombre in lista_archivos:
        try:
            df = leer_archivo_a_dataframe(contenido, nombre)
            items = normalizar_datos_encuesta(df)
            archivos_procesados_data.append((nombre, len(df), items, None))
            total_filas += len(df)

            # Detectar cursos que no existen
            for item in items:
                c_name = re.sub(r"\s+", " ", item["nombre_curso"].strip())
                c_key = _normalizar_clave_curso(c_name)
                if c_key not in mapa_cursos and c_key not in cursos_nuevos_a_crear:
                    cursos_nuevos_a_crear[c_key] = {
                        "nombre": c_name,
                        "institucion": item["institucion"],
                        "departamento": item["departamento"],
                    }
        except Exception as e:
            logger.error(f"Error procesando archivo {nombre}: {e}")
            archivos_procesados_data.append((nombre, 0, [], str(e)))

    # Crear los cursos nuevos que hagan falta
    for c_key, c_info in cursos_nuevos_a_crear.items():
        try:
            curso_obj = Curso(
                nombre=c_info["nombre"],
                institucion=c_info["institucion"],
                departamento=c_info["departamento"],
            )
            db.add(curso_obj)
            db.flush()
            mapa_cursos[c_key] = {"id": curso_obj.id, "nombre": curso_obj.nombre}
        except Exception:
            db.rollback()
            # Si colisionó por colación de MySQL, buscar el ID existente
            c_existente = db.connection().execute(
                text("SELECT id_curso, nombre_curso FROM cursos WHERE nombre_curso = :n"),
                {"n": c_info["nombre"]},
            ).fetchone()
            if c_existente:
                mapa_cursos[c_key] = {"id": c_existente[0], "nombre": c_existente[1]}

    # 5. Fase 2: Procesar e insertar encuestas y respuestas
    for nombre, cant_filas, items, err in archivos_procesados_data:
        if err:
            detalles_archivos.append({
                "archivo": nombre,
                "success": False,
                "error": err,
                "total_rows": 0,
                "imported_surveys": 0,
                "skipped_duplicates": 0,
                "courses_affected": [],
            })
            continue

        arch_importadas = 0
        arch_duplicadas = 0
        arch_cursos_afectados = set()

        encuestas_para_insertar = []
        respuestas_preparadas_por_encuesta = []

        for item in items:
            src_id = item["id_respuesta_origen"]
            if src_id in ids_origen_existentes:
                arch_duplicadas += 1
                continue

            c_name = re.sub(r"\s+", " ", item["nombre_curso"].strip())
            c_key = _normalizar_clave_curso(c_name)
            curso_info = mapa_cursos.get(c_key)
            if not curso_info:
                continue

            arch_cursos_afectados.add(curso_info["nombre"])
            cursos_totales.add(curso_info["nombre"])

            encuesta = Encuesta(
                id_respuesta_origen=src_id,
                id_curso=curso_info["id"],
                fecha_envio=item["fecha_envio"],
                periodo_anio=item["periodo_anio"],
                periodo_mes=item["periodo_mes"],
                periodo_semana=item["periodo_semana"],
            )
            encuestas_para_insertar.append(encuesta)
            respuestas_preparadas_por_encuesta.append(item["respuestas"])

            ids_origen_existentes.add(src_id)
            arch_importadas += 1

        # Inserción en bloques de 500 para máxima velocidad
        BATCH_SIZE = 500
        for i in range(0, len(encuestas_para_insertar), BATCH_SIZE):
            lote_enc = encuestas_para_insertar[i:i + BATCH_SIZE]
            lote_resp = respuestas_preparadas_por_encuesta[i:i + BATCH_SIZE]

            db.add_all(lote_enc)
            db.flush()  # Obtiene todos los IDs generados por MySQL en un solo viaje

            respuestas_batch_mappings = []
            for enc_obj, resp_list in zip(lote_enc, lote_resp):
                for ans in resp_list:
                    q_num = ans["nro_pregunta"]
                    p_id = mapa_preguntas.get(q_num)
                    if not p_id:
                        continue

                    tema = None
                    sent = None
                    if q_num == 9:
                        if not ans["valor_texto"] or ans.get("es_ruido", False):
                            tema = "sin_comentario"
                            sent = "neutro"

                    respuestas_batch_mappings.append({
                        "id_encuesta": enc_obj.id,
                        "id_pregunta": p_id,
                        "valor_numerico": ans["valor_numerico"],
                        "valor_texto": ans["valor_texto"],
                        "ai_tema": tema,
                        "ai_sentimiento": sent,
                    })

            if respuestas_batch_mappings:
                db.bulk_insert_mappings(Respuesta, respuestas_batch_mappings)

        db.commit()

        total_importadas += arch_importadas
        total_duplicadas += arch_duplicadas

        detalles_archivos.append({
            "archivo": nombre,
            "success": True,
            "message": f"Se importaron {arch_importadas} encuestas ({arch_duplicadas} duplicadas ignoradas).",
            "total_rows": cant_filas,
            "imported_surveys": arch_importadas,
            "skipped_duplicates": arch_duplicadas,
            "courses_affected": list(arch_cursos_afectados),
        })

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


def importar_archivo_encuesta(db: Session, contenido_archivo: bytes, nombre_archivo: str) -> dict:
    """Importa un archivo individual reutilizando el motor masivo de alta velocidad."""
    res = importar_archivos_masivos(db, [(contenido_archivo, nombre_archivo)])
    if res.get("files_details"):
        return res["files_details"][0]
    return res


import_survey_file = importar_archivo_encuesta
