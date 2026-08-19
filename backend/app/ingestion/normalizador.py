import re
import io
import pandas as pd
from typing import BinaryIO, Union

MAPA_PREGUNTAS = {
    1: ["Q01_1", "Q01", "Q1_1", "Q1", "p1", "pregunta_1"],
    2: ["Q02_2", "Q02", "Q2_2", "Q2", "p2", "pregunta_2"],
    3: ["Q03_3", "Q03", "Q3_3", "Q3", "p3", "pregunta_3"],
    4: ["Q04_4", "Q04", "Q4_4", "Q4", "p4", "pregunta_4"],
    5: ["Q05_5", "Q05", "Q5_5", "Q5", "p5", "pregunta_5"],
    6: ["Q06_6", "Q06", "Q6_6", "Q6", "p6", "pregunta_6"],
    7: ["Q07_7", "Q07", "Q7_7", "Q7", "p7", "pregunta_7"],
    8: ["Q08_8", "Q08", "Q8_8", "Q8", "p8", "pregunta_8"],
    9: ["Q09_9", "Q09", "Q9_9", "Q9", "p9", "pregunta_9", "observaciones", "sugerencias", "comentario"],
}

COMENTARIOS_RUIDO = {
    "", "-", "--", "---", ".", "..", "...", "....", "/", "//", "*", "(y)", "ok", "ok.",
    "nada", "ninguna", "ninguno", "ningun", "ningún", "no", "no tengo", "no hay",
    "sin comentarios", "sin observaciones", "sin sugerencias", "ninguna sugerencia",
    "no tengo ninguna sugerencia", "no tengo sugerencias", "nada para agregar",
    "nada que agregar", "nada que mejorar", "nada por el momento", "ninguna por el momento",
    "todo bien", "todo ok", "todo correcto", "excelente", "muy bueno", "gracias"
}


def _parsear_valor_escala(raw: any) -> int | None:
    """
    Convierte '10 : 10' -> 10, '8 : 8' -> 8, o 10 -> 10.
    Si está vacío o no es un número válido de 1 a 10, devuelve None.
    """
    if pd.isna(raw):
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


def leer_archivo_a_dataframe(contenido_archivo: Union[bytes, BinaryIO], nombre_archivo: str) -> pd.DataFrame:
    """Lee un archivo CSV o Excel con tolerancia a diferentes encodings y delimitadores."""
    if isinstance(contenido_archivo, bytes):
        buffer = io.BytesIO(contenido_archivo)
    else:
        buffer = contenido_archivo

    nombre_min = nombre_archivo.lower()
    if nombre_min.endswith(".xlsx") or nombre_min.endswith(".xls"):
        return pd.read_excel(buffer)
    
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            buffer.seek(0)
            return pd.read_csv(buffer, encoding=enc, sep=None, engine="python")
        except Exception:
            continue

    buffer.seek(0)
    return pd.read_csv(buffer, encoding="utf-8", errors="ignore")


def normalizar_datos_encuesta(df: pd.DataFrame) -> list[dict]:
    """
    Transforma el DataFrame crudo en una lista de registros normalizados listos
    para ser importados a la base de datos según el modelo relacional.
    """
    col_resp = _buscar_columna(df, ["Respuesta", "id_respuesta", "response_id", "ID"])
    if not col_resp:
        df["_temp_id"] = range(1, len(df) + 1)
        col_resp = "_temp_id"

    col_fecha = _buscar_columna(df, ["Enviado el:", "Enviado el", "Fecha", "Fecha de envío", "submitted_at"])
    col_curso = _buscar_columna(df, ["Curso", "Nombre del curso", "course_name", "course"])
    col_inst = _buscar_columna(df, ["Institución", "Institucion", "institution"])
    col_depto = _buscar_columna(df, ["Departamento", "department"])

    cols_preguntas = {}
    for nro_p, alias in MAPA_PREGUNTAS.items():
        encontrada = _buscar_columna(df, alias)
        if encontrada:
            cols_preguntas[nro_p] = encontrada

    encuestas_normalizadas = []

    for _, fila in df.iterrows():
        try:
            id_origen = int(fila[col_resp])
        except (ValueError, TypeError):
            continue

        nombre_curso = str(fila[col_curso]).strip() if col_curso and pd.notna(fila[col_curso]) else "Curso General"
        institucion = str(fila[col_inst]).strip() if col_inst and pd.notna(fila[col_inst]) else None
        departamento = str(fila[col_depto]).strip() if col_depto and pd.notna(fila[col_depto]) else None

        if col_fecha and pd.notna(fila[col_fecha]):
            raw_fecha = str(fila[col_fecha]).strip()
            try:
                fecha_envio = pd.to_datetime(raw_fecha, dayfirst=True)
            except Exception:
                fecha_envio = pd.Timestamp.now()
        else:
            fecha_envio = pd.Timestamp.now()

        respuestas = []
        for nro_p in range(1, 10):
            col = cols_preguntas.get(nro_p)
            val_crudo = fila[col] if col and col in fila and pd.notna(fila[col]) else None

            if nro_p <= 8:
                num_val = _parsear_valor_escala(val_crudo)
                respuestas.append({
                    "nro_pregunta": nro_p,
                    "valor_numerico": num_val,
                    "valor_texto": None,
                })
            else:
                txt = str(val_crudo).strip() if val_crudo is not None else ""
                respuestas.append({
                    "nro_pregunta": nro_p,
                    "valor_numerico": None,
                    "valor_texto": txt if txt else None,
                    "es_ruido": es_comentario_ruido(txt),
                })

        encuestas_normalizadas.append({
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
