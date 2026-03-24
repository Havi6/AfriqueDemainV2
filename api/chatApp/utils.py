import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from api.settings.config import ACCESS_TOKEN_EXPIRE_HOURS, SECRET_KEY, ALGORITHM
from api.settings.database import get_db
from api.chatApp import models

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"type": "access"})
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    jti = str(uuid.uuid4())
    to_encode = data.copy()
    to_encode.update({"jti": jti})
    to_encode.update({"type": "refresh"})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Token invalide ou expiré")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db),):
    payload = decode_token(token)
    username = payload.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = db.query(models.users_models.User).filter(models.users_models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user

def require_roles(*roles):
    def _require(user: models.users_models.User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Permission refusée")
        return user
    return _require

def require_admin_roles(*roles):
    def _require(user: models.users_models.User = Depends(get_current_user)):
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Uniquement pour admin")
        return user
    return _require


def require_super_roles(user: models.users_models.User = Depends(get_current_user)):
    if user.role != "superuser":
        raise HTTPException(status_code=403, detail="Uniquement pour superuser")
    return user
