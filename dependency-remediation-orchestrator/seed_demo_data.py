from database import SessionLocal, init_db
from models import Job
from datetime import datetime, timedelta, timezone
import random

def seed_demo_data():
    """Seed demo data for Superset dashboard"""
    init_db()
    
    now = datetime.now(timezone.utc)
    
    with SessionLocal() as session:
        # Clear existing data
        session.query(Job).delete()
        session.commit()
        
        # Create demo jobs with realistic data
        demo_jobs = [
            {
                "issue_number": 100,
                "issue_url": "https://github.com/haveitjoewei/superset/issues/100",
                "devin_session_id": "demo-session-001",
                "pr_number": 101,
                "state": "validated",
                "attempts": 1,
                "cost": 2.50,
                "effort_hours": 4.0,
                "notes": "Fixed apispec version compatibility",
                "validated_at": now - timedelta(days=1),
                "labeled_at": now - timedelta(days=1, hours=2),
                "slack_thread_ts": "1234567890.123456"
            },
            {
                "issue_number": 102,
                "issue_url": "https://github.com/haveitjoewei/superset/issues/102",
                "devin_session_id": "demo-session-002",
                "pr_number": 103,
                "state": "validated",
                "attempts": 1,
                "cost": 3.20,
                "effort_hours": 6.0,
                "notes": "Resolved marshmallow-sqlalchemy deprecation",
                "validated_at": now - timedelta(days=2),
                "labeled_at": now - timedelta(days=2, hours=3),
                "slack_thread_ts": "1234567890.123457"
            },
            {
                "issue_number": 104,
                "issue_url": "https://github.com/haveitjoewei/superset/issues/104",
                "devin_session_id": "demo-session-003",
                "pr_number": 105,
                "state": "validated",
                "attempts": 0,
                "cost": 1.80,
                "effort_hours": 3.0,
                "notes": "Test failure fix",
                "validated_at": now - timedelta(days=3),
                "labeled_at": now - timedelta(days=3, hours=1),
                "slack_thread_ts": "1234567890.123458"
            },
            {
                "issue_number": 106,
                "issue_url": "https://github.com/haveitjoewei/superset/issues/106",
                "devin_session_id": "demo-session-004",
                "pr_number": 107,
                "state": "failed",
                "attempts": 1,
                "cost": 2.10,
                "effort_hours": 0.0,
                "notes": "Requires manual intervention - complex dependency conflict",
                "validated_at": None,
                "labeled_at": now - timedelta(days=4),
                "slack_thread_ts": "1234567890.123459"
            },
            {
                "issue_number": 108,
                "issue_url": "https://github.com/haveitjoewei/superset/issues/108",
                "devin_session_id": "demo-session-005",
                "pr_number": None,
                "state": "verifying",
                "attempts": 0,
                "cost": 1.50,
                "effort_hours": 0.0,
                "notes": "PR created, CI running",
                "validated_at": None,
                "labeled_at": now - timedelta(hours=2),
                "slack_thread_ts": "1234567890.123460"
            },
            {
                "issue_number": 110,
                "issue_url": "https://github.com/haveitjoewei/superset/issues/110",
                "devin_session_id": "demo-session-006",
                "pr_number": None,
                "state": "session_started",
                "attempts": 0,
                "cost": 0.50,
                "effort_hours": 0.0,
                "notes": "Session started, Devin working",
                "validated_at": None,
                "labeled_at": now - timedelta(minutes=30),
                "slack_thread_ts": "1234567890.123461"
            },
            {
                "issue_number": 112,
                "issue_url": "https://github.com/haveitjoewei/superset/issues/112",
                "devin_session_id": "demo-session-007",
                "pr_number": None,
                "state": "queued",
                "attempts": 0,
                "cost": 0.0,
                "effort_hours": 0.0,
                "notes": "Waiting for worker",
                "validated_at": None,
                "labeled_at": now - timedelta(minutes=15),
                "slack_thread_ts": None
            },
            {
                "issue_number": 114,
                "issue_url": "https://github.com/haveitjoewei/superset/issues/114",
                "devin_session_id": "demo-session-008",
                "pr_number": 115,
                "state": "needs_human",
                "attempts": 1,
                "cost": 3.50,
                "effort_hours": 0.0,
                "notes": "Requires architectural decision",
                "validated_at": None,
                "labeled_at": now - timedelta(days=5),
                "slack_thread_ts": "1234567890.123462"
            }
        ]
        
        for job_data in demo_jobs:
            job = Job(**job_data)
            session.add(job)
        
        session.commit()
        print(f"Seeded {len(demo_jobs)} demo jobs")

if __name__ == "__main__":
    seed_demo_data()