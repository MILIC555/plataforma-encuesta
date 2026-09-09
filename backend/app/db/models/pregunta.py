# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from app.db.base import Base


class Pregunta(Base):
    """
    Entidad Pregunta:
    (idPregunta, plataforma, nroPregunta, tipo, descripcion, etiquetaCorta).
    """
    __tablename__ = "preguntas"

    id = Column("id_pregunta", Integer, primary_key=True, index=True)
    plataforma = Column("plataforma", String(50), nullable=False, default="campus_cordoba", index=True)
    nro_pregunta = Column("nro_pregunta", Integer, nullable=False, index=True)
    tipo = Column("tipo", String(50), nullable=False)  # "numerica" | "texto" | "mixta"
    descripcion = Column("descripcion", Text, nullable=False)
    etiqueta_corta = Column("etiqueta_corta", String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("plataforma", "nro_pregunta", name="uq_pregunta_plataforma_nro"),
    )

    respuestas = relationship("Respuesta", back_populates="pregunta", cascade="all, delete-orphan")
