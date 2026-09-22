import asyncio
import logging
import time
from datetime import datetime, timezone
from sqlalchemy import select, func, text, or_
from sqlalchemy.orm import Session

from config import settings
from database import get_session, init_db
from models import Job
from devin_client import DevinClient
from reporters import SlackReporter, GitHubReporter
from github_client import GitHubClient
from triggers.github import build_remediation_prompt, reconcile_ci

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("worker")

devin_client = DevinClient()
slack_reporter = SlackReporter()
github_reporter = GitHubReporter()
github_client = GitHubClient()


def extract_pr_number(pull_requests: list) -> int | None:
    """Pull the PR number out of Devin's session response.

    Devin returns pull requests as {'pr_url': ..., 'pr_state': ...}; an older
    shape used {'url': ...}. Returns None when there's no PR yet.
    """
    if not pull_requests:
        return None
    pr = pull_requests[0]
    url = pr.get("pr_url") or pr.get("url", "")
    if url and "/pull/" in url:
        return int(url.split("/pull/")[-1].split("/")[0])
    return None


def _report(job, previous_state):
    """Fan out a state transition to Slack + GitHub in one event loop."""
    for reporter in (slack_reporter, github_reporter):
        try:
            asyncio.run(reporter.report_state_transition(job, previous_state))
        except Exception:
            logger.exception("Notification failed for job %s; workflow state preserved", job.id)


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
    """One worker starts queued jobs and reconciles progress, including missed webhooks."""
    with next(get_session()) as session:
        # A restart during a paid API call needs inspection, not an automatic repeat.
        from datetime import timedelta
        stale = datetime.now(timezone.utc) - timedelta(minutes=5)
        for job in session.execute(select(Job).where(Job.state == "starting", Job.updated_at < stale)).scalars():
            job.state = "needs_human"
            job.notes = "Session creation was interrupted. Check Devin before retrying."
        session.commit()
        queued = session.execute(select(Job).where(Job.state == "queued").order_by(Job.id)).scalars().all()
        for job in queued:
            process_job(job, session)
        jobs = session.execute(select(Job).where(
            Job.state.in_(["fixing", "checks_running", "checks_passed", "checks_failed"]),
            or_(Job.devin_session_id.is_(None), ~Job.devin_session_id.like("demo-%")),
        )).scalars().all()
        for job in jobs:
            if job.state in ("fixing", "checks_running") and job.devin_session_id:
                poll_session(job, session)
            if job.pr_number and not job.is_simulated:
                asyncio.run(reconcile_ci(job.pr_number))


def process_job(job: Job, session: Session):
    if session.bind.dialect.name == "postgresql":
        session.execute(text("SELECT pg_advisory_xact_lock(7834201)"))
    session.refresh(job)
    if job.state != "queued":
        session.commit()
        return
    active = session.execute(select(func.count(Job.id)).where(
        Job.state.in_(["starting", "fixing", "checks_running"]), Job.is_simulated == 0,
        or_(Job.devin_session_id.is_(None), ~Job.devin_session_id.like("demo-%")),
    )).scalar()
    spent = session.execute(select(func.coalesce(func.sum(Job.acu_usage), 0)).where(
        Job.is_simulated == 0,
        or_(Job.devin_session_id.is_(None), ~Job.devin_session_id.like("demo-%")),
    )).scalar()
    if active >= settings.CONCURRENCY_CAP or (settings.ACU_ADMISSION_CAP and spent >= settings.ACU_ADMISSION_CAP):
        session.commit()
        return
    if job.is_simulated or not (job.issue_url or "").startswith(f"https://github.com/{settings.TARGET_REPO}/issues/"):
        job.state = "needs_human"
        job.notes = "Queued issue does not belong to the configured repository."
        session.commit()
        return
    job.state = "starting"
    job.updated_at = datetime.now(timezone.utc)
    session.commit()
    try:
        async def start():
            if job.devin_session_id:
                return {"session_id": job.devin_session_id}
            issue = await github_client.get(f"repos/{settings.TARGET_REPO}/issues/{job.issue_number}")
            if "devin-fix" not in [label["name"] for label in issue.get("labels", [])]:
                raise ValueError("The issue no longer has the devin-fix label")
            return await devin_client.create_session(
                prompt=build_remediation_prompt(issue, {"full_name": settings.TARGET_REPO}),
                session_links=[job.issue_url],
            )
        response = asyncio.run(start())
        if not response.get("session_id"):
            raise ValueError("Devin did not return a session ID")
        job.devin_session_id = response["session_id"]
        job.state = "fixing"
    except Exception:
        logger.exception("Could not confirm session creation for job %s", job.id)
        job.state = "needs_human"
        job.notes = "Session creation could not be confirmed. Check Devin before retrying; no automatic retry."
    job.updated_at = datetime.now(timezone.utc)
    session.commit()
    _report(job, "queued")

def poll_session(job: Job, session: Session):
    """Poll Devin session status and update job state"""
    try:
        session_data = asyncio.run(devin_client.get_session(job.devin_session_id))
        
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
            prs = [pr for pr in prs if (pr.get("pr_url") or pr.get("url", "")).startswith(
                f"https://github.com/{settings.TARGET_REPO}/pull/")]
            if not prs:
                job.state = "needs_human"
                job.notes = "Devin returned a PR outside the configured repository."
                session.commit()
                _report(job, previous_state)
                return
            pr_number = extract_pr_number(prs)
            if pr_number:
                job.pr_number = pr_number
            new_state = "checks_running"
            note = f"PR created: {prs[0].get('pr_url') or prs[0].get('url', '')}"
        elif status in TERMINAL_FAIL:
            new_state = "checks_failed"
            note = f"Session failed: {session_data.get('error', 'Unknown error')}"
        elif status in TERMINAL_DONE:
            # session ended without a PR — needs a human to look
            new_state = "needs_human"
            note = f"Session ended ({status}) with no PR: {session_data.get('url')}"
        # else: still running/working — keep polling, no change

        usage = session_data.get("acus_consumed")
        if usage is not None:
            job.acu_usage = usage

        if new_state != previous_state:
            job.state = new_state
            job.notes = note
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
            logger.info("job %s: %s -> %s (pr=%s)", job.id, previous_state, new_state, job.pr_number)
            _report(job, previous_state)
        else:
            session.commit()  # persist usage update

    except Exception as e:
        logger.error("job %s: error polling session %s: %s", job.id, job.devin_session_id, e)
        session.rollback()  # transient reads retry next cycle; preserve the workflow outcome

if __name__ == "__main__":
    worker()
