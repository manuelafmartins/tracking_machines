"""CRUD helpers for the Fleet Management back‑end."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from . import models, schemas
from .security import generate_hash


# ──────────────────────────────
# Utility
# ──────────────────────────────
def _commit_refresh(db: Session, instance) -> None:
    """Commit current transaction and refresh *instance*."""
    try:
        db.commit()
        db.refresh(instance)
    except Exception:
        db.rollback()
        raise


# ──────────────────────────────
# USER CRUD
# ──────────────────────────────
def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_users(db: Session, *, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def get_users_by_company(db: Session, company_id: int) -> List[models.User]:
    return db.query(models.User).filter(models.User.company_id == company_id).all()


def create_user(
    db: Session,
    user: schemas.UserCreate,
    *,
    role: models.UserRoleEnum = models.UserRoleEnum.fleet_manager,
) -> models.User:
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=generate_hash(user.password),
        role=role,
        company_id=user.company_id,
    )
    db.add(db_user)
    _commit_refresh(db, db_user)
    return db_user


def update_user(
    db: Session,
    user_id: int,
    user_data: schemas.UserUpdate,
) -> Optional[models.User]:
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    update_data = user_data.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = generate_hash(update_data.pop("password"))

    for key, val in update_data.items():
        setattr(db_user, key, val)

    _commit_refresh(db, db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False
    db.delete(db_user)
    _commit_refresh(db, db_user)
    return True


# ──────────────────────────────
# COMPANY CRUD
# ──────────────────────────────
def get_companies(db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Company]:
    return db.query(models.Company).offset(skip).limit(limit).all()


def get_company_by_id(db: Session, company_id: int) -> Optional[models.Company]:
    return db.query(models.Company).filter(models.Company.id == company_id).first()


def create_company(db: Session, company: schemas.CompanyCreate) -> models.Company:
    """
    Cria uma nova empresa com todos os campos.
    Versão corrigida que garante que todos os campos sejam salvos.
    """
    # Converter o objeto Pydantic para dicionário mantendo os valores vazios
    company_dict = company.model_dump(exclude_unset=False)
    
    # Para debugging - imprimir todos os campos
    print("Creating company with fields:")
    for k, v in company_dict.items():
        print(f"  {k}: {v}")
    
    # Criar objeto da empresa com todos os campos do dicionário
    db_company = models.Company(**company_dict)
    
    # Adicionar à sessão do banco de dados
    db.add(db_company)
    
    try:
        # Confirmar as alterações
        db.commit()
        # Atualizar o objeto com os dados do banco de dados
        db.refresh(db_company)
        return db_company
    except Exception as e:
        # Em caso de erro, reverter as alterações
        db.rollback()
        print(f"Error creating company: {str(e)}")
        raise

def update_company(
    db: Session,
    company_id: int,
    company_data: schemas.CompanyUpdate,
) -> Optional[models.Company]:
    db_company = get_company_by_id(db, company_id)
    if not db_company:
        return None

    for key, val in company_data.model_dump(exclude_unset=True).items():
        setattr(db_company, key, val)

    _commit_refresh(db, db_company)
    return db_company


def delete_company(db: Session, company_id: int) -> bool:
    db_company = get_company_by_id(db, company_id)
    if not db_company:
        return False
    db.delete(db_company)
    _commit_refresh(db, db_company)
    return True


# ──────────────────────────────
# MACHINE CRUD
# ──────────────────────────────
def get_machines(db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Machine]:
    return db.query(models.Machine).offset(skip).limit(limit).all()


def get_machine_by_id(db: Session, machine_id: int) -> Optional[models.Machine]:
    return db.query(models.Machine).filter(models.Machine.id == machine_id).first()


def get_machines_by_company(db: Session, company_id: int) -> List[models.Machine]:
    return db.query(models.Machine).filter(models.Machine.company_id == company_id).all()


def create_machine(db: Session, machine: schemas.MachineCreate) -> models.Machine:
    db_machine = models.Machine(**machine.model_dump())
    db.add(db_machine)
    _commit_refresh(db, db_machine)
    return db_machine


def update_machine(
    db: Session,
    machine_id: int,
    machine_data: schemas.MachineUpdate,
) -> Optional[models.Machine]:
    db_machine = get_machine_by_id(db, machine_id)
    if not db_machine:
        return None

    for key, val in machine_data.model_dump(exclude_unset=True).items():
        setattr(db_machine, key, val)

    _commit_refresh(db, db_machine)
    return db_machine


def delete_machine(db: Session, machine_id: int) -> bool:
    db_machine = get_machine_by_id(db, machine_id)
    if not db_machine:
        return False
    db.delete(db_machine)
    _commit_refresh(db, db_machine)
    return True


# ──────────────────────────────
# MAINTENANCE CRUD
# ──────────────────────────────
def get_maintenances(
    db: Session, *, skip: int = 0, limit: int = 100
) -> List[models.Maintenance]:
    return db.query(models.Maintenance).offset(skip).limit(limit).all()


def get_maintenance_by_id(db: Session, maintenance_id: int) -> Optional[models.Maintenance]:
    return db.query(models.Maintenance).filter(models.Maintenance.id == maintenance_id).first()


def get_machine_maintenances(db: Session, machine_id: int) -> List[models.Maintenance]:
    return db.query(models.Maintenance).filter(models.Maintenance.machine_id == machine_id).all()


def get_company_maintenances(db: Session, company_id: int) -> List[models.Maintenance]:
    """All maintenances for machines belonging to *company_id*."""
    return (
        db.query(models.Maintenance)
        .join(models.Machine)
        .filter(models.Machine.company_id == company_id)
        .all()
    )


def create_maintenance(db: Session, maintenance: schemas.MaintenanceCreate) -> models.Maintenance:
    db_maintenance = models.Maintenance(**maintenance.model_dump())
    db.add(db_maintenance)
    _commit_refresh(db, db_maintenance)
    return db_maintenance


def update_maintenance(
    db: Session,
    maintenance_id: int,
    maintenance_data: schemas.MaintenanceUpdate,
) -> Optional[models.Maintenance]:
    db_maintenance = get_maintenance_by_id(db, maintenance_id)
    if not db_maintenance:
        return None

    for key, val in maintenance_data.model_dump(exclude_unset=True).items():
        setattr(db_maintenance, key, val)

    _commit_refresh(db, db_maintenance)
    return db_maintenance


def update_maintenance_status(db: Session, maintenance_id: int, completed: bool) -> Optional[models.Maintenance]:
    maintenance = get_maintenance_by_id(db, maintenance_id)
    if not maintenance:
        return None

    maintenance.completed = completed
    _commit_refresh(db, maintenance)
    return maintenance


def delete_maintenance(db: Session, maintenance_id: int) -> bool:
    db_maintenance = get_maintenance_by_id(db, maintenance_id)
    if not db_maintenance:
        return False
    db.delete(db_maintenance)
    _commit_refresh(db, db_maintenance)
    return True


# ──────────────────────────────
# Helpers for alarms / dashboards
# ──────────────────────────────
def list_pending_maintenances(db: Session) -> List[models.Maintenance]:
    """Maintenances due within the next 7 days (not completed)."""
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    return (
        db.query(models.Maintenance)
        .filter(
            and_(
                models.Maintenance.scheduled_date.between(today, next_week),
                models.Maintenance.completed.is_(False),
            )
        )
        .all()
    )


def list_company_pending_maintenances(db: Session, company_id: int) -> List[models.Maintenance]:
    """Pending maintenances in next 7 days for *company_id*."""
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    return (
        db.query(models.Maintenance)
        .join(models.Machine)
        .filter(
            and_(
                models.Machine.company_id == company_id,
                models.Maintenance.scheduled_date.between(today, next_week),
                models.Maintenance.completed.is_(False),
            )
        )
        .all()
    )


# ──────────────────────────────
# SERVICE CRUD
# ──────────────────────────────
def get_services(db: Session, *, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[models.Service]:
    query = db.query(models.Service)
    if active_only:
        query = query.filter(models.Service.is_active == True)
    return query.offset(skip).limit(limit).all()

def get_service_by_id(db: Session, service_id: int) -> Optional[models.Service]:
    return db.query(models.Service).filter(models.Service.id == service_id).first()

def create_service(db: Session, service: schemas.ServiceCreate) -> models.Service:
    db_service = models.Service(**service.model_dump())
    db.add(db_service)
    _commit_refresh(db, db_service)
    return db_service

def update_service(db: Session, service_id: int, service_data: schemas.ServiceUpdate) -> Optional[models.Service]:
    db_service = get_service_by_id(db, service_id)
    if not db_service:
        return None

    for key, val in service_data.model_dump(exclude_unset=True).items():
        setattr(db_service, key, val)

    _commit_refresh(db, db_service)
    return db_service

def delete_service(db: Session, service_id: int) -> bool:
    db_service = get_service_by_id(db, service_id)
    if not db_service:
        return False
    
    # Em vez de excluir, apenas marcar como inativo
    db_service.is_active = False
    _commit_refresh(db, db_service)
    return True

# ──────────────────────────────
# INVOICE CRUD
# ──────────────────────────────
def _generate_invoice_number(db: Session) -> str:
    """Gera um número de fatura sequencial no formato FP-YYYYMM-XXXX"""
    today = datetime.now()
    prefix = f"FP-{today.year}{today.month:02d}-"
    
    # Encontrar o maior número já usado no mês atual
    result = db.query(func.max(models.Invoice.invoice_number)).filter(
        models.Invoice.invoice_number.like(f"{prefix}%")
    ).scalar()
    
    if result:
        try:
            last_num = int(result.split('-')[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    
    return f"{prefix}{new_num:04d}"

def get_invoices(db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Invoice]:
    return db.query(models.Invoice).order_by(models.Invoice.issue_date.desc()).offset(skip).limit(limit).all()

def get_company_invoices(db: Session, company_id: int) -> List[models.Invoice]:
    return db.query(models.Invoice).filter(models.Invoice.company_id == company_id).order_by(models.Invoice.issue_date.desc()).all()

def get_invoice_by_id(db: Session, invoice_id: int) -> Optional[models.Invoice]:
    return db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()

def create_invoice(db: Session, invoice: schemas.InvoiceCreate) -> models.Invoice:
    """Cria uma nova fatura com seus itens"""
    # Criar uma transação para garantir a integridade dos dados
    db_invoice = models.Invoice(
        invoice_number=_generate_invoice_number(db),
        company_id=invoice.company_id,
        issue_date=invoice.issue_date or datetime.now().date(),
        due_date=invoice.due_date,
        notes=invoice.notes,
        payment_method=invoice.payment_method,
        status=invoice.status
    )
    
    db.add(db_invoice)
    db.flush()  # Para obter o ID da fatura
    
    # Processar os itens da fatura
    subtotal = 0.0
    tax_total = 0.0
    
    for item_data in invoice.items:
        # Obter o serviço para pegar preço e taxa de imposto se não fornecidos
        service = get_service_by_id(db, item_data.service_id)
        if not service:
            db.rollback()
            raise ValueError(f"Service with ID {item_data.service_id} not found")
        
        unit_price = item_data.unit_price if item_data.unit_price is not None else service.unit_price
        tax_rate = item_data.tax_rate if item_data.tax_rate is not None else service.tax_rate
        description = item_data.description or service.name
        
        # Calcular valores
        item_subtotal = unit_price * item_data.quantity
        item_tax = item_subtotal * (tax_rate / 100)
        item_total = item_subtotal + item_tax
        
        # Criar o item
        db_item = models.InvoiceItem(
            invoice_id=db_invoice.id,
            service_id=service.id,
            machine_id=item_data.machine_id,
            quantity=item_data.quantity,
            description=description,
            unit_price=unit_price,
            tax_rate=tax_rate,
            subtotal=item_subtotal,
            tax_amount=item_tax,
            total=item_total
        )
        
        db.add(db_item)
        
        # Atualizar totais da fatura
        subtotal += item_subtotal
        tax_total += item_tax
    
    # Atualizar os totais da fatura
    db_invoice.subtotal = subtotal
    db_invoice.tax_total = tax_total
    db_invoice.total = subtotal + tax_total
    
    _commit_refresh(db, db_invoice)
    return db_invoice

def update_invoice_status(db: Session, invoice_id: int, status: models.InvoiceStatus, payment_date: Optional[date] = None) -> Optional[models.Invoice]:
    """Atualiza o status de uma fatura (e data de pagamento se aplicável)"""
    invoice = get_invoice_by_id(db, invoice_id)
    if not invoice:
        return None
    
    invoice.status = status
    
    # Se for marcada como paga, registrar a data de pagamento
    if status == models.InvoiceStatus.PAID and payment_date:
        invoice.payment_date = payment_date
    
    _commit_refresh(db, invoice)
    return invoice

def delete_invoice(db: Session, invoice_id: int) -> bool:
    """Exclui uma fatura (apenas se estiver em rascunho)"""
    invoice = get_invoice_by_id(db, invoice_id)
    if not invoice:
        return False
    
    # Apenas faturas em rascunho podem ser excluídas
    if invoice.status != models.InvoiceStatus.DRAFT:
        return False
    
    db.delete(invoice)  # Cascade deleta os itens
    _commit_refresh(db, invoice)
    return True