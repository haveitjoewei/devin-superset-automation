from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from models import Base
from config import settings

# Use PostgreSQL for production
engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

def init_db():
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(7834202)"))
        Base.metadata.create_all(connection)
        # Additive upgrade for databases created by the original demo.
        columns = {c["name"] for c in inspect(connection).get_columns("jobs")}
        additions = {"ci_repair_sha": "VARCHAR", "ci_head_sha": "VARCHAR",
                     "is_simulated": "INTEGER NOT NULL DEFAULT 0", "acu_usage": "FLOAT"}
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE jobs ADD COLUMN {name} {definition}"))

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
