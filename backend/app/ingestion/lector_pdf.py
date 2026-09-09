import io
import re
import logging
import pandas as pd
from typing import BinaryIO, Union

logger = logging.getLogger(__name__)


def limpiar_nombre_curso_de_archivo(nombre_archivo: str) -> str:
    """
    Deduce y limpia el nombre del curso a partir del nombre del archivo PDF.
    Ejemplos:
    - 'Encuesta_de_satisfaccion_Habitos_saludables.pdf' -> 'Hábitos saludables'
    - 'Informe_cuestionario_Gestion_de_Expedientes.pdf' -> 'Gestión de Expedientes'
    - '12345_Atencion_al_Ciudadano_2026.pdf' -> 'Atención al Ciudadano'
    """
    if not nombre_archivo:
        return "Curso General"

    nombre = nombre_archivo
    # Quitar extensión
    if "." in nombre:
        nombre = nombre.rsplit(".", 1)[0]

    # Reemplazar guiones bajos y múltiples espacios
    nombre = nombre.replace("_", " ").replace("-", " ")

    # Quitar prefijos comunes
    patrones_prefijos = [
        r"^encuesta\s+(de\s+)?(satisfaccion\s+)?(del\s+curso\s+)?",
        r"^informe\s+(de\s+la\s+encuesta\s+)?(del\s+cuestionario\s+)?",
        r"^reporte\s+(de\s+)?(encuestas\s+)?",
        r"^cuestionario\s+",
        r"^\d{4,}\s+",
    ]
    for pat in patrones_prefijos:
        nombre = re.sub(pat, "", nombre, flags=re.IGNORECASE).strip()

    # Quitar sufijos de fechas o IDs
    nombre = re.sub(r"\s+\d{1,2}\s+(de\s+)?[a-z]+\s+(de\s+)?\d{4}$", "", nombre, flags=re.IGNORECASE)
    nombre = re.sub(r"\s+\d{4,}$", "", nombre).strip()

    # Colapsar espacios
    nombre = re.sub(r"\s+", " ", nombre).strip()

    return nombre if len(nombre) >= 3 else (nombre_archivo.rsplit(".", 1)[0] if "." in nombre_archivo else nombre_archivo)


def _extraer_tabla_plana_pdf(pdf) -> pd.DataFrame:
    """
    Extrae datos de PDFs con formato de tabla apaisada (como el PDF de 153 páginas de Moodle).
    Retorna un DataFrame con columnas estándar.
    """
    todas_las_filas = []
    encabezado_detectado = None

    for page in pdf.pages:
        tablas = page.extract_tables()
        if not tablas:
            continue

        for tabla in tablas:
            for fila in tabla:
                if not fila or not any(fila):
                    continue

                fila_str = [str(celda).strip() if celda is not None else "" for celda in fila]

                # Detectar encabezado
                fila_unida = " ".join(fila_str).lower()
                if "respuesta" in fila_unida and ("q01" in fila_unida or "q1" in fila_unida or "enviado" in fila_unida):
                    if not encabezado_detectado:
                        encabezado_detectado = fila_str
                    continue

                # Si es una fila de datos (primer elemento suele ser un número de ID de respuesta)
                primer_elem = fila_str[0]
                if primer_elem and (primer_elem.isdigit() or len(fila_str) >= 8):
                    todas_las_filas.append(fila_str)

    if not todas_las_filas:
        return pd.DataFrame()

    if not encabezado_detectado:
        # Encabezado por defecto según estructura de Moodle
        columnas = [
            "Respuesta", "Enviado el:", "Institución", "Departamento", "Curso", "Grupo",
            "ID de usuario", "Nombre completo", "Nombre de usuario",
            "Q01_1", "Q02_2", "Q03_3", "Q04_4", "Q05_5"
        ]
        # Ajustar si faltan o sobran columnas
        num_cols = len(todas_las_filas[0])
        if len(columnas) < num_cols:
            columnas += [f"Col_{i}" for i in range(len(columnas) + 1, num_cols + 1)]
        else:
            columnas = columnas[:num_cols]
    else:
        # Limpiar saltos de línea en encabezados
        columnas = [re.sub(r"\s+", " ", c).strip() for c in encabezado_detectado]
        num_cols = len(todas_las_filas[0])
        if len(columnas) < num_cols:
            columnas += [f"Col_{i}" for i in range(len(columnas) + 1, num_cols + 1)]
        else:
            columnas = columnas[:num_cols]

    # Normalizar longitud de filas
    filas_normalizadas = []
    for f in todas_las_filas:
        if len(f) < len(columnas):
            f = f + [""] * (len(columnas) - len(f))
        elif len(f) > len(columnas):
            f = f[:len(columnas)]
        filas_normalizadas.append(f)

    return pd.DataFrame(filas_normalizadas, columns=columnas)


def _extraer_reporte_resumen_pdf(pdf, nombre_archivo: str) -> pd.DataFrame:
    """
    Extrae datos de PDFs tipo reporte resumido (formatos 1 y 3 de 9 o 20 páginas de Moodle Questionnaire).
    Reconstruye las respuestas individuales de Q1 a Q4 según la distribución de frecuencias
    y asocia cada comentario abierto de la Pregunta 5.
    """
    texto_completo = "\n".join(page.extract_text() or "" for page in pdf.pages)
    if not texto_completo:
        return pd.DataFrame()

    nombre_curso = limpiar_nombre_curso_de_archivo(nombre_archivo)

    # 1. Extraer comentarios de la Pregunta 5
    comentarios_q5 = []
    en_seccion_q5 = False

    for page in pdf.pages:
        txt = page.extract_text() or ""
        lineas = txt.split("\n")

        for linea in lineas:
            linea_limpia = linea.strip()
            if not linea_limpia:
                continue

            if "5 Observaciones:" in linea_limpia or "Observaciones: (Sugerencias" in linea_limpia:
                en_seccion_q5 = True
                continue

            if en_seccion_q5:
                # Ignorar encabezados y números de página
                if re.match(r"^Página\s+\d+\s*/\s*\d+", linea_limpia, re.IGNORECASE):
                    continue
                if re.match(r"^Total de respuestas", linea_limpia, re.IGNORECASE):
                    continue
                if linea_limpia in ["Encuestado", "Respuesta", "Fecha", "Encuestado Respuesta", "Nombre/Apellido(s) Fecha Respuesta"]:
                    continue
                if re.match(r"^\d{1,2}\s+de\s+[a-z]+\s+de\s+\d{4}", linea_limpia, re.IGNORECASE):
                    # Línea de fecha del reporte web (Formato 3)
                    continue

                if len(linea_limpia) > 1 and not linea_limpia.isdigit():
                    comentarios_q5.append(linea_limpia)

    # 2. Extraer frecuencias de preguntas 1 a 4
    # Patrones para Q1, Q2, Q3, Q4
    distribuciones = {1: [], 2: [], 3: [], 4: []}

    # Regex para extraer filas de distribución (ej: '10 73% 74' o '10 : 10 18% 18')
    for num_q in range(1, 5):
        # Buscar bloque de pregunta
        patron_bloque = rf"{num_q}\s+([^\n]+)(.*?)(?={num_q + 1}\s+|Total de respuestas|\Z)"
        match = re.search(patron_bloque, texto_completo, re.DOTALL | re.IGNORECASE)
        if match:
            bloque = match.group(2)
            # Extraer líneas numéricas
            for linea in bloque.split("\n"):
                linea = linea.strip()
                # Detectar opción de texto especial en Q2: 'No me comuniqué con el tutor...'
                if num_q == 2 and ("no me comuniqu" in linea.lower() or "sin comunicaci" in linea.lower()):
                    cnt_match = re.search(r"(\d+)\s*$", linea)
                    cant = int(cnt_match.group(1)) if cnt_match else 1
                    distribuciones[2].extend(["No me comuniqué con el tutor o tutora"] * cant)
                    continue

                # Detectar opción de texto especial en Q4: 'No utilizado'
                if num_q == 4 and "no utilizado" in linea.lower():
                    cnt_match = re.search(r"(\d+)\s*$", linea)
                    cant = int(cnt_match.group(1)) if cnt_match else 1
                    distribuciones[4].extend(["No utilizado"] * cant)
                    continue

                # Opciones numéricas 1 a 10: '10 73% 74' o '10 157' o '10 : 10 18'
                m_num = re.search(r"^(\d{1,2})\s+(?:\d+%\s+)?(\d+)", linea)
                if m_num:
                    val_calif = int(m_num.group(1))
                    cant = int(m_num.group(2))
                    if 1 <= val_calif <= 10:
                        distribuciones[num_q].extend([f"{val_calif} : {val_calif}"] * cant)

    total_encuestas = max(
        len(distribuciones[1]),
        len(distribuciones[2]),
        len(distribuciones[3]),
        len(distribuciones[4]),
        len(comentarios_q5),
        1
    )

    # Reconstruir filas de DataFrame
    filas = []
    for i in range(total_encuestas):
        q1_val = distribuciones[1][i] if i < len(distribuciones[1]) else "10 : 10"
        q2_val = distribuciones[2][i] if i < len(distribuciones[2]) else "10 : 10"
        q3_val = distribuciones[3][i] if i < len(distribuciones[3]) else "10 : 10"
        q4_val = distribuciones[4][i] if i < len(distribuciones[4]) else "10 : 10"
        q5_val = comentarios_q5[i] if i < len(comentarios_q5) else ""

        filas.append({
            "Respuesta": 900000 + i + 1,
            "Enviado el:": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Institución": "Subdirección de Capacitación y Formación",
            "Departamento": "Gobierno de Córdoba",
            "Curso": nombre_curso,
            "Grupo": "",
            "ID de usuario": f"Anónimo {i + 1}",
            "Nombre completo": f"Anónimo {i + 1}",
            "Nombre de usuario": "",
            "Q01_1": q1_val,
            "Q02_2": q2_val,
            "Q03_3": q3_val,
            "Q04_4": q4_val,
            "Q05_5": q5_val,
        })

    return pd.DataFrame(filas)


def leer_pdf_a_dataframe(contenido_archivo: Union[bytes, BinaryIO], nombre_archivo: str) -> pd.DataFrame:
    """
    Lee un archivo PDF en memoria y extrae automáticamente las encuestas en un DataFrame normalizado,
    soportando los 3 formatos de Campus Virtual Empleados.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber no está instalado.")
        return pd.DataFrame()

    if isinstance(contenido_archivo, bytes):
        buffer = io.BytesIO(contenido_archivo)
    else:
        buffer = contenido_archivo

    buffer.seek(0)
    with pdfplumber.open(buffer) as pdf:
        if not pdf.pages:
            return pd.DataFrame()

        primera_pag_texto = pdf.pages[0].extract_text() or ""
        
        # 1. Si es formato tabla apaisada (PDF 2)
        if "Respuest" in primera_pag_texto and ("Q01" in primera_pag_texto or "Q1" in primera_pag_texto or "Enviado" in primera_pag_texto):
            df = _extraer_tabla_plana_pdf(pdf)
            if not df.empty:
                return df

        # 2. Si es formato reporte estadístico / resumen (PDF 1 o PDF 3)
        return _extraer_reporte_resumen_pdf(pdf, nombre_archivo)
