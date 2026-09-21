from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    # unique so a concurrently re-delivered webhook can't create a duplicate job
    # (single-repo demo; a multi-repo deployment would key on (repo, issue_number))
    issue_number = Column(Integer, nullable=False, index=True, unique=True)
    issue_url = Column(String, nullable=True)
    devin_session_id = Column(String, nullable=True, index=True)
    pr_number = Column(Integer, nullable=True, index=True)
    state = Column(String, default="queued", nullable=False)  # queued, fixing, checks_running, checks_passed, merged, checks_failed, needs_human
    attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    cost = Column(Float, default=0.0, nullable=False)
    notes = Column(Text, nullable=True)
    effort_hours = Column(Float, default=0.0, nullable=False)
    validated_at = Column(DateTime, nullable=True)
    labeled_at = Column(DateTime, nullable=True)
    slack_thread_ts = Column(String, nullable=True)
