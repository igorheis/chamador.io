from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Office(Base):
    __tablename__ = "consultorios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

class Assistant(Base):
    __tablename__ = "auxiliares"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    usuario: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ativo", nullable=False)

class Request(Base):
    __tablename__ = "solicitacoes"
    __table_args__ = (Index("ix_solicitacoes_status_criacao", "status", "data_hora_criacao"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(ForeignKey("consultorios.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="solicitado", nullable=False)
    data_hora_criacao: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    data_hora_atendimento: Mapped[datetime | None] = mapped_column(DateTime)
    data_hora_conclusao: Mapped[datetime | None] = mapped_column(DateTime)
    auxiliar_id: Mapped[int | None] = mapped_column(ForeignKey("auxiliares.id"))
    tempo_atendimento: Mapped[int | None] = mapped_column(Integer)
    office: Mapped[Office] = relationship()
    assistant: Mapped[Assistant | None] = relationship()
