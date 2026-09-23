from pydantic import BaseModel, Field

class RequestCreate(BaseModel):
    consultorio_id: int = Field(ge=1, le=10)
    tipo: str

class ClaimRequest(BaseModel):
    auxiliar_id: int

class AssistantCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    usuario: str = Field(min_length=1, max_length=80)
