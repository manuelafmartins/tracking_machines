# create_admin.py
from .database import SessionLocal
from .crud import get_user_by_username, create_user
from .schemas import UserCreate
import logging

# Configure logging
logger = logging.getLogger(__name__)

def create_admin_user():
    """
    Create admin user if it doesn't exist
    """
    db = SessionLocal()
    try:
        # Check if admin user already exists
        existing_admin = get_user_by_username(db, "admin")
        if existing_admin:
            logger.info("Admin user already exists")
            return True
            
        # Create new admin user
        user_data = UserCreate(username="admin", password="admin123")
        create_user(db, user_data, is_admin=True)
        logger.info("Admin user created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        return False
    finally:
        db.close()