"""CRUD helpers for the Fleet Management back‑end."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_
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
    db_company = models.Company(**company.model_dump())
    db.add(db_company)
    _commit_refresh(db, db_company)
    return db_company


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
