from typing import Union
from fastapi import APIRouter, Depends, HTTPException
from api.settings.database import get_db
from api.chatApp.models.users_models import User
from api.chatApp.models.chat_models import FileMeta
from api.chatApp.schemas.users_schemas import  UserResponse,  RoleUpdate
from sqlalchemy.orm import Session
from api.chatApp.utils import get_current_user
import api

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users_list", response_model=list[UserResponse])
async def read_users(skip: int=0, limit: int=10, db: Session = Depends(get_db), admin: api.chatApp.models.users_models.User = Depends(get_current_user)):
    if admin.role == "user":
        raise HTTPException(status_code=403, detail="non authorisé")
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/user_details/{user_id}")
async def get_user_by_id(user_id: int, db: Session = Depends(get_db), admin: api.chatApp.models.users_models.User = Depends(get_current_user)):
    if admin.role == "user":
        raise HTTPException(status_code=403, detail="non authorisé")
    user = db.query(User).filter(user_id == User.id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="utilisateur non trouvé")
    return user

@router.put("/role_update/{user_id}")
async def update_role(user_id: int, user: RoleUpdate, db: Session = Depends(get_db), admin: api.chatApp.models.users_models.User = Depends(get_current_user)):
    if admin.role != "superuser":
        raise HTTPException(status_code=403, detail="non authorisé")
    db_user = db.query(User).filter(user_id == User.id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="utilisateur non trouvé")
    db_user.role = user.role if user.role is not None else db_user.role
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/delete_user/{user_id}", response_model=UserResponse)
async def delete_user(user_id: int, db: Session = Depends(get_db), admin: api.chatApp.models.users_models.User = Depends(get_current_user)):
    if admin.role != "superuser":
        raise HTTPException(status_code=403, detail="non authorisé")
    db_user = db.query(User).filter(user_id == User.id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="utilisateur non trouvé")
    db.delete(db_user)
    db.commit()
    return db_user

@router.get("/search_users", response_model=list[UserResponse])
async def search_users(
        username: Union[str, None] = None,
        role: Union[str, None] = None,
        db: Session = Depends(get_db),
        admin: api.chatApp.models.users_models.User = Depends(get_current_user),
):

    if admin.role == "user":
        raise HTTPException(status_code=403, detail="non authorisé")

    filtered_list = []
    users = db.query(User).all()

    # filtrage des utilisateurs
    if username is not None:
        for user in users:
            if user.username == username:
                filtered_list.append(user)

    # filtrage par role
    if role is not None:
        tmp = filtered_list if filtered_list else users
        new = []

        for user in tmp:
            if user.role == role:
                new.append(user)

        filtered_list = new

    if filtered_list:
        return filtered_list
    else:
        raise HTTPException(status_code=404, detail="Aucune taches ne correspond")



@router.get("/files_list")
async def list_files(db: Session = Depends(get_db)):
    files = db.query(FileMeta).all()

    return files

