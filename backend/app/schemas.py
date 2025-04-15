# schemas.py
from pydantic import BaseModel, EmailStr
from datetime import date
from enum import Enum
from typing import Optional, List

# Enums
class MachineTypeEnum(str, Enum):
    TRUCK = "truck"
    FIXED = "fixed"

class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    FLEET_MANAGER = "fleet_manager"

# User schemas
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRoleEnum] = UserRoleEnum.FLEET_MANAGER
    company_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRoleEnum] = None
    company_id: Optional[int] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool = True
    
    class Config:
        from_attributes = True

# Company
class CompanyBase(BaseModel):
    name: str
    address: Optional[str] = None
    logo_path: Optional[str] = None  

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    logo_path: Optional[str] = None  

class Company(CompanyBase):
    id: int
    
    class Config:
        from_attributes = True

class CompanyDetail(Company):
    machines: List["Machine"] = []
    
    class Config:
        from_attributes = True

# Machine
class MachineBase(BaseModel):
    name: str
    type: MachineTypeEnum
    company_id: int

class MachineCreate(MachineBase):
    pass

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[MachineTypeEnum] = None
    company_id: Optional[int] = None

class Machine(MachineBase):
    id: int

    class Config:
        from_attributes = True

# Maintenance
class MaintenanceBase(BaseModel):
    machine_id: int
    type: str
    scheduled_date: date
    notes: Optional[str] = None

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceUpdate(BaseModel):
    type: Optional[str] = None
    scheduled_date: Optional[date] = None
    completed: Optional[bool] = None
    notes: Optional[str] = None

class Maintenance(MaintenanceBase):
    id: int
    completed: bool = False

    class Config:
        from_attributes = True

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
    company_id: Optional[int] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    company_id: Optional[int] = None