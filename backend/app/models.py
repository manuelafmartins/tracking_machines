from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .database import Base
import enum

class TipoMaquinaEnum(str, enum.Enum):
    camiao = "camiao"
    fixa = "fixa"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"))

    empresa = relationship("Empresa")

class Empresa(Base):
    __tablename__ = "empresas"
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)
    maquinas = relationship("Maquina", back_populates="empresa")

class Maquina(Base):
    __tablename__ = "maquinas"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    tipo = Column(Enum(TipoMaquinaEnum), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    empresa = relationship("Empresa", back_populates="maquinas")
    manutencoes = relationship("Manutencao", back_populates="maquina")

class Manutencao(Base):
    __tablename__ = "manutencoes"
    id = Column(Integer, primary_key=True)
    maquina_id = Column(Integer, ForeignKey("maquinas.id"))
    tipo = Column(String, nullable=False)
    data_prevista = Column(Date, nullable=False)
    maquina = relationship("Maquina", back_populates="manutencoes")
