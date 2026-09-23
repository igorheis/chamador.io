from pathlib import Path
from datetime import datetime
from collections import Counter
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Base, engine, get_db, SessionLocal
from .models import Request, Assistant
from .schemas import RequestCreate, ClaimRequest, AssistantCreate
from .services import REQUEST_TYPES, serialize, seed, create_request, claim_request, complete_request

ROOT = Path(__file__).resolve().parent.parent
Base.metadata.create_all(bind=engine)
with SessionLocal() as db: seed(db)
app = FastAPI(title="Chamador Odontológico", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

class Hub:
    def __init__(self): self.connections: set[WebSocket] = set()
    async def connect(self, ws): await ws.accept(); self.connections.add(ws)
    def disconnect(self, ws): self.connections.discard(ws)
    async def broadcast(self, message):
        stale=[]
        for ws in list(self.connections):
            try: await ws.send_json(message)
            except Exception: stale.append(ws)
        for ws in stale: self.disconnect(ws)
hub=Hub()

@app.get("/")
def home(): return FileResponse(ROOT / "templates" / "index.html")
@app.get("/consultorio/{office_id}")
def office_page(office_id: int):
    if office_id not in range(1,11): raise HTTPException(404,"Consultório não encontrado")
    return FileResponse(ROOT / "templates" / "consultorio.html")
@app.get("/painel")
def dashboard(): return FileResponse(ROOT / "templates" / "painel.html")
@app.get("/historico")
def history_page(): return FileResponse(ROOT / "templates" / "historico.html")
@app.get("/api/meta")
def metadata(db: Session=Depends(get_db)):
    return {"tipos": REQUEST_TYPES, "consultorios": [{"id":i,"nome":f"Consultório {i:02d}"} for i in range(1,11)], "auxiliares":[{"id":a.id,"nome":a.nome} for a in db.query(Assistant).order_by(Assistant.id)]}
@app.get("/api/solicitacoes")
def list_requests(status: str="ativos", consultorio_id: int|None=None, db: Session=Depends(get_db)):
    q=db.query(Request)
    if status=="ativos": q=q.filter(Request.status!="concluido")
    elif status=="concluidos": q=q.filter(Request.status=="concluido")
    if consultorio_id: q=q.filter(Request.consultorio_id==consultorio_id)
    calls=q.order_by(Request.data_hora_criacao.desc()).all()
    return [serialize(c) for c in calls]
@app.post("/api/solicitacoes", status_code=201)
async def new_request(payload: RequestCreate, db: Session=Depends(get_db)):
    try: call=create_request(db,payload.consultorio_id,payload.tipo)
    except ValueError as e: raise HTTPException(400,str(e))
    data=serialize(call); await hub.broadcast({"event":"created","request":data}); return data
@app.post("/api/solicitacoes/{call_id}/assumir")
async def assume(call_id: int, payload: ClaimRequest, db: Session=Depends(get_db)):
    try: call=claim_request(db,call_id,payload.auxiliar_id)
    except LookupError as e: raise HTTPException(404,str(e))
    except ValueError as e: raise HTTPException(409,str(e))
    data=serialize(call); await hub.broadcast({"event":"updated","request":data}); return data
@app.post("/api/solicitacoes/{call_id}/concluir")
async def finish(call_id: int, db: Session=Depends(get_db)):
    try: call=complete_request(db,call_id)
    except LookupError as e: raise HTTPException(404,str(e))
    data=serialize(call); await hub.broadcast({"event":"completed","request":data}); return data
@app.post("/api/auxiliares",status_code=201)
def add_assistant(payload: AssistantCreate,db: Session=Depends(get_db)):
    assistant=Assistant(nome=payload.nome,usuario=payload.usuario); db.add(assistant)
    try: db.commit(); db.refresh(assistant)
    except Exception: db.rollback(); raise HTTPException(409,"Usuário já cadastrado")
    return {"id":assistant.id,"nome":assistant.nome,"usuario":assistant.usuario}
@app.get("/api/indicadores")
def metrics(db: Session=Depends(get_db)):
    total=db.query(Request).count(); active=db.query(Request).filter(Request.status!="concluido").count(); done=db.query(Request).filter(Request.status=="concluido").count()
    offices=db.query(Request.consultorio_id,func.count(Request.id)).group_by(Request.consultorio_id).all()
    kinds=db.query(Request.tipo,func.count(Request.id)).group_by(Request.tipo).all()
    avg=db.query(func.avg(Request.tempo_atendimento)).filter(Request.status=="concluido").scalar()
    return {"total":total,"ativos":active,"concluidos":done,"por_consultorio":[{"consultorio_id":i,"total":n} for i,n in offices],"por_tipo":[{"tipo":k,"total":n} for k,n in kinds],"tempo_medio_segundos":round(avg) if avg else 0}
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await hub.connect(ws)
    try:
        with SessionLocal() as db:
            active=db.query(Request).filter(Request.status!="concluido").order_by(Request.data_hora_criacao.desc()).all()
            await ws.send_json({"event":"snapshot","requests":[serialize(c) for c in active]})
        while True: await ws.receive_text()
    except WebSocketDisconnect: hub.disconnect(ws)
