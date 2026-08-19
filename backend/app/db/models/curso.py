# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from app.db.base import Base


class Curso(Base):
    """
    Entidad Curso según el diagrama ERD:
    (idCurso, codCurso, nombreCurso, institucion, departamento).
    """
    __tablename__ = "cursos"

    id = Column("id_curso", Integer, primary_key=True, index=True)
    codigo = Column("cod_curso", String(100), nullable=True, index=True)
    nombre = Column("nombre_curso", String(255), unique=True, nullable=False, index=True)
    institucion = Column("institucion", String(255), nullable=True)
    departamento = Column("departamento", String(255), nullable=True)

    encuestas = relationship("Encuesta", back_populates="curso", cascade="all, delete-orphan")
