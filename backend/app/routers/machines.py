# routers/machines.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database, crud, schemas
from ..dependencies import get_current_user

router = APIRouter(prefix="/machines", tags=["machines"])

@router.get("/", response_model=list[schemas.Machine])
def list_machines(
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    return crud.get_machines(db)

@router.post("/", response_model=schemas.Machine)
def create_machine(
    machine: schemas.MachineCreate, 
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    return crud.create_machine(db, machine)

@router.get("/{machine_id}", response_model=schemas.Machine)
def get_machine(
    machine_id: int, 
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    machine = crud.get_machine_by_id(db, machine_id)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

@router.get("/company/{company_id}", response_model=list[schemas.Machine])
def get_company_machines(
    company_id: int, 
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    return crud.get_machines_by_company(db, company_id)