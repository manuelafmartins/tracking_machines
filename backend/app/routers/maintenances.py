import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import database, crud, schemas, models
from ..dependencies import (
    get_current_user,
    check_maintenance_access,
    check_machine_access
)
from ..notifications import notify_new_maintenance_scheduled, notify_maintenance_completed
from ..crud import get_machine_by_id, get_company_by_id

router = APIRouter(prefix="/maintenances", tags=["maintenances"])


@router.get("/", response_model=List[schemas.Maintenance])
def list_maintenances(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Lists all maintenances. Admin sees all; fleet managers see only their own company's.
    """
    if current_user.role == models.UserRoleEnum.admin:
        return crud.get_maintenances(db, skip=skip, limit=limit)
    if current_user.company_id:
        return crud.get_company_maintenances(db, current_user.company_id)
    return []


@router.post("/", response_model=schemas.Maintenance)
def create_maintenance(
    maintenance: schemas.MaintenanceCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Creates a new maintenance. Admin can create for any machine; fleet managers only for their own company's machines.
    """
    check_machine_access(maintenance.machine_id, current_user, db)
    new_maintenance = crud.create_maintenance(db, maintenance)

    machine = get_machine_by_id(db, maintenance.machine_id)
    if machine:
        machine_name = machine.name
        company_id = machine.company_id
        company = get_company_by_id(db, company_id)
        company_name = company.name if company else "Desconhecida"

        try:
            notify_new_maintenance_scheduled(
                db,
                machine_name=machine_name,
                maintenance_type=maintenance.type,
                scheduled_date=maintenance.scheduled_date.strftime("%d/%m/%Y"),
                company_id=company_id,
                company_name=company_name
            )
        except Exception as e:
            logging.error(f"Failed to send maintenance creation notification: {e}")

    return new_maintenance


@router.get("/{maintenance_id}", response_model=schemas.Maintenance)
def get_maintenance(
    maintenance_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieves maintenance details. Validates user access.
    """
    check_maintenance_access(maintenance_id, current_user, db)
    maintenance = crud.get_maintenance_by_id(db, maintenance_id)
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return maintenance


@router.put("/{maintenance_id}", response_model=schemas.Maintenance)
def update_maintenance(
    maintenance_id: int,
    maintenance_data: schemas.MaintenanceUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Updates maintenance details. Admin can update any; fleet managers only their own company's.
    """
    check_maintenance_access(maintenance_id, current_user, db)
    updated_maintenance = crud.update_maintenance(db, maintenance_id, maintenance_data)
    if not updated_maintenance:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return updated_maintenance


@router.patch("/{maintenance_id}/complete", response_model=schemas.Maintenance)
def mark_maintenance_completed(
    maintenance_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Marks a maintenance as completed. Admin can update any; fleet managers only their own company's.
    """
    check_maintenance_access(maintenance_id, current_user, db)
    maintenance_before = crud.get_maintenance_by_id(db, maintenance_id)
    if not maintenance_before:
        raise HTTPException(status_code=404, detail="Maintenance not found")

    maintenance = crud.update_maintenance_status(db, maintenance_id, True)

    if maintenance and maintenance_before.machine:
        machine = maintenance_before.machine
        machine_name = machine.name
        company_id = machine.company_id
        company = get_company_by_id(db, company_id)
        company_name = company.name if company else "Desconhecida"

        try:
            notify_maintenance_completed(
                db,
                machine_name=machine_name,
                maintenance_type=maintenance.type,
                company_id=company_id,
                company_name=company_name
            )
        except Exception as e:
            logging.error(f"Failed to send maintenance completion notification: {e}")

    return maintenance


@router.delete("/{maintenance_id}", response_model=dict)
def delete_maintenance(
    maintenance_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Deletes a maintenance. Admin can delete any; fleet managers only their own company's.
    """
    check_maintenance_access(maintenance_id, current_user, db)
    result = crud.delete_maintenance(db, maintenance_id)
    if not result:
        raise HTTPException(status_code=404, detail="Maintenance not found")

    return {"success": True, "message": "Maintenance deleted successfully"}


@router.get("/machine/{machine_id}", response_model=List[schemas.Maintenance])
def get_machine_maintenances(
    machine_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Lists maintenances for a specific machine.
    Validates user access, then retrieves the data.
    """
    check_machine_access(machine_id, current_user, db)
    return crud.get_machine_maintenances(db, machine_id)


@router.get("/company/{company_id}", response_model=List[schemas.Maintenance])
def get_company_maintenances(
    company_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Lists maintenances for a specific company. Validates access first.
    """
    from ..dependencies import get_company_access
    get_company_access(company_id, current_user)
    return crud.get_company_maintenances(db, company_id)
