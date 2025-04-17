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
