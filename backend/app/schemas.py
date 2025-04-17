from datetime import date
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, EmailStr

# Enums
class MachineTypeEnum(str, Enum):
    TRUCK = "truck"
    FIXED = "fixed"


class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    FLEET_MANAGER = "fleet_manager"


# User schemas
class UserBase(BaseModel):
    """
    Defines the base fields for a user entity.
    """
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRoleEnum] = UserRoleEnum.FLEET_MANAGER
    company_id: Optional[int] = None
    phone_number: Optional[str] = None
    notifications_enabled: Optional[bool] = True


class UserCreate(UserBase):
    """
    Schema used when creating a new user; includes password.
    """
    password: str


class UserUpdate(BaseModel):
    """
    Schema used for updating an existing user. Fields are optional.
    """
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRoleEnum] = None
    company_id: Optional[int] = None
    is_active: Optional[bool] = None
    phone_number: Optional[str] = None
    notifications_enabled: Optional[bool] = None


class User(UserBase):
    """
    Returns user data, including its ID and active status.
    """
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True


# Company schemas
class CompanyBase(BaseModel):
    """
    Defines the base fields for a company entity.
    """
    name: str
    address: Optional[str] = None
    logo_path: Optional[str] = None
    tax_id: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = "Portugal"
    billing_email: Optional[str] = None
    phone: Optional[str] = None
    payment_method: Optional[str] = None
    iban: Optional[str] = None

class CompanyCreate(CompanyBase):
    """
    Schema used when creating a new company.
    """
    pass

class CompanyUpdate(BaseModel):
    """
    Schema used for updating an existing company. Fields are optional.
    """
    name: Optional[str] = None
    address: Optional[str] = None
    logo_path: Optional[str] = None
    tax_id: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    billing_email: Optional[str] = None
    phone: Optional[str] = None
    payment_method: Optional[str] = None
    iban: Optional[str] = None


class Company(CompanyBase):
    """
    Returns company data with its ID.
    """
    id: int

    class Config:
        from_attributes = True


class CompanyDetail(Company):
    """
    Extended company schema, including a list of associated machines.
    """
    machines: List["Machine"] = []

    class Config:
        from_attributes = True


# Machine schemas
class MachineBase(BaseModel):
    """
    Defines the base fields for a machine entity.
    """
    name: str
    type: MachineTypeEnum
    company_id: int


class MachineCreate(MachineBase):
    """
    Schema used when creating a new machine.
    """
    pass


class MachineUpdate(BaseModel):
    """
    Schema used for updating an existing machine. Fields are optional.
    """
    name: Optional[str] = None
    type: Optional[MachineTypeEnum] = None
    company_id: Optional[int] = None


class Machine(MachineBase):
    """
    Returns machine data with its ID.
    """
    id: int

    class Config:
        from_attributes = True


# Maintenance schemas
class MaintenanceBase(BaseModel):
    """
    Defines the base fields for a maintenance entity.
    """
    machine_id: int
    type: str
    scheduled_date: date
    notes: Optional[str] = None


class MaintenanceCreate(MaintenanceBase):
    """
    Schema used when creating a new maintenance record.
    """
    pass


class MaintenanceUpdate(BaseModel):
    """
    Schema used for updating an existing maintenance record. Fields are optional.
    """
    type: Optional[str] = None
    scheduled_date: Optional[date] = None
    completed: Optional[bool] = None
    notes: Optional[str] = None


class Maintenance(MaintenanceBase):
    """
    Returns maintenance data with its ID and completion status.
    """
    id: int
    completed: bool = False

    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    """
    Represents a JWT-based token used for authentication.
    """
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
    company_id: Optional[int] = None


class TokenData(BaseModel):
    """
    Contains the key information that can be extracted from a token.
    """
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    company_id: Optional[int] = None


# Schemas para serviços
class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    unit_price: float
    tax_rate: float = 23.0
    is_active: bool = True

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[float] = None
    tax_rate: Optional[float] = None
    is_active: Optional[bool] = None

class Service(ServiceBase):
    id: int

    class Config:
        from_attributes = True

# Schemas para itens de fatura
class InvoiceItemBase(BaseModel):
    service_id: int
    machine_id: Optional[int] = None
    quantity: float = 1.0
    description: Optional[str] = None
    unit_price: Optional[float] = None  # Se não fornecido, usa o preço do serviço
    tax_rate: Optional[float] = None    # Se não fornecido, usa a taxa do serviço

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItemUpdate(BaseModel):
    service_id: Optional[int] = None
    machine_id: Optional[int] = None
    quantity: Optional[float] = None
    description: Optional[str] = None
    unit_price: Optional[float] = None
    tax_rate: Optional[float] = None

class InvoiceItem(InvoiceItemBase):
    id: int
    invoice_id: int
    subtotal: float
    tax_amount: float
    total: float
    unit_price: float
    tax_rate: float

    class Config:
        from_attributes = True

# Schemas para faturas
class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELED = "canceled"

class InvoiceBase(BaseModel):
    company_id: int
    issue_date: Optional[date] = None
    due_date: date
    notes: Optional[str] = None
    payment_method: Optional[str] = None
    status: InvoiceStatus = InvoiceStatus.DRAFT

class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]

class InvoiceUpdate(BaseModel):
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
    payment_method: Optional[str] = None
    status: Optional[InvoiceStatus] = None
    payment_date: Optional[date] = None

class Invoice(InvoiceBase):
    id: int
    invoice_number: str
    subtotal: float
    tax_total: float
    total: float
    payment_date: Optional[date] = None
    items: List[InvoiceItem]

    class Config:
        from_attributes = True