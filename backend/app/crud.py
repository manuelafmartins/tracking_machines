# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from . import models, schemas
from .security import generate_hash
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

# --- USER CRUD ---
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_id(db: Session, user_id: int):
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_users_by_company(db: Session, company_id: int):
    return db.query(models.User).filter(models.User.company_id == company_id).all()

def create_user(db: Session, user: schemas.UserCreate, role: models.UserRoleEnum = models.UserRoleEnum.fleet_manager):
    hashed_password = generate_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=role,
        company_id=user.company_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_data: schemas.UserUpdate):
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    # Update user data
    update_data = user_data.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = generate_hash(update_data.pop("password"))
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    """Delete user by ID"""
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

# --- COMPANY CRUD ---
def get_companies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Company).offset(skip).limit(limit).all()

def get_company_by_id(db: Session, company_id: int):
    return db.query(models.Company).filter(models.Company.id == company_id).first()

def create_company(db: Session, company: schemas.CompanyCreate):
    db_company = models.Company(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def update_company(db: Session, company_id: int, company_data: schemas.CompanyUpdate):
    db_company = get_company_by_id(db, company_id)
    if not db_company:
        return None
    
    update_data = company_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_company, key, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company

def delete_company(db: Session, company_id: int):
    db_company = get_company_by_id(db, company_id)
    if db_company:
        db.delete(db_company)
        db.commit()
        return True
    return False

# --- MACHINE CRUD ---
def get_machines(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Machine).offset(skip).limit(limit).all()

def get_machine_by_id(db: Session, machine_id: int):
    return db.query(models.Machine).filter(models.Machine.id == machine_id).first()

def get_machines_by_company(db: Session, company_id: int):
    return db.query(models.Machine).filter(models.Machine.company_id == company_id).all()

def create_machine(db: Session, machine: schemas.MachineCreate):
    db_machine = models.Machine(**machine.model_dump())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine

def update_machine(db: Session, machine_id: int, machine_data: schemas.MachineUpdate):
    db_machine = get_machine_by_id(db, machine_id)
    if not db_machine:
        return None
    
    update_data = machine_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_machine, key, value)
    
    db.commit()
    db.refresh(db_machine)
    return db_machine

def delete_machine(db: Session, machine_id: int):
    db_machine = get_machine_by_id(db, machine_id)
    if db_machine:
        db.delete(db_machine)
        db.commit()
        return True
    return False

# --- MAINTENANCE CRUD ---
def get_maintenances(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Maintenance).offset(skip).limit(limit).all()

def get_maintenance_by_id(db: Session, maintenance_id: int):
    return db.query(models.Maintenance).filter(models.Maintenance.id == maintenance_id).first()

def get_machine_maintenances(db: Session, machine_id: int):
    return db.query(models.Maintenance).filter(models.Maintenance.machine_id == machine_id).all()

def get_company_maintenances(db: Session, company_id: int):
    """Get all maintenances for machines owned by a specific company"""
    return db.query(models.Maintenance).join(models.Machine).filter(
        models.Machine.company_id == company_id
    ).all()

def create_maintenance(db: Session, maintenance: schemas.MaintenanceCreate):
    db_maintenance = models.Maintenance(**maintenance.model_dump())
    db.add(db_maintenance)
    db.commit()
    db.refresh(db_maintenance)
    return db_maintenance

def update_maintenance(db: Session, maintenance_id: int, maintenance_data: schemas.MaintenanceUpdate):
    db_maintenance = get_maintenance_by_id(db, maintenance_id)
    if not db_maintenance:
        return None
    
    update_data = maintenance_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_maintenance, key, value)
    
    db.commit()
    db.refresh(db_maintenance)
    return db_maintenance

def update_maintenance_status(db: Session, maintenance_id: int, completed: bool):
    maintenance = get_maintenance_by_id(db, maintenance_id)
    if maintenance:
        maintenance.completed = completed
        db.commit()
        db.refresh(maintenance)
    return maintenance

def delete_maintenance(db: Session, maintenance_id: int):
    db_maintenance = get_maintenance_by_id(db, maintenance_id)
    if db_maintenance:
        db.delete(db_maintenance)
        db.commit()
        return True
    return False

def list_pending_maintenances(db: Session):
    today = datetime.now().date()
    # Get maintenances scheduled in the next 7 days and not completed
    next_week = today + timedelta(days=7)
    return db.query(models.Maintenance).filter(
        and_(
            models.Maintenance.scheduled_date.between(today, next_week),
            models.Maintenance.completed == False
        )
    ).all()

def list_company_pending_maintenances(db: Session, company_id: int):
    """Get pending maintenances for machines owned by a specific company"""
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    return db.query(models.Maintenance).join(models.Machine).filter(
        and_(
            models.Machine.company_id == company_id,
            models.Maintenance.scheduled_date.between(today, next_week),
            models.Maintenance.completed == False
        )
    ).all()