import logging
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import database, crud, schemas, models
from ..security import (
    verify_password,
    create_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_user_token
)
from ..dependencies import get_admin_user, get_current_user
from ..notifications import notify_new_user_created
from ..crud import get_company_by_id

# Configure router
router = APIRouter(tags=["authentication"], prefix="/auth")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db)
):
    """
    Authenticate a user and return an access token.
    
    Args:
        form_data: OAuth2 form with username and password
        db: Database session
        
    Returns:
        Token information including access token and user details
        
    Raises:
        HTTPException: If credentials are invalid or user is inactive
    """
    # Verify user credentials
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Generate token with appropriate expiration
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = create_user_token(user)
    access_token = create_token(token_data, expires_delta=access_token_expires)
    
    # Return token with user information
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "company_id": user.company_id
    }


@router.get("/users/me", response_model=schemas.User)
def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """
    Returns information about the currently logged-in user.
    
    Args:
        current_user: User extracted from token
        
    Returns:
        User information
    """
    return current_user


@router.get("/users", response_model=List[schemas.User])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)
):
    """
    Retrieves all users (admin only).
    
    Args:
        skip: Number of users to skip for pagination
        limit: Maximum number of users to return
        db: Database session
        current_user: Current user (must be admin)
        
    Returns:
        List of users
    """
    return crud.get_users(db, skip=skip, limit=limit)


@router.post("/users", response_model=schemas.User)
def create_new_user(
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_admin_user)
):
    """
    Creates a new user (admin only).
    
    Args:
        user: User data to create
        db: Database session
        current_user: Current user (must be admin)
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If username already exists
    """
    # Check if username already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Create new user
    new_user = crud.create_user(db=db, user=user, role=user.role)

    # Include company name if the new user is a fleet manager
    company_name = None
    if user.role == models.UserRoleEnum.fleet_manager and user.company_id:
        company = get_company_by_id(db, user.company_id)
        company_name = company.name if company else None

    # Send notification (ignore any failures)
    try:
        role_display = "Administrator" if user.role == models.UserRoleEnum.admin else "Fleet Manager"
        notify_new_user_created(
            db,
            username=user.username,
            role=role_display,
            company_name=company_name
        )
    except Exception as e:
        logging.error(f"Failed to send user creation notification: {e}")

    return new_user


@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Updates user information. 
    Only admins can update other users or change roles.
    
    Args:
        user_id: ID of user to update
        user_data: User data to update
        db: Database session
        current_user: Current user
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If user not found or insufficient permissions
    """
    # Check permissions
    if current_user.id != user_id and current_user.role != models.UserRoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update other users"
        )

    # Only admins can change roles
    if user_data.role is not None and current_user.role != models.UserRoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to change roles"
        )

    # Update user
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
    """
    Deletes a user (admin only).
    
    Args:
        user_id: ID of user to delete
        db: Database session
        current_user: Current user (must be admin)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found or trying to delete own account
    """
    # Prevent self-deletion
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )

    # Delete user
    result = crud.delete_user(db, user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"success": True, "message": "User deleted successfully"}