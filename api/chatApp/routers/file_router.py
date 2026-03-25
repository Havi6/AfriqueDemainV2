from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette.responses import FileResponse
import os
from fastapi import  UploadFile, File, Form, HTTPException, APIRouter
from api.chatApp import models
from api.chatApp.models.chat_models import FileMeta
from api.chatApp.schemas.file_schemas import ImageMeta
from api.chatApp.utils import get_current_user
from api.settings.database import get_db

router = APIRouter(prefix="/file", tags=["file gestion"])

BASE_DIR = "./uploads"
DIR = {
    "video": os.path.join(BASE_DIR, "video"),
    "pdf": os.path.join(BASE_DIR, "pdf"),
    "image": os.path.join(BASE_DIR, "image"),
    "audio": os.path.join(BASE_DIR, "audio"),
}


#Extentions autorisées
CATEGORIES = ["audio", "video", "image", "pdf"]

VIDEO_EXT =  [".mp4", ".avi", ".mkv"]
PDF_EXT = [".pdf"]
IMG_EXT = [".jpg", ".jpeg", ".png"]
AUDIO_EXT = [".mp3", ".wav", ".flac", ".ogg", ".m4a"]





@router.post("/upload-file")
async def upload_file(
        file: UploadFile = File(...),
        title: str = Form(...),
        description: str = Form(None),
        db: Session = Depends(get_db),
        user: models.users_models.User = Depends(get_current_user)
):
    # construction des répertoires
    for d in DIR.values():
        os.makedirs(d, exist_ok=True)

    content = await file.read()
    #recupération de l'extention
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()


    # choix du répertoire en fonction de l'extension
    if ext in VIDEO_EXT:
        target_dir = DIR["video"]
    elif ext in PDF_EXT:
        target_dir = DIR["pdf"]
    elif ext in IMG_EXT:
        target_dir = DIR["image"]
    elif ext in AUDIO_EXT:
        target_dir = DIR["audio"]
    else:
        raise HTTPException(status_code=400, detail=f"extention non supportée")

    # construction du chemin final
    file_path = os.path.join(target_dir, file.filename)


    with open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    file = FileMeta(filename=title ,uploader=user.username, size=len(content),path= file_path, description=description )
    db.add(file)
    db.commit()
    db.refresh(file)

    return file

@router.get("/download/{category}/{filename}")
async def download_file(category: str, filename: str, db: Session = Depends(get_db)):
    file = db.query(FileMeta).filter(FileMeta.filename == filename).first()

    if category not in CATEGORIES or not file:
        raise HTTPException(status_code=400, detail="mauvaise catégorie ou fichier inexistant")

    file_path = file.path

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"le fichier {filename} n'a pas été trouvé")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type = "application/octet-stream",
    )

@router.get("/list_file/{category}")
async def list_files(category: str):
    if category not in CATEGORIES:
        raise HTTPException(status_code=400, detail="mauvaise catégorie")

    dir_path = os.path.join(BASE_DIR, category)
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail="répertoire introuvable")

    files = os.listdir(dir_path)
    return {"categories": category, "files": files}
