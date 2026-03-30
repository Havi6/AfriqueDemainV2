from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.params import Depends, Query
from sqlalchemy.orm import Session
import api
from api.chatApp.models import chat_models as models
from api.chatApp.models.chat_models import AnnouncementModels
from api.chatApp.models.chat_models import Message, Room
from api.chatApp.models.users_models import User
from api.chatApp.schemas.chat_schemas import AnnouncementSchemas
from api.chatApp.utils import decode_token, get_current_user
from api.settings.database import SessionLocal, get_db

router = APIRouter(prefix="/chat", tags=["chat"])

class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}
        self.room_members: Dict[str, List[str]] = {}  # optional membership

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active.setdefault(username, []).append(websocket)
        await websocket.send_text("connecté")

    def disconnect(self, websocket: WebSocket, username: str):
        conns = self.active.get(username, [])
        if websocket in conns:
            conns.remove(websocket)
            if not conns:
                del self.active[username]

    async def send_personal(self, username: str, message: dict):
        for ws in self.active.get(username, []):
            await ws.send_json(message)

    async def broadcast_room(self, room: str, message: dict):
        members = self.room_members.get(room, list(self.active.keys()))
        for u in members:
            for ws in self.active.get(u, []):
                await ws.send_json(message)

    async def broadcast_all(self, message: dict):
        for conns in self.active.values():
            for ws in conns:
                await ws.send_json(message)

manager = ConnectionManager()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    #token = websocket.query_params.get("token")
    if not decode_token(token):
        await websocket.close(code=1008)
        return

    try:
        payload = decode_token(token)
        username = payload.get("user")
    except TypeError:
        await websocket.close(code=1008)
        return


    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_json()
            t = data.get("type")
            db = SessionLocal()
            if t == "room":
                room = data.get("room")
                msg = data.get("msg")
                m = models.Message(sender=username, room=room, content=msg)
                db.add(m); db.commit()
                await manager.broadcast_room(room, {"type":"room_message","room":room,"from":username,"msg":msg,"ts":str(m.timestamp)})
            elif t == "announcement":
                role = payload.get("role")
                if role not in ["admin", "superuser"]:
                    raise HTTPException(status_code=403)

                title = data.get("title")
                img = data.get("image")
                desc = data.get("description")
                m = models.AnnouncementModels(sender= username, description= desc, title= title, image= img)
                db.add(m); db.commit()
                await  manager.broadcast_all({"type":"announcement", "from":username, "desc":desc,"title":title,"img":img})
            elif t == "private_message":
                to = data.get("to")
                msg = data.get("msg")
                recipient = db.query(User).filter(User.username == to).first()

                if not recipient:
                    raise HTTPException(status_code=404, detail="utilisateurs non éxistant")

                m = models.Message(sender=username, recipient=to, content=msg)
                db.add(m); db.commit()
                await manager.send_personal(to, {"type":"private_message","from":username,"to":to,"msg":msg,"ts":str(m.timestamp)})
                await manager.send_personal(username, {"type":"private_message","from":username,"to":to,"msg":msg,"ts":str(m.timestamp)})
            elif t == "create_room":
                role = payload.get("role")
                name = data.get("room")
                if role not in ["admin", "superadmin"]:
                    await websocket.send_json({"type":"system","msg":"Permission refusée: admin requis"})
                    continue
                if not name:
                    await websocket.send_json({"type":"system","msg":"Nom de room requis"})
                    continue
                if db.query(models.Room).filter(models.Room.name==name).first():
                    await websocket.send_json({"type":"system","msg":f"Room {name} existe déjà"})
                    continue
                r = models.Room(name=name, created_by=username)
                db.add(r); db.commit()
                await manager.broadcast_all({"type":"room_created","name":name,"by":username})
            elif t == "file_start":
                fm = models.FileMeta(filename=data.get("filename"), uploader=username, size=data.get("size"), room=data.get("room"), recipient=data.get("to"))
                db.add(fm); db.commit()
                file_id = fm.id
                if fm.recipient:
                    await manager.send_personal(fm.recipient, {"type":"file_started","file_id":file_id,"filename":fm.filename,"from":username})
                else:
                    await manager.broadcast_all({"type":"file_started","file_id":file_id,"filename":fm.filename,"from":username})
            elif t == "file_chunk":
                payload_msg = {"type":"file_chunk","file_id":data.get("file_id"),"chunk":data.get("chunk"),"from":username}
                to = data.get("to"); room = data.get("room")
                if to:
                    await manager.send_personal(to, payload_msg)
                elif room:
                    await manager.broadcast_room(room, payload_msg)
                else:
                    await manager.broadcast_all(payload_msg)
            elif t == "file_end":
                payload_msg = {"type":"file_complete","file_id":data.get("file_id"),"from":username}
                to = data.get("to"); room = data.get("room")
                if to:
                    await manager.send_personal(to, payload_msg)
                elif room:
                    await manager.broadcast_room(room, payload_msg)
                else:
                    await manager.broadcast_all(payload_msg)
            db.close()
    except WebSocketDisconnect:
        manager.disconnect(websocket, username)

@router.post("/announcement", response_model= AnnouncementSchemas)
async def post_announcement(desc: str, title: str, db: Session = Depends(get_db)):
    announcement  = AnnouncementModels(title= title, description= desc, sender= "havi")
    db.add(announcement); db.commit()
    db.refresh(announcement)

    return announcement


@router.get("/announcement")
async def get_announcement_list(db: Session = Depends(get_db)):
    announcements = db.query(models.AnnouncementModels).all()

    if not announcements:
        raise HTTPException(status_code=404, detail="Pas d'annonces")


    return announcements

@router.get("/announcement/{num}")
async def get_announcement_by_id(num: int, db: Session = Depends(get_db)):
    announcement = db.query(models.AnnouncementModels).filter(num == models.AnnouncementModels.id).first()

    if not announcement:
        raise HTTPException(status_code=404, detail="Annonces non trouvée")

    return announcement


@router.get("/messages")
async def get_messages(user: api.chatApp.models.users_models.User = Depends(get_current_user),db: Session = Depends(get_db)):
    messages_receive = db.query(Message).filter(Message.sender == user.username).all()
    messages_sent = db.query(Message).filter(Message.recipient == user.username).all()
    messages = messages_sent + messages_receive

    if not messages:
        raise HTTPException(status_code=404, detail="Pas de messages")

    return messages

@router.delete("/messages")
async def delete_messages(user: api.chatApp.models.users_models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages_receive = db.query(Message).filter(Message.sender == user.username).all()
    messages_sent = db.query(Message).filter(Message.recipient == user.username).all()
    messages = messages_sent + messages_receive

    if not messages:
        raise HTTPException(status_code=404, detail="Pas de messages")

    for message in messages:
        db.delete(message); db.commit()

    return {"messages supprimés"}


@router.get("/messages/room")
async def get_room_messages(room: str, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.room == room).all()
    if not messages:
        raise HTTPException(status_code=404, detail="Pas de messages ou room inexistante")

    return messages

@router.delete("/messages/room")
async def delete_room_messages(room: str, db: Session = Depends(get_db)):
    forum = db.query(Room).filter(room == Room.name).first()
    if not forum:
        raise HTTPException(status_code=404, detail="cette room n'exisrte pas")

    messages = db.query(Message).filter(room == Message.room).all()
    if not messages:
        raise HTTPException(status_code=404, detail="Pas de messages")

    for message in messages:
        db.delete(message); db.commit()

    db.delete(forum); db.commit()

    return {"room supprimée"}



