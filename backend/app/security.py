from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

SECRET_KEY = "chave_secreta_muito_segura"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def gerar_hash(password: str):
    return pwd_context.hash(password)

def verificar_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

def criar_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        exp = datetime.utcnow() + expires_delta
    else:
        exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": exp})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
