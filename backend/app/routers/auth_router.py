# backend/app/routers/auth_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from .. import database, crud, schemas
from ..security import verificar_password, criar_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(tags=["auth"], prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not verificar_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Definir tempo de expiração do token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Criar payload do token
    token_data = {"sub": user.username}
    
    # Gerar o token JWT
    access_token = criar_token(token_data, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer"}