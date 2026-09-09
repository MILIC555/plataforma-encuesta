import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.base import Base, engine, SessionLocal
from app.db.models.pregunta import Pregunta
import app.db.models  # registra Curso, Encuesta, Pregunta, Respuesta en Base

logger = logging.getLogger(__name__)

CATALOGO_PREGUNTAS = [
    {
        "plataforma": "campus_cordoba",
        "nro": 1,
        "tipo": "numerica",
        "etiqueta": "Aula Virtual",
        "descripcion": "¿El aula virtual fue fácil de usar y de acceder?",
    },
    {
        "plataforma": "campus_cordoba",
        "nro": 2,
        "tipo": "numerica",
        "etiqueta": "Utilidad de Contenidos",
        "descripcion": "¿Los contenidos de la capacitación le resultan útiles para mejorar su desempeño laboral y/o personal?",
    },
    {
        "plataforma": "campus_cordoba",
        "nro": 3,
        "tipo": "numerica",
        "etiqueta": "Material Didáctico",
        "descripcion": "¿El material y los recursos didácticos de la capacitación fueron claros y facilitaron la comprensión de los contenidos?",
    },
    {
        "plataforma": "campus_cordoba",
        "nro": 4,
        "tipo": "numerica",
        "etiqueta": "Desempeño Tutorial",
        "descripcion": "¿El/la tutor/a mantuvo una comunicación adecuada con los participantes durante la capacitación?",
    },
    {
        "plataforma": "campus_cordoba",
        "nro": 5,
        "tipo": "numerica",
        "etiqueta": "Atención Administrativa",
        "descripcion": "¿La atención del área administrativa del Campus Córdoba fue adecuada y respondió a sus consultas en tiempo y forma?",
    },
    {
        "plataforma": "campus_cordoba",
        "nro": 6,
        "tipo": "numerica",
        "etiqueta": "Satisfacción General",
        "descripcion": "¿Cuál es su nivel de satisfacción general con la capacitación realizada?",
    },
    {
        "plataforma": "campus_cordoba",
        "nro": 7,
        "tipo": "numerica",
        "etiqueta": "Expectativas",
        "descripcion": "¿La capacitación cumplió con sus expectativas iniciales?",
    },
    {
        "plataforma": "campus_cordoba",
        "nro": 8,
        "tipo": "numerica",
        "etiqueta": "Recomendación (NPS)",
        "descripcion": "¿Qué tan probable es que recomiende Campus Córdoba a otras personas?",
    },
    {
        "plataforma": "campus_cordoba",
        "nro": 9,
        "tipo": "texto",
        "etiqueta": "Observaciones y Sugerencias",
        "descripcion": "Observaciones o sugerencias para mejorar la capacitación",
    },
]


def iniciar_base_datos():
    """Crea o actualiza las tablas en la base de datos y siembra los catálogos oficiales."""
    logger.info("Verificando y sincronizando tablas en MySQL...")
    Base.metadata.create_all(bind=engine)

    # Migración suave de columnas si faltan en tablas existentes
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE preguntas ADD COLUMN plataforma VARCHAR(50) NOT NULL DEFAULT 'campus_cordoba'"))
        except Exception:
            pass  # ya existe
        try:
            conn.execute(text("ALTER TABLE encuestas ADD COLUMN plataforma VARCHAR(50) NOT NULL DEFAULT 'campus_cordoba'"))
        except Exception:
            pass  # ya existe

    db: Session = SessionLocal()
    try:
        # Asegurar que las preguntas obsoletas de otras plataformas se eliminen
        conn = db.connection()
        db.execute(text("DELETE FROM preguntas WHERE plataforma != 'campus_cordoba'"))
        db.execute(text("UPDATE encuestas SET plataforma = 'campus_cordoba' WHERE plataforma != 'campus_cordoba'"))
        
        for p_data in CATALOGO_PREGUNTAS:
            existente = (
                db.query(Pregunta)
                .filter(
                    Pregunta.plataforma == p_data["plataforma"],
                    Pregunta.nro_pregunta == p_data["nro"],
                )
                .first()
            )
            if not existente:
                p = Pregunta(
                    plataforma=p_data["plataforma"],
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
        logger.info("Catálogo oficial de preguntas (Campus Córdoba) listo.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error al inicializar catálogo de preguntas: {e}")
        raise
    finally:
        db.close()


init_db = iniciar_base_datos
