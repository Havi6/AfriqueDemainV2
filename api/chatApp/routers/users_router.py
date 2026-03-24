from fastapi import APIRouter, Depends, HTTPException
import api
from api.settings.database import get_db
from api.chatApp.models.users_models import User, RefreshToken
from api.chatApp.schemas.token_schemas import Token, RefreshTokenSchemas
from api.chatApp.schemas.users_schemas import Users, UserCreate, UserResponse, UserUpdate, UsersLogin
from sqlalchemy.orm import Session
from api.chatApp.utils import hash_password, create_access_token, verify_password, get_current_user, create_refresh_token, \
    decode_token

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/admin_list", response_model=list[UserResponse])
async def read_users(skip: int=0, limit: int=10, db: Session = Depends(get_db), admin: api.chatApp.models.users_models.User = Depends(get_current_user)):
    users = db.query(User).filter("admin" == api.chatApp.models.users_models.User.role).offset(skip).limit(limit).all()
    return users



@router.post("/register", response_model=UserCreate)
async def create_user(user: Users, db: Session = Depends(get_db)):
    db_user = User(username=user.username, email=user.email, password_hash=hash_password(user.password_hash))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/user_update")
async def update_user(user: api.chatApp.models.users_models.User = Depends(get_current_user), db: Session = Depends(get_db), form_data: UserUpdate = None):
    db_user = db.query(api.chatApp.models.users_models.User).filter(
        api.chatApp.models.users_models.User.email == user.email).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="utilisateur non trouvé")
    
    db_user.username = form_data.username if form_data.username is not None else db_user.username
    db_user.password_hash = hash_password(form_data.password_hash) if form_data.password_hash is not None else db_user.password_hash
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
async def login_for_token(form_data: UsersLogin, db: Session = Depends(get_db)):
    user = db.query(api.chatApp.models.users_models.User).filter(
        api.chatApp.models.users_models.User.email == form_data.email).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    accesstoken = create_access_token({"user": user.username, "role": user.role})
    refreshtoken = create_refresh_token({"user": user.username, "role": user.role})
    payload = decode_token(refreshtoken)
    token = RefreshToken(**payload)
    try:
        if not db.query(api.chatApp.models.users_models.RefreshToken).filter(
                api.chatApp.models.users_models.RefreshToken == payload.get("jti")).first():
            db.add(token)
            db.commit()
    finally:
        db.close()
    return {"access_token": accesstoken,"refresh_token": refreshtoken}

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: api.chatApp.models.users_models.User = Depends(get_current_user), db: Session = Depends(get_db), form_data: RefreshTokenSchemas = None):
    user = current_user
    payload = decode_token(form_data.refresh_token)
    token = db.query(api.chatApp.models.users_models.RefreshToken).filter(
        api.chatApp.models.users_models.RefreshToken.jti == payload.get("jti")).first()
    if not token or current_user.username != token.user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    db.delete(token); db.commit()
    accesstoken = create_access_token({"user": user.username, "role": user.role})
    refreshtoken = create_refresh_token({"user": user.username, "role": user.role})
    return {"access_token": accesstoken,"refresh_token": refreshtoken}

@router.post("/change_password")
async def change_password(new_password: str, current_user: api.chatApp.models.users_models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.password_hash = hash_password(new_password)
    db.add(current_user); db.commit()
    return {"msg": "password changed"}

@router.post("/delete_account")
def delete_account(current_user: api.chatApp.models.users_models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(current_user); db.commit()
    return {"msg": "account deleted"}

