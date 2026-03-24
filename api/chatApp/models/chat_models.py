from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from api.settings.database import Base


class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)
    created_by = Column(String(80))
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String(80), nullable=False)
    recipient = Column(String(80), nullable=True)  # null => room message
    room = Column(String(120), nullable=True)
    content = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class FileMeta(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    uploader = Column(String(80), nullable=False)
    room = Column(String(120), nullable=True)
    recipient = Column(String(80), nullable=True)
    size = Column(Integer, nullable=True)
    path = Column(String(512), nullable=True)  # optional server path
    created_at = Column(DateTime, default=datetime.utcnow)

class AnnouncementModels(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String(80), nullable=False)
    title = Column(String(80), nullable=False)
    image = Column(String(512), nullable=True, default=None)
    description = Column(Text, nullable=True)
    send_at = Column(DateTime, default=datetime.utcnow)