# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from app.db.base import Base


class Encuesta(Base):
    """
    Entidad Encuesta:
    (idEncuesta, plataforma, idCurso FK, fechaEnvio, idRespuestaOrigen, periodos).
    """
    __tablename__ = "encuestas"

    id = Column("id_encuesta", Integer, primary_key=True, index=True)
    plataforma = Column("plataforma", String(50), nullable=False, default="campus_cordoba", index=True)
    id_respuesta_origen = Column("id_respuesta_origen", Integer, unique=True, nullable=False, index=True)

    id_curso = Column("id_curso", Integer, ForeignKey("cursos.id_curso"), nullable=False, index=True)
    curso = relationship("Curso", back_populates="encuestas")

    fecha_envio = Column("fecha_envio", DateTime, nullable=False, index=True)

    # Períodos calculados para consultas analíticas rápidas
    periodo_anio = Column("periodo_anio", Integer, nullable=False, index=True)
    periodo_mes = Column("periodo_mes", Integer, nullable=False, index=True)
    periodo_semana = Column("periodo_semana", Integer, nullable=False, index=True)

    respuestas = relationship("Respuesta", back_populates="encuesta", cascade="all, delete-orphan")
