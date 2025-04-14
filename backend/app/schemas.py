# backend/schemas.py
from pydantic import BaseModel
from datetime import date
from enum import Enum

# O enum de tipo da máquina, repetido aqui para Pydantic
class TipoMaquinaEnum(str, Enum):
    CAMIAO = "camiao"
    FIXA = "fixa"

# Empresa
class EmpresaBase(BaseModel):
    nome: str

class EmpresaCreate(EmpresaBase):
    pass

class Empresa(EmpresaBase):
    id: int

    class Config:
        orm_mode = True  # permite usar objetos do SQLAlchemy

# Maquina
class MaquinaBase(BaseModel):
    nome: str
    tipo: TipoMaquinaEnum
    empresa_id: int

class MaquinaCreate(MaquinaBase):
    pass

class Maquina(MaquinaBase):
    id: int

    class Config:
        orm_mode = True

# Manutencao
class ManutencaoBase(BaseModel):
    maquina_id: int
    tipo: str
    data_prevista: date

class ManutencaoCreate(ManutencaoBase):
    pass

class Manutencao(ManutencaoBase):
    id: int

    class Config:
        orm_mode = True
