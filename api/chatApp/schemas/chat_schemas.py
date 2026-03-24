from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class RoomCreate(BaseModel):
    name: str

class MessageOut(BaseModel):
    id: int
    from_user: str
    to: Optional[str]
    room: Optional[str]
    msg: Optional[str]
    ts: datetime

class FileMetaIn(BaseModel):
    filename: str
    size: Optional[int]
    room: Optional[str]
    to: Optional[str]

class AnnouncementSchemas(BaseModel):
    title: str
    image: Optional[str]
    description: str
    sender: str
    send_at: datetime
