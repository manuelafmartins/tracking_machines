# create_admin.py
from .database import SessionLocal
from .crud import create_user
from .schemas import UserCreate

def create_admin_user():
    """
    Create admin user if it doesn't exist
    """
    db = SessionLocal()
    try:
        user_data = UserCreate(username="admin", password="admin123")
        create_user(db, user_data, is_admin=True)
        return True
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if create_admin_user():
        print("Admin user created successfully!")
    else:
        print("Failed to create admin user.")