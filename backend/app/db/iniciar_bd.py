import logging
from sqlalchemy.orm import Session
from app.db.base import Base, engine, SessionLocal
from app.db.models.pregunta import Pregunta
import app.db.models  # registra Curso, Encuesta, Pregunta, Respuesta en Base

logger = logging.getLogger(__name__)

PREGUNTAS_OFICIALES = [
    {
        "nro": 1,
        "tipo": "numerica",
        "etiqueta": "Aula Virtual",
        "descripcion": "¿El aula virtual fue fácil de usar y de acceder?",
    },
    {
        "nro": 2,
        "tipo": "numerica",
        "etiqueta": "Utilidad de Contenidos",
        "descripcion": "¿Los contenidos de la capacitación le resultan útiles para mejorar su desempeño laboral y/o personal?",
    },
    {
        "nro": 3,
        "tipo": "numerica",
        "etiqueta": "Material Didáctico",
        "descripcion": "¿El material y los recursos didácticos de la capacitación fueron claros y facilitaron la comprensión de los contenidos?",
    },
    {
        "nro": 4,
        "tipo": "numerica",
        "etiqueta": "Desempeño Tutorial",
        "descripcion": "¿El/la tutor/a mantuvo una comunicación adecuada con los participantes durante la capacitación?",
    },
    {
        "nro": 5,
        "tipo": "numerica",
        "etiqueta": "Atención Administrativa",
        "descripcion": "¿La atención del área administrativa del Campus Córdoba fue adecuada y respondió a sus consultas en tiempo y forma?",
    },
    {
        "nro": 6,
        "tipo": "numerica",
        "etiqueta": "Satisfacción General",
        "descripcion": "¿Cuál es su nivel de satisfacción general con la capacitación realizada?",
    },
    {
        "nro": 7,
        "tipo": "numerica",
        "etiqueta": "Expectativas",
        "descripcion": "¿La capacitación cumplió con sus expectativas iniciales?",
    },
    {
        "nro": 8,
        "tipo": "numerica",
        "etiqueta": "Recomendación (NPS)",
        "descripcion": "¿Qué tan probable es que recomiende Campus Córdoba a otras personas?",
    },
    {
        "nro": 9,
        "tipo": "texto",
        "etiqueta": "Observaciones y Sugerencias",
        "descripcion": "Observaciones o sugerencias para mejorar la capacitación",
    },
]


def iniciar_base_datos():
    """Crea las tablas en la base de datos y siembra las 9 preguntas oficiales si no existen."""
    logger.info("Creando tablas en MySQL...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        for p_data in PREGUNTAS_OFICIALES:
            existente = db.query(Pregunta).filter(Pregunta.nro_pregunta == p_data["nro"]).first()
            if not existente:
                p = Pregunta(
                    nro_pregunta=p_data["nro"],
                    tipo=p_data["tipo"],
                    etiqueta_corta=p_data["etiqueta"],
                    descripcion=p_data["descripcion"],
                )
                db.add(p)
            else:
                existente.etiqueta_corta = p_data["etiqueta"]
                existente.descripcion = p_data["descripcion"]
                existente.tipo = p_data["tipo"]
        db.commit()
        logger.info("Catálogo oficial de preguntas inicializado exitosamente.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error al inicializar preguntas: {e}")
        raise
    finally:
        db.close()


init_db = iniciar_base_datos
