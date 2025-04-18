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

# Configure router
router = APIRouter(prefix="/machines", tags=["machines"])


@router.get("/", response_model=List[schemas.Machine])
def list_machines(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Lists machines based on user role.
    
    Admins can see all machines; fleet managers see only their company's machines.
    
    Args:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of machines the user has access to
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
    Sends a notification about the new machine creation.
    
    Args:
        machine: Machine data to create
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created machine
        
    Raises:
        HTTPException: If user lacks access to the specified company
    """
    # Verify access to the company
    get_company_access(machine.company_id, current_user)
    
    # Create the machine
    new_machine = crud.create_machine(db, machine)

    # Get company name for notification
    company = get_company_by_id(db, machine.company_id)
    company_name = company.name if company else "Unknown"

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
    
    Validates that the user has access to this machine before returning details.
    
    Args:
        machine_id: ID of machine to retrieve
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Machine details
        
    Raises:
        HTTPException: If machine not found or user lacks access permission
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
    
    Admin can update any machine; fleet managers can only update their company's machines.
    If company ID is being updated, verifies access to the target company.
    
    Args:
        machine_id: ID of machine to update
        machine_data: Machine data to update
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated machine
        
    Raises:
        HTTPException: If machine not found or user lacks access permission
    """
    # Verify access to the machine
    check_machine_access(machine_id, current_user, db)
    
    # If company is being changed, verify access to target company
    if machine_data.company_id is not None:
        get_company_access(machine_data.company_id, current_user)

    # Update the machine
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
    Deletes a machine and all its associated maintenances.
    
    Admin can delete any machine; fleet managers only their own company's machines.
    
    Args:
        machine_id: ID of machine to delete
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If machine not found or user lacks access permission
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
    
    Admin can see any company's machines; fleet managers only their own company's machines.
    
    Args:
        company_id: ID of company to list machines for
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of machines for the specified company
        
    Raises:
        HTTPException: If user lacks access permission to the company
    """
    get_company_access(company_id, current_user)
    return crud.get_machines_by_company(db, company_id)