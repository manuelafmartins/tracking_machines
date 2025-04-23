import os
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session

from .. import database, crud, schemas, models
from ..dependencies import get_current_user, get_admin_user, get_company_access
from ..email_service import send_company_creation_email
from ..notifications import notify_new_company_added
import os
import logging

# Configure router
router = APIRouter(prefix="/companies", tags=["companies"])

# Directory for company logos
LOGO_DIR = Path("frontend/images/company_logos")
os.makedirs(LOGO_DIR, exist_ok=True)


@router.get("/", response_model=List[schemas.Company])
def list_companies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Lists companies based on user role.
    
    Admins can see all companies; fleet managers see only their own company.
    
    Args:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of companies the user has access to
    """
    if current_user.role == models.UserRoleEnum.admin:
        return crud.get_companies(db, skip=skip, limit=limit)
    if current_user.company_id:
        company = crud.get_company_by_id(db, current_user.company_id)
        return [company] if company else []
    return []


@router.post("/", response_model=schemas.Company)
def create_company(
    company: schemas.CompanyCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)
):
    db_company = crud.create_company(db, company)
    
    # Notificar sobre a nova empresa
    try:
        notify_new_company_added(db, db_company.name, db_company.id)
    except Exception as e:
        logging.error(f"Erro ao enviar notificação de nova empresa: {str(e)}")
    
    return db_company

@router.get("/{company_id}", response_model=schemas.Company)
def get_company(
    company_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieves a company's details.
    
    Validates user access permissions before returning company data.
    
    Args:
        company_id: ID of company to retrieve
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Company details
        
    Raises:
        HTTPException: If company not found or user lacks access permission
    """
    get_company_access(company_id, current_user)
    company = crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=schemas.Company)
def update_company(
    company_id: int,
    company_data: schemas.CompanyUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)
):
    """
    Updates a company (admin only).
    
    Args:
        company_id: ID of company to update
        company_data: Company data to update
        db: Database session
        current_user: Current user (must be admin)
        
    Returns:
        Updated company
        
    Raises:
        HTTPException: If company not found
    """
    updated_company = crud.update_company(db, company_id, company_data)
    if not updated_company:
        raise HTTPException(status_code=404, detail="Company not found")
    return updated_company


@router.delete("/{company_id}", response_model=dict)
def delete_company(
    company_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)
):
    """
    Deletes a company and all its associated machines and maintenances (admin only).
    
    Args:
        company_id: ID of company to delete
        db: Database session
        current_user: Current user (must be admin)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If company not found
    """
    # Get associated users before deletion (optional)
    company_users = crud.get_users_by_company(db, company_id)
    
    # Delete company (cascades to machines and maintenances)
    result = crud.delete_company(db, company_id)
    if not result:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {
        "success": True,
        "message": "Company deleted successfully with all associated machines and maintenances"
    }


@router.post("/{company_id}/logo", response_model=schemas.Company)
def upload_company_logo(
    company_id: int,
    logo: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)
):
    """
    Uploads and updates the company's logo (admin only).
    
    Args:
        company_id: ID of company to update logo
        logo: Uploaded image file
        db: Database session
        current_user: Current user (must be admin)
        
    Returns:
        Updated company
        
    Raises:
        HTTPException: If company not found or error saving logo
    """
    # Verify company exists
    company = crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Save uploaded logo
    file_extension = os.path.splitext(logo.filename)[1]
    logo_filename = f"company_{company_id}{file_extension}"
    logo_path = LOGO_DIR / logo_filename

    try:
        with open(logo_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error saving logo: {e}"
        )

    # Update company with new logo path
    relative_path = f"company_logos/{logo_filename}"
    updated_company = crud.update_company(db, company_id, schemas.CompanyUpdate(logo_path=relative_path))
    if not updated_company:
        raise HTTPException(status_code=404, detail="Company not found")

    return updated_company