# backend/crud.py
from sqlalchemy.orm import Session
from datetime import date
from . import models, schemas

# 1) Empresa
def create_empresa(db: Session, empresa: schemas.EmpresaCreate):
    db_empresa = models.Empresa(nome=empresa.nome)
    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa

def get_empresas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Empresa).offset(skip).limit(limit).all()


# 2) Maquina
def create_maquina(db: Session, maquina: schemas.MaquinaCreate):
    db_maquina = models.Maquina(
        nome=maquina.nome,
        tipo=maquina.tipo,
        empresa_id=maquina.empresa_id
    )
    db.add(db_maquina)
    db.commit()
    db.refresh(db_maquina)
    return db_maquina

def get_maquinas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Maquina).offset(skip).limit(limit).all()


# 3) Manutencao
def create_manutencao(db: Session, manutencao: schemas.ManutencaoCreate):
    db_manutencao = models.Manutencao(
        maquina_id=manutencao.maquina_id,
        tipo=manutencao.tipo,
        data_prevista=manutencao.data_prevista
    )
    db.add(db_manutencao)
    db.commit()
    db.refresh(db_manutencao)
    return db_manutencao

def get_manutencoes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Manutencao).offset(skip).limit(limit).all()

def listar_manutencoes_pendentes(db: Session):
    # Exemplo: filtra manutenções com data <= hoje
    return db.query(models.Manutencao).filter(models.Manutencao.data_prevista <= date.today()).all()
