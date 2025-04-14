# security.py
import os
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional, Dict, Any
from . import models

load_dotenv()  # Load .env variables

SECRET_KEY = os.getenv("SECRET_KEY", "default_super_secret_key_replace_in_production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_hash(password: str) -> str:
    """Generate bcrypt hash from plain password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify if plain password matches stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token with payload `data`, expiring after `expires_delta`."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def create_user_token(user: models.User) -> Dict[str, Any]:
    """Create a token for the user with role and company information"""
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "role": user.role,
    }
    
    # Add company_id only if it exists
    if user.company_id:
        token_data["company_id"] = user.company_id
        
    return token_data