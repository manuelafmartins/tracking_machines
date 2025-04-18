import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import database, crud, schemas, models
from ..dependencies import (
    get_current_user, 
    get_admin_user, 
    get_company_access, 
    check_machine_access
)
from ..notifications import notify_new_machine_added
from ..crud import get_company_by_id

router = APIRouter(prefix="/machines", tags=["machines"])


@router.get("/", response_model=List[schemas.Machine])
def list_machines(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Lists machines. Admin can see all; fleet managers only their company's machines.
    """
    if current_user.role == models.UserRoleEnum.admin:
        return crud.get_machines(db, skip=skip, limit=limit)
    if current_user.company_id:
        return crud.get_machines_by_company(db, current_user.company_id)
    return []


@router.post("/", response_model=schemas.Machine)
def create_machine(
    machine: schemas.MachineCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Creates a new machine.
    Admin can create for any company; fleet managers only for their own company.
    """
    get_company_access(machine.company_id, current_user)
    new_machine = crud.create_machine(db, machine)

    company = get_company_by_id(db, machine.company_id)
    company_name = company.name if company else "Desconhecida"

    # Attempt to send notification
    try:
        notify_new_machine_added(
            db,
            machine_name=new_machine.name,
            company_id=machine.company_id,
            company_name=company_name
        )
    except Exception as e:
        logging.error(f"Failed to send machine creation notification: {e}")

    return new_machine


@router.get("/{machine_id}", response_model=schemas.Machine)
def get_machine(
    machine_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieves details for a specific machine.
    Validates that the user has access to this machine.
    """
    check_machine_access(machine_id, current_user, db)
    machine = crud.get_machine_by_id(db, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


@router.put("/{machine_id}", response_model=schemas.Machine)
def update_machine(
    machine_id: int,
    machine_data: schemas.MachineUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Updates machine details.
    Admin can update any; fleet managers can only update their company's machines.
    """
    check_machine_access(machine_id, current_user, db)
    if machine_data.company_id is not None:
        get_company_access(machine_data.company_id, current_user)

    updated_machine = crud.update_machine(db, machine_id, machine_data)
    if not updated_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return updated_machine


@router.delete("/{machine_id}", response_model=dict)
def delete_machine(
    machine_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Deletes a machine (and its maintenances).
    Admin can delete any; fleet managers only their own company's machines.
    """
    check_machine_access(machine_id, current_user, db)
    result = crud.delete_machine(db, machine_id)
    if not result:
        raise HTTPException(status_code=404, detail="Machine not found")

    return {
        "success": True,
        "message": "Machine deleted successfully with all associated maintenances"
    }


@router.get("/company/{company_id}", response_model=List[schemas.Machine])
def get_company_machines(
    company_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Lists machines for a specific company.
    Admin can see any; fleet managers only their own company's machines.
    """
    get_company_access(company_id, current_user)
    return crud.get_machines_by_company(db, company_id)
