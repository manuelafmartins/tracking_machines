import enum
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship

from .database import Base

class MachineTypeEnum(str, enum.Enum):
    """Defines machine types."""
    truck = "truck"
    fixed = "fixed"


class UserRoleEnum(str, enum.Enum):
    """Defines user roles."""
    admin = "admin"
    fleet_manager = "fleet_manager"


class User(Base):
    """Represents a system user with optional phone and notifications settings."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, index=True)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.fleet_manager)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    phone_number = Column(String(20), nullable=True)
    notifications_enabled = Column(Boolean, default=True)

    company = relationship("Company", back_populates="users")


class Company(Base):
    """Represents a company, including a list of machines and its users."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    
    # Campos existentes
    address = Column(String, nullable=True)
    logo_path = Column(String, nullable=True)
    
    # Novos campos para faturação
    tax_id = Column(String, nullable=True)   
    postal_code = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True, default="Portugal")
    billing_email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    iban = Column(String, nullable=True)

    machines = relationship(
        "Machine",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    users = relationship(
        "User",
        back_populates="company"
    )


class Machine(Base):
    """Represents a machine associated with a company."""
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(Enum(MachineTypeEnum), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"))

    company = relationship("Company", back_populates="machines")
    maintenances = relationship(
        "Maintenance",
        back_populates="machine",
        cascade="all, delete-orphan"
    )


class Maintenance(Base):
    """Represents a maintenance record for a machine."""
    __tablename__ = "maintenances"

    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    type = Column(String, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)
    notes = Column(String, nullable=True)

    machine = relationship("Machine", back_populates="maintenances")
