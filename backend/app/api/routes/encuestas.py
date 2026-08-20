# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.db.models.pregunta import Pregunta
from app.db.models.curso import Curso
from app.db.models.encuesta import Encuesta
from app.db.models.respuesta import Respuesta
from app.ingestion.importador import importar_archivos_masivos

router = APIRouter(prefix="/surveys", tags=["Encuestas e Ingesta"])


@router.post("/upload")
async def subir_archivos_encuestas(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Permite subir uno o múltiples archivos de encuestas (CSV o Excel) de forma masiva o individual.
    Ignora automáticamente registros y archivos duplicados.
    """
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No se enviaron archivos para procesar.",
        )

    extensiones_validas = (".csv", ".xlsx", ".xls")
    lista_para_procesar = []

    for item in files:
        nombre = item.filename or ""
        if not any(nombre.lower().endswith(ext) for ext in extensiones_validas):
            continue
        contenido = await item.read()
        lista_para_procesar.append((contenido, nombre))

    if not lista_para_procesar:
        raise HTTPException(
            status_code=400,
            detail="Ninguno de los archivos enviados tiene un formato válido (.csv, .xlsx, .xls).",
        )

    try:
        resultado = importar_archivos_masivos(db, lista_para_procesar)
        return resultado
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error durante el procesamiento masivo: {str(e)}",
        )


@router.get("/questions")
def listar_preguntas(db: Session = Depends(get_db)):
    """Devuelve el catálogo de preguntas oficiales de Campus Córdoba."""
    preguntas = db.query(Pregunta).order_by(Pregunta.nro_pregunta).all()
    return [
        {
            "id": p.id,
            "number": p.nro_pregunta,
            "type": p.tipo,
            "label": p.etiqueta_corta,
            "description": p.descripcion,
        }
        for p in preguntas
    ]


@router.get("/courses")
def listar_cursos(db: Session = Depends(get_db)):
    """Devuelve todos los cursos registrados con su conteo de encuestas."""
    cursos = db.query(Curso).order_by(Curso.nombre).all()
    resultado = []
    for c in cursos:
        conteo = db.query(Encuesta).filter(Encuesta.id_curso == c.id).count()
        resultado.append({
            "id": c.id,
            "name": c.nombre,
            "code": c.codigo,
            "institution": c.institucion,
            "department": c.departamento,
            "total_surveys": conteo,
        })
    return resultado


@router.delete("/courses/{course_id}")
def eliminar_curso_y_encuestas(course_id: int, db: Session = Depends(get_db)):
    """
    Elimina un curso específico y todas sus encuestas y respuestas asociadas en cascada.
    """
    curso = db.query(Curso).filter(Curso.id == course_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="El curso no fue encontrado.")

    nombre_curso = curso.nombre
    total_encuestas = db.query(Encuesta).filter(Encuesta.id_curso == course_id).count()

    db.delete(curso)
    db.commit()

    return {
        "success": True,
        "message": f"Curso '{nombre_curso}' y sus {total_encuestas} encuestas fueron eliminados exitosamente.",
        "course_id": course_id,
        "deleted_surveys": total_encuestas,
    }


@router.delete("/clear-all")
def vaciar_todas_las_encuestas(db: Session = Depends(get_db)):
    """
    Elimina todas las encuestas, respuestas y cursos cargados, preservando el catálogo de preguntas.
    """
    total_respuestas = db.query(Respuesta).count()
    total_encuestas = db.query(Encuesta).count()
    total_cursos = db.query(Curso).count()

    db.query(Respuesta).delete()
    db.query(Encuesta).delete()
    db.query(Curso).delete()
    db.commit()

    return {
        "success": True,
        "message": f"Se vació la base de datos: {total_encuestas} encuestas y {total_cursos} cursos eliminados.",
        "deleted_courses": total_cursos,
        "deleted_surveys": total_encuestas,
        "deleted_responses": total_respuestas,
    }
