# backend/app/create_main_admin.py
from .database import SessionLocal
from .crud import get_user_by_username, create_user
from .schemas import UserCreate
from .models import UserRoleEnum
import logging

# Configure logging
logger = logging.getLogger(__name__)

def create_main_admin():
    """
    Create the main administrator (Filipe Ferreira) if it doesn't exist
    """
    db = SessionLocal()
    try:
        # Check if main admin user already exists
        existing_admin = get_user_by_username(db, "filipe.ferreira")
        if existing_admin:
            logger.info("Main administrator (Filipe Ferreira) already exists")
            return True
            
        # Create new admin user
        user_data = UserCreate(
            username="filipe.ferreira",
            password="Mafmafm563895",  # Will be hashed
            email="filipe.ferreira@fleetpilot.com",
            full_name="Filipe Ferreira",
            role=UserRoleEnum.admin
        )
        
        create_user(db, user_data, UserRoleEnum.admin)
        logger.info("Main administrator (Filipe Ferreira) created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating main administrator: {str(e)}")
        return False
    finally:
        db.close()