from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from api.settings.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(), unique=True, nullable=False, index=True)
    email = Column(String(), unique = True, nullable=False, index= True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(), default="user", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class RefreshToken(Base):
    __tablename__ = "refresh_token"
    id = Column(Integer, primary_key=True, index=True)
    user = Column(String(), nullable=False, index=True)
    jti = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now())