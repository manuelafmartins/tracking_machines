from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from .. import database, crud, schemas, models
from ..dependencies import get_current_user, get_admin_user, get_company_access

router = APIRouter(prefix="/billing", tags=["billing"])

# Rotas para serviços
@router.get("/services", response_model=List[schemas.Service])
def list_services(
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Lista todos os serviços disponíveis"""
    return crud.get_services(db, skip=skip, limit=limit, active_only=active_only)

@router.post("/services", response_model=schemas.Service)
def create_service(
    service: schemas.ServiceCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)
):
    """Cria um novo serviço (apenas admin)"""
    return crud.create_service(db, service)

@router.get("/services/{service_id}", response_model=schemas.Service)
def get_service(
    service_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtém detalhes de um serviço específico"""
    service = crud.get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@router.put("/services/{service_id}", response_model=schemas.Service)
def update_service(
    service_id: int,
    service_data: schemas.ServiceUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)
):
    """Atualiza um serviço existente (apenas admin)"""
    updated_service = crud.update_service(db, service_id, service_data)
    if not updated_service:
        raise HTTPException(status_code=404, detail="Service not found")
    return updated_service

@router.delete("/services/{service_id}", response_model=dict)
def delete_service(
    service_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)
):
    """Desativa um serviço (apenas admin)"""
    result = crud.delete_service(db, service_id)
    if not result:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"success": True, "message": "Service deactivated successfully"}

# Rotas para faturas
@router.get("/invoices", response_model=List[schemas.Invoice])
def list_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Lista todas as faturas (admin vê todas, gestores veem apenas as suas)"""
    if current_user.role == models.UserRoleEnum.admin:
        return crud.get_invoices(db, skip=skip, limit=limit)
    if current_user.company_id:
        return crud.get_company_invoices(db, current_user.company_id)
    return []

@router.post("/invoices", response_model=schemas.Invoice)
def create_invoice(
    invoice: schemas.InvoiceCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Cria uma nova fatura"""
    # Verificar acesso à empresa
    from ..dependencies import get_company_access
    get_company_access(invoice.company_id, current_user)
    
    try:
        return crud.create_invoice(db, invoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/invoices/{invoice_id}", response_model=schemas.Invoice)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtém detalhes de uma fatura específica"""
    invoice = crud.get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Verificar acesso à empresa
    from ..dependencies import get_company_access
    get_company_access(invoice.company_id, current_user)
    
    return invoice

@router.patch("/invoices/{invoice_id}/status", response_model=schemas.Invoice)
def update_invoice_status(
    invoice_id: int,
    status: schemas.InvoiceStatus,
    payment_date: Optional[date] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Atualiza o status de uma fatura"""
    invoice = crud.get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Verificar acesso à empresa
    from ..dependencies import get_company_access
    get_company_access(invoice.company_id, current_user)
    
    updated_invoice = crud.update_invoice_status(db, invoice_id, status, payment_date)
    return updated_invoice

@router.delete("/invoices/{invoice_id}", response_model=dict)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Exclui uma fatura (apenas se estiver em rascunho)"""
    invoice = crud.get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Verificar acesso à empresa
    from ..dependencies import get_company_access
    get_company_access(invoice.company_id, current_user)
    
    result = crud.delete_invoice(db, invoice_id)
    if not result:
        raise HTTPException(status_code=400, detail="Only invoices in draft status can be deleted")
    
    return {"success": True, "message": "Invoice deleted successfully"}

@router.get("/invoices/company/{company_id}", response_model=List[schemas.Invoice])
def get_company_invoices(
    company_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Lista todas as faturas de uma empresa específica"""
    # Verificar acesso à empresa
    from ..dependencies import get_company_access
    get_company_access(company_id, current_user)
    
    return crud.get_company_invoices(db, company_id)