# routers/machines.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import database, crud, schemas, models
from ..dependencies import get_current_user, get_admin_user, get_company_access, check_machine_access
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
    List machines.
    Admin can see all machines, fleet managers can only see their company's machines.
    """
    if current_user.role == models.UserRoleEnum.admin:
        return crud.get_machines(db, skip=skip, limit=limit)
    else:
        # Fleet managers can only see machines from their company
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
    Create a new machine.
    Admin can create machines for any company, fleet managers only for their company.
    """
    # Check if user has access to the company where they want to add the machine
    get_company_access(machine.company_id, current_user)
    
    # Criar a máquina
    new_machine = crud.create_machine(db, machine)
    
    # Obter o nome da empresa para a notificação
    company = get_company_by_id(db, machine.company_id)
    company_name = company.name if company else "Desconhecida"
    
    # Enviar notificação
    try:
        notify_new_machine_added(
            db, 
            machine_name=new_machine.name,
            company_id=machine.company_id,
            company_name=company_name
        )
    except Exception as e:
        # Log error but don't fail the request
        logging.error(f"Failed to send machine creation notification: {str(e)}")
    
    return new_machine

@router.get("/{machine_id}", response_model=schemas.Machine)
def get_machine(
    machine_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get machine details.
    Admin can see any machine, fleet managers can only see their company's machines.
    """
    # Check if user has access to this machine
    check_machine_access(machine_id, current_user, db)
    
    machine = crud.get_machine_by_id(db, machine_id)
    if machine is None:
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
    Update machine details.
    Admin can update any machine, fleet managers only their company's machines.
    """
    # Check if user has access to this machine
    check_machine_access(machine_id, current_user, db)
    
    # If company_id is being updated, check if user has access to the target company
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
    Delete a machine and its maintenances.
    Admin can delete any machine, fleet managers only their company's machines.
    """
    # Check if user has access to this machine
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
    List machines belonging to a specific company.
    Admin can see any company's machines, fleet managers only their company's machines.
    """
    # Check if user has access to this company
    get_company_access(company_id, current_user)
    
    return crud.get_machines_by_company(db, company_id)