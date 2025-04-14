# routers/maintenances.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database, crud, schemas
from ..dependencies import get_current_user

router = APIRouter(prefix="/maintenances", tags=["maintenances"])

@router.get("/", response_model=list[schemas.Maintenance])
def list_maintenances(
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    return crud.get_maintenances(db)

@router.post("/", response_model=schemas.Maintenance)
def create_maintenance(
    maintenance: schemas.MaintenanceCreate, 
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    return crud.create_maintenance(db, maintenance)

@router.get("/{maintenance_id}", response_model=schemas.Maintenance)
def get_maintenance(
    maintenance_id: int, 
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    maintenance = crud.get_maintenance_by_id(db, maintenance_id)
    if maintenance is None:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return maintenance

@router.get("/machine/{machine_id}", response_model=list[schemas.Maintenance])
def get_machine_maintenances(
    machine_id: int, 
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    return crud.get_machine_maintenances(db, machine_id)

@router.patch("/{maintenance_id}/complete", response_model=schemas.Maintenance)
def mark_maintenance_completed(
    maintenance_id: int, 
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    maintenance = crud.update_maintenance_status(db, maintenance_id, True)
    if maintenance is None:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return maintenance