# routers/auth_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from .. import database, crud, schemas, models
from ..security import verify_password, create_token, ACCESS_TOKEN_EXPIRE_MINUTES, create_user_token
from ..dependencies import get_admin_user, get_current_user

router = APIRouter(tags=["authentication"], prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Set token expiration time
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Create token payload with user info
    token_data = create_user_token(user)
    
    # Generate JWT token
    access_token = create_token(token_data, expires_delta=access_token_expires)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "company_id": user.company_id
    }

@router.get("/users/me", response_model=schemas.User)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """Get current logged in user information"""
    return current_user

@router.get("/users", response_model=List[schemas.User])
def get_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)
):
    """Get all users (admin only)"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.post("/users", response_model=schemas.User)
def create_new_user(
    user: schemas.UserCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)
):
    """Create a new user (admin only)"""
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    return crud.create_user(db=db, user=user, role=user.role)

@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update user information"""
    # Only admins can update other users or change roles
    if current_user.id != user_id and current_user.role != models.UserRoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update other users"
        )
    
    # Only admin can change roles
    if user_data.role is not None and current_user.role != models.UserRoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to change roles"
        )
    
    updated_user = crud.update_user(db, user_id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user

@router.delete("/users/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)
):
    """Delete a user (admin only)"""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    
    result = crud.delete_user(db, user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"success": True, "message": "User deleted successfully"}