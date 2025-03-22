from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, users, database, auth, security

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/register")
def registar_user(data: schemas.UserCreate, db: Session = Depends(database.SessionLocal)):
    return users.criar_utilizador(db, data.username, data.password)

@router.post("/login", response_model=schemas.Token)
def login_user(data: schemas.UserLogin, db: Session = Depends(database.SessionLocal)):
    user = auth.autenticar_utilizador(data.username, data.password, db)
    token = security.criar_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
