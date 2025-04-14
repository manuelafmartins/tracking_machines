# backend/routers/empresas.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import database, crud, schemas

router = APIRouter(prefix="/empresas", tags=["empresas"])

@router.get("/", response_model=list[schemas.Empresa])
def listar_empresas(db: Session = Depends(database.get_db)):
    return crud.get_empresas(db)

@router.post("/", response_model=schemas.Empresa)
def criar_empresa(empresa: schemas.EmpresaCreate, db: Session = Depends(database.get_db)):
    return crud.create_empresa(db, empresa)
