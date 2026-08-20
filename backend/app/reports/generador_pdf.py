import os
from datetime import datetime
# pyrefly: ignore [missing-import]
from jinja2 import Environment, FileSystemLoader
# pyrefly: ignore [missing-import]
import weasyprint

DIR_PLANTILLAS = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(DIR_PLANTILLAS), autoescape=True)


def generar_pdf_encuestas(
    kpis: dict,
    preguntas: list[dict],
    insights_ia: dict,
    comentarios: list[dict],
    nombre_curso: str = "Todos los Cursos",
    fecha_inicio: str = None,
    fecha_fin: str = None,
) -> bytes:
    """
    Renderiza el reporte institucional en HTML usando Jinja2 y lo compila
    a un archivo PDF binario mediante WeasyPrint.
    """
    plantilla = env.get_template("reporte_encuesta.html")

    fechas_filtro = None
    if fecha_inicio and fecha_fin:
        fechas_filtro = f"Del {fecha_inicio} al {fecha_fin}"
    elif fecha_inicio:
        fechas_filtro = f"Desde {fecha_inicio}"
    elif fecha_fin:
        fechas_filtro = f"Hasta {fecha_fin}"

    contexto = {
        "course_name": nombre_curso,
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "filter_dates": fechas_filtro,
        "kpis": kpis,
        "questions": preguntas,
        "ai_insights": insights_ia,
        "comments": comentarios,
    }

    contenido_html = plantilla.render(contexto)
    bytes_pdf = weasyprint.HTML(string=contenido_html).write_pdf()
    return bytes_pdf


# Alias de compatibilidad
build_survey_pdf = generar_pdf_encuestas
