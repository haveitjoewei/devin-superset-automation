from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
import hmac
import hashlib
import json

from config import settings
from models import Job
from database import get_session, init_db
from metrics import get_job_metrics
from triggers import github as github_trigger

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    init_db()
    _create_metrics_view()


def _create_metrics_view():
    """(Re)create the vw_job_metrics view the Superset dashboard reads."""
    from database import SessionLocal
    from sqlalchemy import text

    with SessionLocal() as session:
        session.execute(text("DROP VIEW IF EXISTS vw_job_metrics"))
        session.execute(text("""
            CREATE VIEW vw_job_metrics AS
            SELECT
                id, issue_number, issue_url, devin_session_id, pr_number, state,
                attempts, created_at, updated_at, CAST(NULL AS FLOAT) AS cost, effort_hours, validated_at,
                labeled_at, slack_thread_ts, notes, acu_usage, ci_head_sha,
                CASE
                    WHEN validated_at IS NOT NULL AND labeled_at IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (validated_at - labeled_at)) / 3600
                    ELSE NULL
                END AS mttr_hours,
                CASE
                    WHEN notes LIKE '%test%' THEN 'test'
                    WHEN notes LIKE '%bug%' THEN 'bug'
                    ELSE 'dependency'
                END AS stream
            FROM jobs
            WHERE is_simulated = 0
              AND (devin_session_id IS NULL OR devin_session_id NOT LIKE 'demo-%')
              AND (state NOT IN ('checks_passed', 'merged') OR ci_head_sha IS NOT NULL)
        """))
        session.commit()
        print("Created vw_job_metrics view")


def verify_github_signature(payload: bytes, signature: str) -> bool:
    if not signature:
        return False
    digest = hmac.new(settings.GITHUB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256)
    return hmac.compare_digest(f"sha256={digest.hexdigest()}", signature)


@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Verify the signature, then hand the event to the GitHub trigger adapter."""
    payload = await request.body()
    if not verify_github_signature(payload, request.headers.get("x-hub-signature-256")):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event_type = request.headers.get("x-github-event")
    await github_trigger.route(event_type, json.loads(payload), background_tasks)
    return JSONResponse({"status": "ok"})


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "devin-auto-fix-orchestrator"}


@app.get("/jobs")
async def list_jobs(session: Session = Depends(get_session)):
    jobs = session.execute(select(Job)).scalars().all()
    return [
        {"id": j.id, "issue_number": j.issue_number, "state": j.state, "created_at": j.created_at,
         "pr_number": j.pr_number, "session_id": j.devin_session_id, "notes": j.notes,
         "checked_commit": j.ci_head_sha, "simulated": bool(j.is_simulated)}
        for j in jobs
    ]


@app.get("/metrics")
async def get_metrics():
    return get_job_metrics()
