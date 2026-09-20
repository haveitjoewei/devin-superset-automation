from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
import hmac
import hashlib
import json
from datetime import datetime

from config import settings
from database import get_session, init_db
from models import Job
from devin_client import DevinClient
from github_client import GitHubClient

app = FastAPI()
devin_client = DevinClient()
github_client = GitHubClient()

@app.on_event("startup")
async def startup_event():
    init_db()

def verify_github_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature:
        return False
    
    hmac_obj = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    )
    expected_signature = f"sha256={hmac_obj.hexdigest()}"
    return hmac.compare_digest(expected_signature, signature)

@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhooks"""
    signature = request.headers.get("x-hub-signature-256")
    payload = await request.body()
    
    if not verify_github_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    event_data = json.loads(payload)
    event_type = request.headers.get("x-github-event")
    
    if event_type == "issues":
        await handle_issue_event(event_data, background_tasks)
    elif event_type == "pull_request":
        await handle_pr_event(event_data, background_tasks)
    elif event_type == "check_suite":
        await handle_check_suite_event(event_data, background_tasks)
    
    return JSONResponse({"status": "ok"})

async def handle_issue_event(event_data: dict, background_tasks: BackgroundTasks):
    """Handle issue labeled events"""
    action = event_data.get("action")
    issue = event_data.get("issue")
    repository = event_data.get("repository")
    
    if action == "labeled" and "devin-remediate" in [l["name"] for l in issue.get("labels", [])]:
        background_tasks.add_task(create_remediation_job, issue, repository)

async def handle_pr_event(event_data: dict, background_tasks: BackgroundTasks):
    """Handle pull request events"""
    action = event_data.get("action")
    pr = event_data.get("pull_request")
    repository = event_data.get("repository")
    
    if action == "opened":
        background_tasks.add_task(match_pr_to_job, pr, repository)

async def handle_check_suite_event(event_data: dict, background_tasks: BackgroundTasks):
    """Handle check suite completion events"""
    check_suite = event_data.get("check_suite")
    repository = event_data.get("repository")
    
    if check_suite.get("conclusion") == "failure":
        background_tasks.add_task(handle_ci_failure, check_suite, repository)

async def create_remediation_job(issue: dict, repository: dict):
    """Create a new remediation job and start Devin session"""
    with next(get_session()) as session:
        # Check if job already exists
        result = session.execute(
            select(Job).where(Job.issue_number == issue["number"])
        )
        existing_job = result.scalar_one_or_none()
        
        if existing_job:
            return
        
        # Create new job
        job = Job(
            issue_number=issue["number"],
            state="queued"
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        
        # Build prompt for Devin
        prompt = build_remediation_prompt(issue, repository)
        
        # Create Devin session
        session_response = await devin_client.create_session(
            prompt=prompt,
            session_links=[issue["html_url"]]
        )
        
        # Update job with session info
        job.devin_session_id = session_response.get("session_id")
        job.state = "session_started"
        job.updated_at = datetime.utcnow()
        session.commit()
        
        # Post comment on GitHub
        comment = f"🤖 **Dependency Remediation Started**\n\nDevin session created: {session_response.get('url')}\nSession ID: {session_response.get('session_id')}"
        await github_client.comment_on_issue(
            repository["owner"]["login"],
            repository["name"],
            issue["number"],
            comment
        )

async def match_pr_to_job(pr: dict, repository: dict):
    """Match a PR to its remediation job"""
    with next(get_session()) as session:
        # Try to match by issue number (assuming PR is related to issue)
        result = session.execute(
            select(Job).where(Job.state == "session_started")
        )
        jobs = result.scalars().all()
        
        for job in jobs:
            job.pr_number = pr["number"]
            job.state = "verifying"
            job.updated_at = datetime.utcnow()
            session.commit()
            break

async def handle_ci_failure(check_suite: dict, repository: dict):
    """Handle CI failure with bounded repair attempt"""
    with next(get_session()) as session:
        # Find job associated with this PR
        result = session.execute(
            select(Job).where(
                Job.state == "verifying",
                Job.attempts < 1
            )
        )
        job = result.scalar_one_or_none()
        
        if job and job.devin_session_id:
            # Send follow-up message to Devin with failure details
            failure_message = f"CI failed for your changes. Please review and fix the failing tests:\n\n{check_suite.get('details_url')}"
            await devin_client.send_message(job.devin_session_id, failure_message)
            
            job.attempts += 1
            job.updated_at = datetime.utcnow()
            session.commit()

def build_remediation_prompt(issue: dict, repository: dict) -> str:
    """Build prompt for Devin based on issue content"""
    return f"""Analyze and fix this dependency upgrade blocker:

**Issue:** {issue['title']}
**Description:** {issue.get('body', '')}
**Repository:** {repository['full_name']}

**Task:**
1. Investigate why the current dependency constraint is in place
2. Analyze the code that uses this dependency
3. Identify what would break with the target version
4. Implement the necessary code changes to make the upgrade compatible
5. Update any related tests
6. Create a pull request with the complete remediation

**Validation:**
- The fix should allow unpinning the dependency
- All tests should pass
- No breaking changes to existing functionality
- Follow the project's coding standards

Please create a pull request with your changes."""

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "dependency-remediation-orchestrator"}

@app.get("/jobs")
async def list_jobs(session: Session = Depends(get_session)):
    """List all jobs"""
    result = session.execute(select(Job))
    jobs = result.scalars().all()
    return [{"id": job.id, "issue_number": job.issue_number, "state": job.state, "created_at": job.created_at} for job in jobs]
