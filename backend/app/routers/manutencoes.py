from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import database, crud, schemas

router = APIRouter(prefix="/manutencoes", tags=["manutencoes"])

@router.get("/", response_model=list[schemas.Manutencao])
def listar_manutencoes(db: Session = Depends(database.get_db)):
    return crud.get_manutencoes(db)

@router.post("/", response_model=schemas.Manutencao)
def criar_manutencao(manutencao: schemas.ManutencaoCreate, db: Session = Depends(database.get_db)):
    return crud.create_manutencao(db, manutencao)
