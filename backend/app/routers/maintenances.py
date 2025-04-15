# routers/maintenances.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import database, crud, schemas, models
from ..dependencies import get_current_user, check_maintenance_access, check_machine_access
from fastapi import Body, HTTPException

router = APIRouter(prefix="/maintenances", tags=["maintenances"])

@router.get("/", response_model=List[schemas.Maintenance])
def list_maintenances(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    List maintenances.
    Admin can see all maintenances, fleet managers only see their company's maintenances.
    """
    if current_user.role == models.UserRoleEnum.admin:
        return crud.get_maintenances(db, skip=skip, limit=limit)
    else:
        # Fleet managers can only see maintenances for their company
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
    Create a new maintenance.
    Admin can create maintenances for any machine, fleet managers only for their company's machines.
    """
    # Check if user has access to the machine
    check_machine_access(maintenance.machine_id, current_user, db)
    
    return crud.create_maintenance(db, maintenance)

@router.get("/{maintenance_id}", response_model=schemas.Maintenance)
def get_maintenance(
    maintenance_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get maintenance details.
    Admin can see any maintenance, fleet managers only their company's maintenances.
    """
    # Check if user has access to this maintenance
    check_maintenance_access(maintenance_id, current_user, db)
    
    maintenance = crud.get_maintenance_by_id(db, maintenance_id)
    if maintenance is None:
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
    Update maintenance details.
    Admin can update any maintenance, fleet managers only their company's maintenances.
    """
    # Check if user has access to this maintenance
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
    Mark a maintenance as completed.
    Admin can update any maintenance, fleet managers only their company's maintenances.
    """
    # Check if user has access to this maintenance
    check_maintenance_access(maintenance_id, current_user, db)
    
    maintenance = crud.update_maintenance_status(db, maintenance_id, True)
    if maintenance is None:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    return maintenance

@router.delete("/{maintenance_id}", response_model=dict)
def delete_maintenance(
    maintenance_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Delete a maintenance.
    Admin can delete any maintenance, fleet managers only their company's maintenances.
    """
    # Check if user has access to this maintenance
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
    List maintenances for a specific machine.
    Admin can see any machine's maintenances, fleet managers only their company's machine maintenances.
    """
    # Check if user has access to this machine
    check_machine_access(machine_id, current_user, db)
    
    return crud.get_machine_maintenances(db, machine_id)

@router.get("/company/{company_id}", response_model=List[schemas.Maintenance])
def get_company_maintenances(
    company_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    List all maintenances for a specific company's machines.
    Admin can see any company's maintenances, fleet managers only their company's maintenances.
    """
    # This is handled in the get_company_access dependency
    from ..dependencies import get_company_access
    get_company_access(company_id, current_user)
    
    return crud.get_company_maintenances(db, company_id)
