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
from reporters import SlackReporter, GitHubReporter

devin_client = DevinClient()
github_client = GitHubClient()
slack_reporter = SlackReporter()
github_reporter = GitHubReporter()


def _report(job, previous_state):
    """Fan out a state transition to Slack + GitHub in one event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(slack_reporter.report_state_transition(job, previous_state))
        loop.run_until_complete(github_reporter.report_state_transition(job, previous_state))
    finally:
        loop.close()

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
            select(Job).where(Job.state.in_(["fixing", "checks_running"]))
        )
        active_jobs = result.scalars().all()

        # Concurrency cap gates STARTING new jobs only — it must never block
        # polling of already-active jobs (that would freeze the lifecycle).
        if len(active_jobs) < settings.CONCURRENCY_CAP:
            queued_jobs = session.execute(
                select(Job).where(Job.state == "queued")
            ).scalars().all()
            for job in queued_jobs:
                if len(active_jobs) >= settings.CONCURRENCY_CAP:
                    break
                process_job(job, session)
                active_jobs.append(job)

        # Always poll every active job, regardless of the cap.
        for job in active_jobs:
            poll_session(job, session)

def process_job(job: Job, session: Session):
    """Process a single job"""
    if not job.devin_session_id:
        print(f"Job {job.id} has no session ID")
        return
    
    print(f"Processing job {job.id}")
    previous_state = job.state
    job.state = "fixing"
    job.labeled_at = datetime.now(timezone.utc)
    job.updated_at = datetime.now(timezone.utc)
    session.commit()
    
    _report(job, previous_state)

def poll_session(job: Job, session: Session):
    """Poll Devin session status and update job state"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        session_data = loop.run_until_complete(devin_client.get_session(job.devin_session_id))
        loop.close()
        
        previous_state = job.state

        # Devin's status vocabulary varies by API version (status vs status_enum;
        # terminal value may be "finished"/"stopped", not "completed"). Drive off
        # PR presence first — that's version-agnostic — then fall back to status.
        status = (session_data.get("status") or session_data.get("status_enum") or "").lower()
        prs = session_data.get("pull_requests")
        if not prs and session_data.get("pull_request"):
            prs = [session_data["pull_request"]]
        prs = prs or []

        TERMINAL_DONE = {"completed", "finished", "stopped", "expired", "suspended", "blocked"}
        TERMINAL_FAIL = {"failed", "error", "crashed"}

        new_state = job.state
        note = job.notes
        if prs:
            # Devin returns {'pr_url': ..., 'pr_state': ...}; older shape uses 'url'
            pr_url = prs[0].get("pr_url") or prs[0].get("url", "")
            if pr_url and "/pull/" in pr_url:
                job.pr_number = int(pr_url.split("/pull/")[-1].split("/")[0])
            new_state = "checks_running"
            note = f"PR created: {pr_url}"
        elif status in TERMINAL_FAIL:
            new_state = "checks_failed"
            note = f"Session failed: {session_data.get('error', 'Unknown error')}"
        elif status in TERMINAL_DONE:
            # session ended without a PR — needs a human to look
            new_state = "needs_human"
            note = f"Session ended ({status}) with no PR: {session_data.get('url')}"
        # else: still running/working — keep polling, no change

        # capture cost regardless (Devin reports acus_consumed)
        cost = session_data.get("cost", session_data.get("acus_consumed"))
        if cost is not None:
            job.cost = cost

        if new_state != previous_state:
            job.state = new_state
            job.notes = note
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
            _report(job, previous_state)
        else:
            session.commit()  # persist cost update
            
    except Exception as e:
        print(f"Error polling session {job.devin_session_id}: {e}")
        previous_state = job.state
        job.state = "needs_human"
        job.notes = f"Polling error: {str(e)}"
        job.updated_at = datetime.now(timezone.utc)
        session.commit()
        _report(job, previous_state)

if __name__ == "__main__":
    worker()
