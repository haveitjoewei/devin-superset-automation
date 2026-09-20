"""GitHub trigger adapter.

Maps GitHub webhook events (issues / check_suite / pull_request) onto the job
engine: start a fix, run a bounded CI repair, mark checks passed, mark merged.

To add another trigger source (Linear, Sentry, a scanner), add a sibling module
that normalizes its events into the same job actions — the Devin session logic
and reporters stay shared. `api.py` only routes; it knows nothing GitHub-specific.
"""
from datetime import datetime, timezone
from sqlalchemy import select, func

from config import settings
from database import get_session
from models import Job
from devin_client import DevinClient
from github_client import GitHubClient
from reporters import SlackReporter, GitHubReporter


def _daily_spend_exceeded(session) -> bool:
    """True if today's Devin spend has hit the configured cap (0 disables)."""
    if not settings.DAILY_COST_CAP:
        return False
    day_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    spent = session.execute(
        select(func.coalesce(func.sum(Job.cost), 0.0)).where(Job.created_at >= day_start)
    ).scalar() or 0.0
    return spent >= settings.DAILY_COST_CAP

devin_client = DevinClient()
github_client = GitHubClient()
slack_reporter = SlackReporter()
github_reporter = GitHubReporter()


async def route(event_type: str, event_data: dict, background_tasks):
    """Dispatch a verified GitHub webhook to the right handler."""
    if event_type == "issues":
        await handle_issue_event(event_data, background_tasks)
    elif event_type == "check_suite":
        await handle_check_suite_event(event_data, background_tasks)
    elif event_type == "pull_request":
        await handle_pull_request_event(event_data, background_tasks)


async def handle_issue_event(event_data: dict, background_tasks):
    action = event_data.get("action")
    issue = event_data.get("issue")
    repository = event_data.get("repository")
    if action == "labeled" and "devin-fix" in [l["name"] for l in issue.get("labels", [])]:
        background_tasks.add_task(create_remediation_job, issue, repository)


async def handle_check_suite_event(event_data: dict, background_tasks):
    check_suite = event_data.get("check_suite")
    repository = event_data.get("repository")
    if check_suite.get("conclusion") == "failure":
        background_tasks.add_task(handle_ci_failure, check_suite, repository)
    elif check_suite.get("conclusion") == "success":
        background_tasks.add_task(handle_ci_success, check_suite, repository)
    # Production trigger (fully automated, no human label): when a Dependabot-authored
    # PR's checks FAIL and no job owns it yet, auto-create a job here and hand the
    # failing upgrade to Devin. That turns the "dead lane" catch fully hands-off. The
    # demo uses the labeled-issue on-ramp instead (a deliberate human-approval gate).


async def handle_pull_request_event(event_data: dict, background_tasks):
    """PR merged — the true terminal success (human-gated, we never auto-merge)."""
    if event_data.get("action") == "closed" and event_data.get("pull_request", {}).get("merged"):
        background_tasks.add_task(handle_pr_merged, event_data["pull_request"])


async def create_remediation_job(issue: dict, repository: dict):
    """Create a job and start a Devin session for a labeled issue."""
    with next(get_session()) as session:
        existing = session.execute(
            select(Job).where(Job.issue_number == issue["number"])
        ).scalar_one_or_none()
        if existing:
            return

        # Cost guard: don't start new Devin work once the daily spend cap is hit.
        if _daily_spend_exceeded(session):
            await github_client.comment_on_issue(
                repository["owner"]["login"], repository["name"], issue["number"],
                "⏸️ Devin auto-fix paused: daily cost cap reached. Will resume next cycle.",
            )
            return

        job = Job(
            issue_number=issue["number"],
            issue_url=issue["html_url"],
            state="queued",
            labeled_at=datetime.now(timezone.utc),
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        session_response = await devin_client.create_session(
            prompt=build_remediation_prompt(issue, repository),
            session_links=[issue["html_url"]],
        )
        job.devin_session_id = session_response.get("session_id")
        job.state = "fixing"
        job.updated_at = datetime.now(timezone.utc)
        session.commit()

        await slack_reporter.report_state_transition(job, None)
        await github_client.comment_on_issue(
            repository["owner"]["login"], repository["name"], issue["number"],
            f"🤖 **Devin auto-fix started**\n\nDevin is working on this dependency "
            f"upgrade. Session: {session_response.get('url')}",
        )


async def handle_ci_failure(check_suite: dict, repository: dict):
    """One bounded repair attempt, then mark checks_failed."""
    with next(get_session()) as session:
        jobs = session.execute(
            select(Job).where(Job.state == "checks_running", Job.attempts < 1)
            .order_by(Job.created_at.desc())
        ).scalars().all()
        if not jobs:
            return
        job = jobs[0]
        if not job.devin_session_id:
            return

        await devin_client.send_message(
            job.devin_session_id,
            f"CI failed for your changes ({check_suite.get('conclusion')}). "
            f"Details: {check_suite.get('details_url')}. Please fix all failing checks.",
        )
        job.attempts += 1
        job.updated_at = datetime.now(timezone.utc)
        session.commit()

        if job.attempts >= 1:
            job.state = "checks_failed"
            job.notes = f"CI failed after repair attempt: {check_suite.get('details_url')}"
            session.commit()
            await slack_reporter.report_state_transition(job, "checks_running")
            await github_reporter.report_state_transition(job, "checks_running")


async def handle_ci_success(check_suite: dict, repository: dict):
    """Checks passed — ready for human review (never auto-merged)."""
    with next(get_session()) as session:
        jobs = session.execute(
            select(Job).where(Job.state == "checks_running").order_by(Job.created_at.desc())
        ).scalars().all()
        if not jobs:
            return
        job = jobs[0]
        previous_state = job.state
        job.state = "checks_passed"
        job.validated_at = datetime.now(timezone.utc)
        job.effort_hours = 2.0  # estimated dev-hours saved per validated job
        job.updated_at = datetime.now(timezone.utc)
        session.commit()
        await slack_reporter.report_state_transition(job, previous_state)
        await github_reporter.report_state_transition(job, previous_state)


async def handle_pr_merged(pr: dict):
    """Mark the job merged once a human merges its PR."""
    with next(get_session()) as session:
        job = session.execute(
            select(Job).where(Job.pr_number == pr["number"])
        ).scalar_one_or_none()
        if job and job.state != "merged":
            previous_state = job.state
            job.state = "merged"
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
            await slack_reporter.report_state_transition(job, previous_state)
            await github_reporter.report_state_transition(job, previous_state)


def build_remediation_prompt(issue: dict, repository: dict) -> str:
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
6. Create a pull request with the complete fix

**Validation:**
- The fix should allow unpinning the dependency
- All tests should pass
- No breaking changes to existing functionality
- Follow the project's coding standards

Please create a pull request with your changes."""
