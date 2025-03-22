from pydantic import BaseModel
from datetime import date
from enum import Enum

class TipoMaquinaEnum(str, Enum):
    camiao = "camiao"
    fixa = "fixa"

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class EmpresaCreate(BaseModel):
    nome: str

class Empresa(BaseModel):
    id: int
    nome: str
    class Config:
        orm_mode = True

class MaquinaCreate(BaseModel):
    nome: str
    tipo: TipoMaquinaEnum
    empresa_id: int

class ManutencaoCreate(BaseModel):
    maquina_id: int
    tipo: str
    data_prevista: date
