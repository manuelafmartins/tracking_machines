# dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional

from . import crud, database, models, schemas
from .security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        token_data = schemas.TokenData(
            username=username,
            user_id=payload.get("user_id"),
            role=payload.get("role"),
            company_id=payload.get("company_id")
        )
    except JWTError:
        raise credentials_exception
        
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
        
    return user

def get_admin_user(current_user: models.User = Depends(get_current_user)):
    """Dependency for admin-only endpoints"""
    if current_user.role != models.UserRoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user

def get_company_access(
    company_id: int, 
    current_user: models.User = Depends(get_current_user)
):
    """Verify if the user has access to a specific company"""
    # Admin has access to all companies
    if current_user.role == models.UserRoleEnum.admin:
        return True
    
    # Fleet manager has access only to their company
    if current_user.company_id == company_id:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have access to this company"
    )

def get_resource_company_id(
    resource_id: int, 
    resource_type: str,
    db: Session = Depends(database.get_db)
):
    """Get the company_id associated with a resource (machine or maintenance)"""
    if resource_type == "machine":
        resource = crud.get_machine_by_id(db, resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Machine not found"
            )
        return resource.company_id
    
    elif resource_type == "maintenance":
        resource = crud.get_maintenance_by_id(db, resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Maintenance not found"
            )
        return resource.machine.company_id
    
    raise ValueError(f"Invalid resource type: {resource_type}")

def check_machine_access(
    machine_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Check if user has access to a specific machine"""
    company_id = get_resource_company_id(machine_id, "machine", db)
    get_company_access(company_id, current_user)
    return True

def check_maintenance_access(
    maintenance_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Check if user has access to a specific maintenance"""
    company_id = get_resource_company_id(maintenance_id, "maintenance", db)
    get_company_access(company_id, current_user)
    return True