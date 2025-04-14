# models.py
import enum
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class MachineTypeEnum(str, enum.Enum):
    truck = "truck"
    fixed = "fixed"


class UserRoleEnum(str, enum.Enum):
    admin = "admin"             # Main administrator with full access
    fleet_manager = "fleet_manager"  # Company-specific manager


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, index=True)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.fleet_manager)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationship with Company
    company = relationship("Company", back_populates="users")


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    address = Column(String, nullable=True)
    machines = relationship("Machine", back_populates="company", cascade="all, delete-orphan")
    users = relationship("User", back_populates="company")


class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(Enum(MachineTypeEnum), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"))
    company = relationship("Company", back_populates="machines")
    maintenances = relationship("Maintenance", back_populates="machine", cascade="all, delete-orphan")


class Maintenance(Base):
    __tablename__ = "maintenances"
    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    type = Column(String, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)
    notes = Column(String, nullable=True)
    machine = relationship("Machine", back_populates="maintenances")