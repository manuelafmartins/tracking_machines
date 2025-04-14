# create_admin.py
from .database import SessionLocal
from .crud import create_user
from .schemas import UserCreate

def criar_usuario_admin():
    db = SessionLocal()
    user_data = UserCreate(username="admin", password="admin123")
    create_user(db, user_data)
    db.close()

if __name__ == "__main__":
    criar_usuario_admin()
    print("Admin user created!")

