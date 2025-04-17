import os
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session

from .. import database, crud, schemas, models
from ..dependencies import get_current_user, get_admin_user, get_company_access

router = APIRouter(prefix="/companies", tags=["companies"])

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
    Lists companies. Admin sees all; fleet managers see only their own.
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
    """Creates a new company (admin only)."""
    return crud.create_company(db, company)


@router.get("/{company_id}", response_model=schemas.Company)
def get_company(
    company_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieves a company's details. Validates user access permissions.
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
    """Updates a company (admin only)."""
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
    """
    # Optionally, handle associated users first
    company_users = crud.get_users_by_company(db, company_id)
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
    """Uploads and updates the company's logo (admin only)."""
    company = crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    file_extension = os.path.splitext(logo.filename)[1]
    logo_filename = f"company_{company_id}{file_extension}"
    logo_path = LOGO_DIR / logo_filename

    try:
        with open(logo_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao salvar o logo: {e}"
        )

    relative_path = f"company_logos/{logo_filename}"
    updated_company = crud.update_company(db, company_id, schemas.CompanyUpdate(logo_path=relative_path))
    if not updated_company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    return updated_company
