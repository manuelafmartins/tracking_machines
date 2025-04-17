import enum
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
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

    invoices = relationship(
        "Invoice",
        back_populates="company",
        cascade="all, delete-orphan"
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

    invoice_items = relationship(
        "InvoiceItem",
        back_populates="machine"
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



class InvoiceStatus(str, enum.Enum):
    """Define os estados possíveis de uma fatura."""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELED = "canceled"


class Service(Base):
    """Representa um serviço que pode ser incluído em faturas."""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    unit_price = Column(Float, nullable=False)
    tax_rate = Column(Float, default=23.0)  # IVA padrão em Portugal
    is_active = Column(Boolean, default=True)

    # Relacionamento com os itens de fatura
    invoice_items = relationship("InvoiceItem", back_populates="service")


class Invoice(Base):
    """Representa uma fatura emitida para uma empresa."""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    invoice_number = Column(String, unique=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    issue_date = Column(Date, nullable=False, default=lambda: datetime.now().date())
    due_date = Column(Date, nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    
    # Valores calculados
    subtotal = Column(Float, default=0.0)
    tax_total = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    
    # Informações adicionais
    notes = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    payment_date = Column(Date, nullable=True)
    
    # Relacionamentos
    company = relationship("Company", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    """Representa um item individual em uma fatura."""
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False)
    tax_rate = Column(Float, nullable=False)
    
    # Valores calculados
    subtotal = Column(Float, nullable=False)  # quantity * unit_price
    tax_amount = Column(Float, nullable=False)  # subtotal * (tax_rate/100)
    total = Column(Float, nullable=False)  # subtotal + tax_amount
    
    # Descrição customizada (caso seja diferente do serviço base)
    description = Column(String, nullable=True)
    
    # Relacionamentos
    invoice = relationship("Invoice", back_populates="items")
    service = relationship("Service", back_populates="invoice_items")
    machine = relationship("Machine", back_populates="invoice_items")