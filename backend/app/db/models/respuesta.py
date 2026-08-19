# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from app.db.base import Base


class Respuesta(Base):
    """
    Entidad Respuesta según el diagrama ERD:
    (idRespuesta, idEncuesta FK, idPregunta FK, valorNumerico, valorTexto, campos IA).
    """
    __tablename__ = "respuestas"

    id = Column("id_respuesta", Integer, primary_key=True, index=True)

    id_encuesta = Column("id_encuesta", Integer, ForeignKey("encuestas.id_encuesta"), nullable=False, index=True)
    encuesta = relationship("Encuesta", back_populates="respuestas")

    id_pregunta = Column("id_pregunta", Integer, ForeignKey("preguntas.id_pregunta"), nullable=False, index=True)
    pregunta = relationship("Pregunta", back_populates="respuestas")

    # Valores de la respuesta según su tipo
    valor_numerico = Column("valor_numerico", Integer, nullable=True, index=True)  # 1 a 10
    valor_texto = Column("valor_texto", Text, nullable=True)                        # Pregunta 9

    # Metadatos del análisis de IA sobre valor_texto
    ai_tema = Column("ai_tema", String(100), nullable=True, index=True)
    ai_sentimiento = Column("ai_sentimiento", String(50), nullable=True, index=True)  # "positivo" | "negativo" | "neutro"
    ai_procesado_en = Column("ai_procesado_en", DateTime, nullable=True)
