# routers/companies.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database, crud, schemas
from ..dependencies import get_current_user

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/", response_model=list[schemas.Company])
def list_companies(
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    return crud.get_companies(db)

@router.post("/", response_model=schemas.Company)
def create_company(
    company: schemas.CompanyCreate, 
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    return crud.create_company(db, company)

@router.get("/{company_id}", response_model=schemas.Company)
def get_company(
    company_id: int, 
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    company = crud.get_company_by_id(db, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company