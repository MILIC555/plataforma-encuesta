# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Text
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from app.db.base import Base


class Pregunta(Base):
    """
    Entidad Pregunta según el diagrama ERD:
    (idPregunta, nroPregunta, tipo, descripcion).
    """
    __tablename__ = "preguntas"

    id = Column("id_pregunta", Integer, primary_key=True, index=True)
    nro_pregunta = Column("nro_pregunta", Integer, unique=True, nullable=False, index=True)
    tipo = Column("tipo", String(50), nullable=False)  # "numerica" | "texto"
    descripcion = Column("descripcion", Text, nullable=False)
    etiqueta_corta = Column("etiqueta_corta", String(100), nullable=True)

    respuestas = relationship("Respuesta", back_populates="pregunta", cascade="all, delete-orphan")
