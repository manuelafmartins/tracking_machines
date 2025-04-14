# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from . import models, schemas
from .security import generate_hash
from datetime import datetime, timedelta
from typing import List, Optional

# --- COMPANY CRUD ---
def get_companies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Company).offset(skip).limit(limit).all()

def get_company_by_id(db: Session, company_id: int):
    return db.query(models.Company).filter(models.Company.id == company_id).first()

def create_company(db: Session, company: schemas.CompanyCreate):
    db_company = models.Company(name=company.name)
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

# --- MACHINE CRUD ---
def get_machines(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Machine).offset(skip).limit(limit).all()

def get_machine_by_id(db: Session, machine_id: int):
    return db.query(models.Machine).filter(models.Machine.id == machine_id).first()

def get_machines_by_company(db: Session, company_id: int):
    return db.query(models.Machine).filter(models.Machine.company_id == company_id).all()

def create_machine(db: Session, machine: schemas.MachineCreate):
    db_machine = models.Machine(**machine.dict())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine

# --- MAINTENANCE CRUD ---
def get_maintenances(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Maintenance).offset(skip).limit(limit).all()

def get_maintenance_by_id(db: Session, maintenance_id: int):
    return db.query(models.Maintenance).filter(models.Maintenance.id == maintenance_id).first()

def get_machine_maintenances(db: Session, machine_id: int):
    return db.query(models.Maintenance).filter(models.Maintenance.machine_id == machine_id).all()

def create_maintenance(db: Session, maintenance: schemas.MaintenanceCreate):
    db_maintenance = models.Maintenance(**maintenance.dict())
    db.add(db_maintenance)
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

# --- USER CRUD ---
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate, is_admin: bool = False):
    hashed_password = generate_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password, is_admin=is_admin)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user