from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
from .config import get_settings

settings = get_settings()

# Use synchronous SQLite for simplicity
DATABASE_URL = settings.DATABASE_URL.replace("+aiosqlite", "")
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
