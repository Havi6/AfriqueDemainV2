from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, constr
from datetime import datetime

class Users(BaseModel):
    username: str
    email: EmailStr
    password_hash: str

class UsersLogin(BaseModel):
    email: EmailStr
    password: str
    
class UserCreate(BaseModel):
    id: int
    username: str
    email: EmailStr
    password_hash: str
    role: Optional[Literal["user", "admin", "superadmin"]] = "user"
    created_at: datetime

class UserResponse(BaseModel):
    username: str
    email: str
    role: Optional[Literal["user", "admin", "superadmin"]]
    created_at: datetime
    
class UserUpdate(BaseModel):
    username: Optional[str]
    password_hash: Optional[str]
    
class RoleUpdate(BaseModel):
    role: Literal["user", "admin", "superadmin"]