from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .models import Request, Office, Assistant

REQUEST_TYPES = ["Água", "Valo", "Anestesia", "Gazes", "Suporte presencial", "Limpeza", "Abridor"]

def serialize(call: Request) -> dict:
    return {
        "id": call.id, "consultorio_id": call.consultorio_id,
        "consultorio": call.office.nome if call.office else f"Consultório {call.consultorio_id:02d}",
        "tipo": call.tipo, "status": call.status,
        "data_hora_criacao": call.data_hora_criacao.isoformat() + "Z",
        "data_hora_atendimento": call.data_hora_atendimento.isoformat() + "Z" if call.data_hora_atendimento else None,
        "data_hora_conclusao": call.data_hora_conclusao.isoformat() + "Z" if call.data_hora_conclusao else None,
        "auxiliar_id": call.auxiliar_id, "auxiliar": call.assistant.nome if call.assistant else None,
        "tempo_atendimento": call.tempo_atendimento,
    }

def seed(db: Session):
    if db.query(Office).count() == 0:
        db.add_all([Office(id=i, nome=f"Consultório {i:02d}") for i in range(1, 11)])
    if db.query(Assistant).count() == 0:
        db.add_all([Assistant(nome=f"Auxiliar {i:02d}", usuario=f"auxiliar{i:02d}") for i in range(1, 6)])
    db.commit()

def create_request(db: Session, office_id: int, kind: str) -> Request:
    if kind not in REQUEST_TYPES:
        raise ValueError("Tipo de solicitação inválido")
    if db.get(Office, office_id) is None:
        raise ValueError("Consultório não encontrado")
    call = Request(consultorio_id=office_id, tipo=kind, status="solicitado")
    db.add(call); db.commit(); db.refresh(call)
    return call

def claim_request(db: Session, call_id: int, assistant_id: int) -> Request:
    call = db.get(Request, call_id)
    if call is None: raise LookupError("Chamado não encontrado")
    if call.status == "concluido": raise ValueError("Este chamado já foi concluído")
    if db.get(Assistant, assistant_id) is None: raise LookupError("Auxiliar não encontrado")
    if call.auxiliar_id is not None and call.auxiliar_id != assistant_id:
        raise ValueError("Este chamado já está sendo atendido por outra auxiliar")
    if call.status == "solicitado":
        call.status = "em_atendimento"
        call.data_hora_atendimento = datetime.now(timezone.utc)
    call.auxiliar_id = assistant_id
    db.commit(); db.refresh(call)
    return call

def complete_request(db: Session, call_id: int) -> Request:
    call = db.get(Request, call_id)
    if call is None: raise LookupError("Chamado não encontrado")
    if call.status == "concluido": return call
    now = datetime.now(timezone.utc)
    call.status = "concluido"
    call.data_hora_conclusao = now
    start = call.data_hora_atendimento or call.data_hora_criacao
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    call.tempo_atendimento = max(0, int((now - start).total_seconds()))
    db.commit(); db.refresh(call)
    return call
