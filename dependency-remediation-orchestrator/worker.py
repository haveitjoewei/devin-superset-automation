import asyncio
import time
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import get_session, init_db
from .models import Job
from .devin_client import DevinClient
from .github_client import GitHubClient

devin_client = DevinClient()
github_client = GitHubClient()

def worker():
    """Background worker to poll Devin sessions and manage job lifecycle"""
    print("Worker started")
    init_db()
    
    while True:
        try:
            process_jobs()
            time.sleep(settings.WORKER_POLL_INTERVAL)
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(settings.WORKER_POLL_INTERVAL)

def process_jobs():
    """Process all active jobs respecting concurrency cap"""
    with next(get_session()) as session:
        # Count active sessions
        result = session.execute(
            select(Job).where(Job.state.in_(["session_started", "verifying"]))
        )
        active_jobs = result.scalars().all()
        
        if len(active_jobs) >= settings.CONCURRENCY_CAP:
            print(f"Concurrency cap reached: {len(active_jobs)} active jobs")
            return
        
        # Process jobs in queued state
        result = session.execute(
            select(Job).where(Job.state == "queued")
        )
        queued_jobs = result.scalars().all()
        
        for job in queued_jobs:
            if len(active_jobs) >= settings.CONCURRENCY_CAP:
                break
            
            process_job(job, session)
            active_jobs.append(job)
        
        # Poll active sessions
        for job in active_jobs:
            poll_session(job, session)

def process_job(job: Job, session: Session):
    """Process a single job"""
    if not job.devin_session_id:
        print(f"Job {job.id} has no session ID")
        return
    
    print(f"Processing job {job.id}")
    job.state = "session_started"
    job.updated_at = datetime.utcnow()
    session.commit()

def poll_session(job: Job, session: Session):
    """Poll Devin session status and update job state"""
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        session_data = loop.run_until_complete(devin_client.get_session(job.devin_session_id))
        loop.close()
        
        # Update job based on session status
        if session_data.get("status") == "completed":
            job.state = "pr_opened"
            job.updated_at = datetime.utcnow()
            
            # Try to extract PR URL from session
            session_url = session_data.get("url")
            if session_url:
                job.notes = f"Session completed: {session_url}"
            
            session.commit()
        
        elif session_data.get("status") == "failed":
            job.state = "failed"
            job.updated_at = datetime.utcnow()
            job.notes = f"Session failed: {session_data.get('error', 'Unknown error')}"
            session.commit()
        
        # Update cost if available
        if "cost" in session_data:
            job.cost = session_data["cost"]
            session.commit()
            
    except Exception as e:
        print(f"Error polling session {job.devin_session_id}: {e}")
        job.state = "needs_human"
        job.notes = f"Polling error: {str(e)}"
        job.updated_at = datetime.utcnow()
        session.commit()

if __name__ == "__main__":
    worker()
