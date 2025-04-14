# backend/app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from .security import gerar_hash
from datetime import datetime, timedelta

# --- CRUD EMPRESA ---
def get_empresas(db: Session):
    return db.query(models.Empresa).all()

def create_empresa(db: Session, empresa: schemas.EmpresaCreate):
    db_empresa = models.Empresa(nome=empresa.nome)
    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa

# --- CRUD MÁQUINA ---
def get_maquinas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Maquina).offset(skip).limit(limit).all()

def create_maquina(db: Session, maquina: schemas.MaquinaCreate):
    db_maquina = models.Maquina(**maquina.dict())
    db.add(db_maquina)
    db.commit()
    db.refresh(db_maquina)
    return db_maquina

# --- CRUD MANUTENÇÃO ---
def get_manutencoes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Manutencao).offset(skip).limit(limit).all()

def create_manutencao(db: Session, manutencao: schemas.ManutencaoCreate):
    db_manutencao = models.Manutencao(**manutencao.dict())
    db.add(db_manutencao)
    db.commit()
    db.refresh(db_manutencao)
    return db_manutencao

def listar_manutencoes_pendentes(db: Session):
    hoje = datetime.now().date()
    # Buscar manutenções com data prevista dentro dos próximos 7 dias
    proxima_semana = hoje + timedelta(days=7)
    return db.query(models.Manutencao).filter(
        models.Manutencao.data_prevista.between(hoje, proxima_semana)
    ).all()

# --- CRUD USUÁRIO ---
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = gerar_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user