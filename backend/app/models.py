# models.py
import enum
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class MachineTypeEnum(str, enum.Enum):
    truck = "truck"
    fixed = "fixed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    machines = relationship("Machine", back_populates="company")


class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(Enum(MachineTypeEnum), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"))
    company = relationship("Company", back_populates="machines")
    maintenances = relationship("Maintenance", back_populates="machine")


class Maintenance(Base):
    __tablename__ = "maintenances"
    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    type = Column(String, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)
    machine = relationship("Machine", back_populates="maintenances")