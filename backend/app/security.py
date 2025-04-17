import os
import logging
from dotenv import load_dotenv
from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional, Dict, Any
from . import models

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# IMPORTANT: Never use a default secret key in production. Always set SECRET_KEY in your environment.
SECRET_KEY = os.getenv("SECRET_KEY", "default_super_secret_key_replace_in_production")
if SECRET_KEY == "default_super_secret_key_replace_in_production":
    logger.warning("Using default secret key. Replace it with a secure value in production.")

ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Fallback to 30 minutes if the environment variable is not set
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_hash(password: str) -> str:
    """Generate a bcrypt hash from a plain text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if the plain text password matches the stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_token(payload: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token with the provided `payload`, expiring after `expires_delta`."""
    to_encode = payload.copy()
    expire_time = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire_time})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token. Returns the decoded payload if valid, or None if invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        logger.error(f"Token verification failed: {exc}")
        return None


def create_user_token(user: models.User, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT for the given user, including role and optional company information.
    Returns the signed JWT as a string.
    """
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "role": user.role,
    }
    if user.company_id:
        token_data["company_id"] = user.company_id

    return create_token(token_data, expires_delta=expires_delta)
