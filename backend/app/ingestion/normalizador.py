import re
import io
import pandas as pd
from typing import BinaryIO, Union

# Aliases de columnas para Campus Córdoba (Formatos de 9 Preguntas y 5 Preguntas)
MAPA_PREGUNTAS_9P = {
    1: ["Q01_1", "Q01", "Q1_1", "Q1", "p1", "pregunta_1", "aula virtual"],
    2: ["Q02_2", "Q02", "Q2_2", "Q2", "p2", "pregunta_2", "utilidad de contenidos"],
    3: ["Q03_3", "Q03", "Q3_3", "Q3", "p3", "pregunta_3", "material didactico", "material didáctico"],
    4: ["Q04_4", "Q04", "Q4_4", "Q4", "p4", "pregunta_4", "desempeño tutorial", "desempeño del tutor"],
    5: ["Q05_5", "Q05", "Q5_5", "Q5", "p5", "pregunta_5", "atención administrativa", "atencion administrativa"],
    6: ["Q06_6", "Q06", "Q6_6", "Q6", "p6", "pregunta_6", "satisfacción general", "satisfaccion general"],
    7: ["Q07_7", "Q07", "Q7_7", "Q7", "p7", "pregunta_7", "expectativas"],
    8: ["Q08_8", "Q08", "Q8_8", "Q8", "p8", "pregunta_8", "nps", "recomendación", "recomendacion"],
    9: ["Q09_9", "Q09", "Q9_9", "Q9", "p9", "pregunta_9", "observaciones", "sugerencias", "comentario"],
}

# Aliases para encuestas de 5 preguntas (pre-abril 2026) y su equivalencia con las 9 canónicas
# 5P Q1 -> Canónica Q2 (Utilidad)
# 5P Q2 -> Canónica Q4 (Tutor)
# 5P Q3 -> Canónica Q3 (Material)
# 5P Q4 -> Canónica Q5 (Administrativa)
# 5P Q5 -> Canónica Q9 (Observaciones)
MAPA_PREGUNTAS_5P = {
    1: ["Q01_1", "Q01", "Q1_1", "Q1", "p1", "incrementar sus conocimientos", "utiles para incrementar", "útiles para incrementar"],
    2: ["Q02_2", "Q02", "Q2_2", "Q2", "p2", "tutor/a fue claro", "tutor fue claro", "tutora fue clara", "comunicación adecuada"],
    3: ["Q03_3", "Q03", "Q3_3", "Q3", "p3", "metodología y recursos", "metodologia y recursos", "recursos didácticos"],
    4: ["Q04_4", "Q04", "Q4_4", "Q4", "p4", "subdirección de capacitación", "subdireccion de capacitacion", "atención del área administrativa"],
    5: ["Q05_5", "Q05", "Q5_5", "Q5", "p5", "observaciones", "sugerencias", "propuestas", "comentario"],
}

# Mapeo de equivalencia: nro_pregunta en encuesta 5P -> nro_pregunta_canónica en Campus Córdoba
MAPEO_EQUIVALENCIA_5P_A_CANONICA = {
    1: 2,  # 5P Q1 (Contenidos utiles) -> Canónica Q2
    2: 4,  # 5P Q2 (Tutor claro/interes) -> Canónica Q4
    3: 3,  # 5P Q3 (Metodologia y recursos) -> Canónica Q3
    4: 5,  # 5P Q4 (Atencion administrativa) -> Canónica Q5
    5: 9,  # 5P Q5 (Observaciones) -> Canónica Q9 (Texto)
}

COMENTARIOS_RUIDO = {
    "", "-", "--", "---", ".", "..", "...", "....", "/", "//", "*", "(y)", "x", "xx", "xxx",
    "nada", "ninguna", "ninguno", "ningun", "ningún", "no", "no tengo", "no hay",
    "sin comentarios", "sin observaciones", "sin sugerencias", "ninguna sugerencia",
    "no tengo ninguna sugerencia", "no tengo sugerencias", "nada para agregar",
    "nada que agregar", "nada que mejorar", "nada por el momento", "ninguna por el momento",
    "no tengo observaciones", "sin observaciones para hacer", "sin nada que agregar"
}


def _parsear_valor_escala(raw: any) -> int | None:
    """
    Convierte '10 : 10' -> 10, '8 : 8' -> 8, o 10 -> 10.
    Si está vacío o no es un número de 1 a 10, devuelve None.
    """
    if raw is None or pd.isna(raw):
        return None
    raw_str = str(raw).strip()
    if not raw_str:
        return None
    try:
        if ":" in raw_str:
            val = int(raw_str.split(":")[-1].strip())
        else:
            val = int(float(raw_str))
        if 1 <= val <= 10:
            return val
        return None
    except (ValueError, IndexError):
        return None


def es_comentario_ruido(texto: str) -> bool:
    """Verifica si un comentario es trivial/relleno para no enviarlo innecesariamente a la IA."""
    if not texto:
        return True
    limpio = texto.strip().lower()
    limpio = re.sub(r"[^\w\s]", "", limpio).strip()
    if len(limpio) <= 1:
        return True
    return limpio in COMENTARIOS_RUIDO


def _buscar_columna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    for c in df.columns:
        norm_c = str(c).strip().lower()
        for cand in candidatos:
            if norm_c == cand.lower() or cand.lower() in norm_c:
                return c
    return None


def detectar_formato_encuesta(df: pd.DataFrame) -> str:
    """
    Detecta automáticamente el formato de la encuesta de Campus Córdoba:
    - '9_preguntas' (Desde Abril 2026: Q1..Q8 numéricas + Q9 texto)
    - '5_preguntas' (Anterior a Abril 2026: Q1..Q4 numéricas + Q5 texto)
    """
    # Si tiene columnas de Q6, Q7 o Q8 es de 9 preguntas
    tiene_q6 = _buscar_columna(df, ["Q06", "Q6", "p6", "satisfacción general", "satisfaccion general"])
    tiene_q8 = _buscar_columna(df, ["Q08", "Q8", "p8", "nps", "recomendación", "recomendacion"])
    if tiene_q6 or tiene_q8:
        return "9_preguntas"

    # Si tiene columna Q5 pero no Q6
    tiene_q5 = _buscar_columna(df, ["Q05", "Q5", "p5", "observaciones", "propuestas"])
    if tiene_q5 and not tiene_q6:
        return "5_preguntas"

    # Conteo general de columnas de preguntas
    cols_q = [c for c in df.columns if re.match(r"^Q0?\d", str(c).strip(), re.IGNORECASE)]
    if len(cols_q) >= 8:
        return "9_preguntas"

    return "5_preguntas"


def leer_archivo_a_dataframe(contenido_archivo: Union[bytes, BinaryIO], nombre_archivo: str) -> pd.DataFrame:
    """Lee un archivo CSV, Excel o PDF y lo transforma en un DataFrame normalizado."""
    nombre_min = nombre_archivo.lower()
    if nombre_min.endswith(".pdf"):
        from app.ingestion.lector_pdf import leer_pdf_a_dataframe
        return leer_pdf_a_dataframe(contenido_archivo, nombre_archivo)

    if isinstance(contenido_archivo, bytes):
        buffer = io.BytesIO(contenido_archivo)
    else:
        buffer = contenido_archivo

    if nombre_min.endswith(".xlsx") or nombre_min.endswith(".xls"):
        return pd.read_excel(buffer)
    
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    separators = [",", ";", "\t"]
    
    for enc in encodings:
        for sep in separators:
            try:
                buffer.seek(0)
                df = pd.read_csv(buffer, encoding=enc, sep=sep, engine="c", low_memory=False)
                if len(df.columns) > 1:
                    return df
            except Exception:
                continue

    for enc in encodings:
        try:
            buffer.seek(0)
            return pd.read_csv(buffer, encoding=enc, sep=None, engine="python")
        except Exception:
            continue

    buffer.seek(0)
    return pd.read_csv(buffer, encoding="utf-8", errors="ignore")


def normalizar_datos_encuesta(df: pd.DataFrame, plataforma_forzada: str = None) -> list[dict]:
    """
    Transforma el DataFrame crudo en una lista de encuestas y respuestas normalizadas para Campus Córdoba,
    mapeando automáticamente las encuestas de 5 preguntas a las 9 preguntas canónicas oficiales.
    """
    if df.empty:
        return []

    formato = detectar_formato_encuesta(df)
    plataforma = "campus_cordoba"

    col_resp = _buscar_columna(df, ["Respuesta", "id_respuesta", "response_id", "ID"])
    if not col_resp:
        df["_temp_id"] = range(1, len(df) + 1)
        col_resp = "_temp_id"

    col_fecha = _buscar_columna(df, ["Enviado el:", "Enviado el", "Fecha", "Fecha de envío", "submitted_at"])
    col_curso = _buscar_columna(df, ["Curso", "Nombre del curso", "course_name", "course"])
    col_inst = _buscar_columna(df, ["Institución", "Institucion", "institution"])
    col_depto = _buscar_columna(df, ["Departamento", "department"])

    encuestas_normalizadas = []
    filas_dict = df.to_dict(orient="records")

    if formato == "5_preguntas":
        cols_preguntas = {}
        for nro_local, alias in MAPA_PREGUNTAS_5P.items():
            encontrada = _buscar_columna(df, alias)
            if encontrada:
                cols_preguntas[nro_local] = encontrada

        for fila in filas_dict:
            val_resp = fila.get(col_resp)
            if pd.isna(val_resp):
                continue
            try:
                id_origen = int(val_resp)
            except (ValueError, TypeError):
                continue

            raw_curso = fila.get(col_curso) if col_curso else None
            nombre_curso = str(raw_curso).strip() if raw_curso and pd.notna(raw_curso) else "Curso General"

            raw_inst = fila.get(col_inst) if col_inst else None
            institucion = str(raw_inst).strip() if raw_inst and pd.notna(raw_inst) else None

            raw_depto = fila.get(col_depto) if col_depto else None
            departamento = str(raw_depto).strip() if raw_depto and pd.notna(raw_depto) else None

            raw_fecha = fila.get(col_fecha) if col_fecha else None
            if raw_fecha and pd.notna(raw_fecha):
                try:
                    fecha_envio = pd.to_datetime(str(raw_fecha).strip(), dayfirst=True)
                except Exception:
                    fecha_envio = pd.Timestamp.now()
            else:
                fecha_envio = pd.Timestamp.now()

            respuestas = []
            # Mapear 5P a la canónica de 9P:
            # 5P Q1 -> Q2 (Utilidad)
            # 5P Q2 -> Q4 (Tutor)
            # 5P Q3 -> Q3 (Material)
            # 5P Q4 -> Q5 (Administrativa)
            # 5P Q5 -> Q9 (Observaciones)
            for nro_5p in range(1, 6):
                col = cols_preguntas.get(nro_5p)
                val_crudo = fila.get(col) if col else None
                nro_canonica = MAPEO_EQUIVALENCIA_5P_A_CANONICA[nro_5p]

                if nro_5p <= 4:
                    num_val = _parsear_valor_escala(val_crudo)
                    respuestas.append({
                        "nro_pregunta": nro_canonica,
                        "valor_numerico": num_val,
                        "valor_texto": None,
                    })
                else:
                    txt = str(val_crudo).strip() if val_crudo is not None and pd.notna(val_crudo) else ""
                    respuestas.append({
                        "nro_pregunta": nro_canonica,  # Q9
                        "valor_numerico": None,
                        "valor_texto": txt if txt else None,
                        "es_ruido": es_comentario_ruido(txt),
                    })

            encuestas_normalizadas.append({
                "plataforma": plataforma,
                "id_respuesta_origen": id_origen,
                "nombre_curso": nombre_curso,
                "institucion": institucion,
                "departamento": departamento,
                "fecha_envio": fecha_envio.to_pydatetime(),
                "periodo_anio": int(fecha_envio.year),
                "periodo_mes": int(fecha_envio.month),
                "periodo_semana": int(fecha_envio.isocalendar().week),
                "respuestas": respuestas,
            })

    else:
        # Formato de 9 Preguntas (Desde Abril 2026)
        cols_preguntas = {}
        for nro_p, alias in MAPA_PREGUNTAS_9P.items():
            encontrada = _buscar_columna(df, alias)
            if encontrada:
                cols_preguntas[nro_p] = encontrada

        for fila in filas_dict:
            val_resp = fila.get(col_resp)
            if pd.isna(val_resp):
                continue
            try:
                id_origen = int(val_resp)
            except (ValueError, TypeError):
                continue

            raw_curso = fila.get(col_curso) if col_curso else None
            nombre_curso = str(raw_curso).strip() if raw_curso and pd.notna(raw_curso) else "Curso General"

            raw_inst = fila.get(col_inst) if col_inst else None
            institucion = str(raw_inst).strip() if raw_inst and pd.notna(raw_inst) else None

            raw_depto = fila.get(col_depto) if col_depto else None
            departamento = str(raw_depto).strip() if raw_depto and pd.notna(raw_depto) else None

            raw_fecha = fila.get(col_fecha) if col_fecha else None
            if raw_fecha and pd.notna(raw_fecha):
                try:
                    fecha_envio = pd.to_datetime(str(raw_fecha).strip(), dayfirst=True)
                except Exception:
                    fecha_envio = pd.Timestamp.now()
            else:
                fecha_envio = pd.Timestamp.now()

            respuestas = []
            for nro_p in range(1, 10):
                col = cols_preguntas.get(nro_p)
                val_crudo = fila.get(col) if col else None

                if nro_p <= 8:
                    num_val = _parsear_valor_escala(val_crudo)
                    respuestas.append({
                        "nro_pregunta": nro_p,
                        "valor_numerico": num_val,
                        "valor_texto": None,
                    })
                else:
                    txt = str(val_crudo).strip() if val_crudo is not None and pd.notna(val_crudo) else ""
                    respuestas.append({
                        "nro_pregunta": nro_p,
                        "valor_numerico": None,
                        "valor_texto": txt if txt else None,
                        "es_ruido": es_comentario_ruido(txt),
                    })

            encuestas_normalizadas.append({
                "plataforma": plataforma,
                "id_respuesta_origen": id_origen,
                "nombre_curso": nombre_curso,
                "institucion": institucion,
                "departamento": departamento,
                "fecha_envio": fecha_envio.to_pydatetime(),
                "periodo_anio": int(fecha_envio.year),
                "periodo_mes": int(fecha_envio.month),
                "periodo_semana": int(fecha_envio.isocalendar().week),
                "respuestas": respuestas,
            })

    return encuestas_normalizadas
