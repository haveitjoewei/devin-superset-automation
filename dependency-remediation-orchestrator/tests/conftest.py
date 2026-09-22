"""Test setup: dummy env + path so app modules import without real credentials."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.__setitem__("DEVIN_API_KEY", "test")
os.environ.__setitem__("DEVIN_ORG_ID", "test")
os.environ.__setitem__("GITHUB_TOKEN", "test")
os.environ.__setitem__("GITHUB_WEBHOOK_SECRET", "testsecret")
os.environ.__setitem__("DATABASE_URL", "sqlite:///:memory:")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base


@pytest.fixture
def jobs_db(monkeypatch):
    import worker
    import metrics
    from triggers import github
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)
    def get_session():
        with sessions() as session:
            yield session
    monkeypatch.setattr(worker, "get_session", get_session)
    monkeypatch.setattr(github, "get_session", get_session)
    monkeypatch.setattr(metrics, "SessionLocal", sessions)
    yield sessions
    engine.dispose()
