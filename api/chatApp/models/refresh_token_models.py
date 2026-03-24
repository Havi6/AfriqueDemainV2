from sqlalchemy import Column, String, DateTime
from datetime import datetime
from api.settings.database import Base

class RefreshToken(Base):
    __tablename__ = "refresh_token"
    jti = Column(String(255), nullable=False)
    refresh_token = Column(String(255), nullable=False)
    token_type = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now())