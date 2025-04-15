# routers/companies.py
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List
from .. import database, crud, schemas, models
from ..dependencies import get_current_user, get_admin_user, get_company_access
import shutil
import os
from pathlib import Path

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
    List all companies.
    Admin can see all companies, fleet managers can only see their company.
    """
    if current_user.role == models.UserRoleEnum.admin:
        return crud.get_companies(db, skip=skip, limit=limit)
    else:
        # Fleet managers can only see their own company
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
    """Create new company (admin only)"""
    return crud.create_company(db, company)

@router.get("/{company_id}", response_model=schemas.Company)
def get_company(
    company_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get company details.
    Admin can see any company, fleet managers can only see their company.
    """
    # Check if user has access to this company
    get_company_access(company_id, current_user)
    
    company = crud.get_company_by_id(db, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.put("/{company_id}", response_model=schemas.Company)
def update_company(
    company_id: int,
    company_data: schemas.CompanyUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)  # Only admin can update companies
):
    """Update company details (admin only)"""
    updated_company = crud.update_company(db, company_id, company_data)
    if not updated_company:
        raise HTTPException(status_code=404, detail="Company not found")
    return updated_company

@router.delete("/{company_id}", response_model=dict)
def delete_company(
    company_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)  # Only admin can delete companies
):
    """Delete a company and all its associated resources (admin only)"""
    # Get company users first to handle them
    company_users = crud.get_users_by_company(db, company_id)
    
    # Delete the company (will cascade delete machines and maintenances)
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
    current_user: models.User = Depends(get_admin_user)  # Apenas admin pode fazer upload
):
    """Upload e atualiza o logo da empresa (admin only)"""
    # Verificar se a empresa existe
    company = crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
    # Criar um nome de arquivo seguro
    file_extension = os.path.splitext(logo.filename)[1]
    logo_filename = f"company_{company_id}{file_extension}"
    logo_path = LOGO_DIR / logo_filename
    
    # Salvar o arquivo
    try:
        with open(logo_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar o logo: {str(e)}")
    
    # Atualizar o caminho do logo no banco de dados
    relative_path = f"company_logos/{logo_filename}"
    company_data = schemas.CompanyUpdate(logo_path=relative_path)
    
    updated_company = crud.update_company(db, company_id, company_data)
    if not updated_company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    return updated_company