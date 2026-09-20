from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_number = Column(Integer, nullable=False, index=True)
    devin_session_id = Column(String, nullable=True, index=True)
    pr_number = Column(Integer, nullable=True, index=True)
    state = Column(String, default="queued", nullable=False)  # queued, session_started, pr_opened, verifying, validated, failed, needs_human
    attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    cost = Column(Float, default=0.0, nullable=False)
    notes = Column(Text, nullable=True)
    effort_hours = Column(Float, default=0.0, nullable=False)
    validated_at = Column(DateTime, nullable=True)
    labeled_at = Column(DateTime, nullable=True)
    slack_thread_ts = Column(String, nullable=True)
