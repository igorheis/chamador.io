from pathlib import Path
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "database" / "chamador.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(os.getenv("CHAMADOR_DATABASE_URL", f"sqlite:///{DB_PATH}"), connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
