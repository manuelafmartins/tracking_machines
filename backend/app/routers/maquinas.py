from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import database, crud, schemas

router = APIRouter(prefix="/maquinas", tags=["maquinas"])

@router.get("/", response_model=list[schemas.Maquina])
def listar_maquinas(db: Session = Depends(database.get_db)):
    return crud.get_maquinas(db)

@router.post("/", response_model=schemas.Maquina)
def criar_maquina(maquina: schemas.MaquinaCreate, db: Session = Depends(database.get_db)):
    return crud.create_maquina(db, maquina)
