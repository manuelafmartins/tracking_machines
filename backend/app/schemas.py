# schemas.py
from pydantic import BaseModel
from datetime import date
from enum import Enum

# Machine type enum for Pydantic
class MachineTypeEnum(str, Enum):
    TRUCK = "truck"
    FIXED = "fixed"

# Company
class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int

    class Config:
        orm_mode = True

# Machine
class MachineBase(BaseModel):
    name: str
    type: MachineTypeEnum
    company_id: int

class MachineCreate(MachineBase):
    pass

class Machine(MachineBase):
    id: int

    class Config:
        orm_mode = True

# Maintenance
class MaintenanceBase(BaseModel):
    machine_id: int
    type: str
    scheduled_date: date

class MaintenanceCreate(MaintenanceBase):
    pass

class Maintenance(MaintenanceBase):
    id: int
    completed: bool = False

    class Config:
        orm_mode = True

# User schemas
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_admin: bool = False
    
    class Config:
        orm_mode = True

# Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None