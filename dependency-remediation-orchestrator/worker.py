import asyncio
import time
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from database import get_session, init_db
from models import Job
from devin_client import DevinClient
from github_client import GitHubClient
from slack_reporter import SlackReporter

devin_client = DevinClient()
github_client = GitHubClient()
slack_reporter = SlackReporter()

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
        result = session.execute(
            select(Job).where(Job.state.in_(["session_started", "verifying"]))
        )
        active_jobs = result.scalars().all()
        
        if len(active_jobs) >= settings.CONCURRENCY_CAP:
            print(f"Concurrency cap reached: {len(active_jobs)} active jobs")
            return
        
        result = session.execute(
            select(Job).where(Job.state == "queued")
        )
        queued_jobs = result.scalars().all()
        
        for job in queued_jobs:
            if len(active_jobs) >= settings.CONCURRENCY_CAP:
                break
            
            process_job(job, session)
            active_jobs.append(job)
        
        for job in active_jobs:
            poll_session(job, session)

def process_job(job: Job, session: Session):
    """Process a single job"""
    if not job.devin_session_id:
        print(f"Job {job.id} has no session ID")
        return
    
    print(f"Processing job {job.id}")
    previous_state = job.state
    job.state = "session_started"
    job.labeled_at = datetime.now(timezone.utc)
    job.updated_at = datetime.now(timezone.utc)
    session.commit()
    
    # Report to Slack
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(slack_reporter.report_state_transition(job, previous_state))
    loop.close()

def poll_session(job: Job, session: Session):
    """Poll Devin session status and update job state"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        session_data = loop.run_until_complete(devin_client.get_session(job.devin_session_id))
        loop.close()
        
        previous_state = job.state
        
        if session_data.get("status") == "completed":
            pr_urls = session_data.get("pull_requests", [])
            if pr_urls:
                pr_url = pr_urls[0].get("url", "")
                # Extract PR number from URL (format: https://github.com/owner/repo/pull/123)
                if pr_url and "/pull/" in pr_url:
                    pr_number = pr_url.split("/pull/")[-1]
                    job.pr_number = int(pr_number)
                job.state = "verifying"
                job.notes = f"PR created: {pr_url}"
            else:
                job.state = "completed"
                session_url = session_data.get("url")
                if session_url:
                    job.notes = f"Session completed: {session_url}"
            
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
            
            # Report to Slack
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(slack_reporter.report_state_transition(job, previous_state))
            loop.close()
        
        elif session_data.get("status") == "failed":
            job.state = "failed"
            job.updated_at = datetime.now(timezone.utc)
            job.notes = f"Session failed: {session_data.get('error', 'Unknown error')}"
            session.commit()
            
            # Report to Slack
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(slack_reporter.report_state_transition(job, previous_state))
            loop.close()
        
        if "cost" in session_data:
            job.cost = session_data["cost"]
            session.commit()
            
    except Exception as e:
        print(f"Error polling session {job.devin_session_id}: {e}")
        previous_state = job.state
        job.state = "needs_human"
        job.notes = f"Polling error: {str(e)}"
        job.updated_at = datetime.now(timezone.utc)
        session.commit()
        
        # Report to Slack
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(slack_reporter.report_state_transition(job, previous_state))
        loop.close()

if __name__ == "__main__":
    worker()
