from fastapi import FastAPI
from api.settings.database import init_db
from api.chatApp.routers import users_router, admin_router, chat_router, file_router
import api.chatApp.models.users_models as models
from api.chatApp.utils import hash_password
from sqlalchemy.orm import  Session
from api.settings.database import SessionLocal
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

#création des tables de la db et initialisation des routes
init_db()
app.include_router(users_router.router)
app.include_router(admin_router.router)
app.include_router(chat_router.router)
app.include_router(file_router.router)

#configuration du midelware
origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#creation du superutilisateur
def create_superuser():
    db: Session = SessionLocal()
    try:
        if not db.query(models.User).filter("superadmin" == models.User.role).first():
            su = models.User(username="Havi",email="havidu6@gmail.com", password_hash=hash_password("havi6"), role="superadmin")
            db.add(su)
            db.commit()
    finally:
        db.close()

create_superuser()

@app.get("/")
def read_root():
    return {"message" : "your are connected successfully"}