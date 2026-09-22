"""Receive approved issues and reconcile checks against GitHub's current PR state."""
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from config import settings
from database import get_session
from models import Job
from devin_client import DevinClient
from github_client import GitHubClient
from reporters import SlackReporter, GitHubReporter

logger = logging.getLogger(__name__)
devin_client = DevinClient()
github_client = GitHubClient()
slack_reporter = SlackReporter()
github_reporter = GitHubReporter()


async def report(job, previous_state):
    for reporter in (slack_reporter, github_reporter):
        try:
            await reporter.report_state_transition(job, previous_state)
        except Exception:
            logger.exception("Notification failed for job %s; workflow state preserved", job.id)


async def route(event_type: str, event_data: dict, background_tasks):
    repository = event_data.get("repository") or {}
    if repository.get("full_name", "").lower() != settings.TARGET_REPO.lower():
        return
    simulated = event_data.get("simulated") is True
    if simulated and not settings.ALLOW_SIMULATED_EVENTS:
        return
    if event_type == "issues":
        issue = event_data.get("issue") or {}
        if event_data.get("action") == "labeled" and "devin-fix" in [l["name"] for l in issue.get("labels", [])]:
            # Persist before acknowledging the webhook; the worker starts paid work.
            await create_remediation_job(issue, repository)
    elif event_type == "check_suite" and event_data.get("action") == "completed":
        suite = event_data.get("check_suite") or {}
        for pr in suite.get("pull_requests", []):
            if pr.get("number"):
                background_tasks.add_task(reconcile_ci, pr["number"], suite if simulated else None)
    elif event_type == "pull_request":
        pr = event_data.get("pull_request") or {}
        if event_data.get("action") == "closed" and pr.get("merged"):
            background_tasks.add_task(handle_pr_merged, pr, simulated)
        elif event_data.get("action") in ("synchronize", "reopened"):
            background_tasks.add_task(reconcile_ci, pr["number"])


def _job_for_pr(session, pr_numbers: list):
    if not pr_numbers:
        return None
    return session.execute(select(Job).where(
        Job.state.in_(["checks_running", "checks_passed", "checks_failed"]),
        Job.pr_number.in_(pr_numbers),
        Job.issue_url.startswith(f"https://github.com/{settings.TARGET_REPO}/issues/"),
    ).with_for_update()).scalars().first()


async def create_remediation_job(issue: dict, repository: dict):
    if repository.get("full_name", "").lower() != settings.TARGET_REPO.lower():
        return
    with next(get_session()) as session:
        if session.execute(select(Job).where(Job.issue_number == issue["number"])).scalar_one_or_none():
            return
        session.add(Job(issue_number=issue["number"], issue_url=issue["html_url"],
                        state="queued", labeled_at=datetime.now(timezone.utc)))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()


async def reconcile_ci(pr_number: int, simulated_suite=None):
    with next(get_session()) as session:
        observed = _job_for_pr(session, [pr_number])
        if not observed:
            return
        observed_version = observed.updated_at
        session.rollback()  # never hold a database lock across an HTTP request
    if simulated_suite is not None:
        if not settings.ALLOW_SIMULATED_EVENTS:
            return
        sha = simulated_suite.get("head_sha")
        result = simulated_suite.get("conclusion")
        if not sha or result not in ("success", "failure"):
            return
        details = f"Simulated {result}; no tests were run."
    else:
        try:
            sha, result, details = await github_client.verification(settings.TARGET_REPO, pr_number)
        except Exception:
            logger.exception("Could not verify PR %s; retrying on the next worker poll", pr_number)
            return

    with next(get_session()) as session:
        job = _job_for_pr(session, [pr_number])
        if not job or (job.is_simulated and simulated_suite is None):
            return
        if job.updated_at != observed_version:
            return  # another handler advanced this job while GitHub was being read
        previous_state = job.state
        job.is_simulated = int(bool(job.is_simulated or simulated_suite is not None))
        job.ci_head_sha = sha
        job.updated_at = datetime.now(timezone.utc)
        job.notes = details
        if result == "success":
            job.state = "checks_passed"
            job.validated_at = job.validated_at or datetime.now(timezone.utc)
            job.effort_hours = 2.0
        elif result == "pending":
            job.state = "checks_running"
            job.validated_at = None
        elif result == "failure":
            job.validated_at = None
            if job.ci_repair_sha == sha:
                # Replayed failures and other suites on the same commit are one attempt.
                job.state = "checks_running"
                session.commit()
                return
            if job.attempts or not job.devin_session_id:
                job.state = "checks_failed"
            else:
                job.attempts = 1
                job.ci_repair_sha = sha
                job.state = "checks_running"
                job.notes = f"Repair requested for {sha}: {details}"
                session.commit()  # reserve the repair before the external call
                try:
                    await devin_client.send_message(job.devin_session_id,
                        f"CI failed on commit {sha}. {details}. Please fix the failing checks.")
                except Exception:
                    job.state = "needs_human"
                    job.notes = "Repair request could not be confirmed. Check Devin before retrying."
                    session.commit()
                    await report(job, previous_state)
                return
        job.updated_at = datetime.now(timezone.utc)
        session.commit()
        if job.state != previous_state:
            await report(job, previous_state)


async def handle_pr_merged(pr: dict, simulated=False):
    if not simulated:
        pr = await github_client.get(f"repos/{settings.TARGET_REPO}/pulls/{pr['number']}")
        if not pr.get("merged"):
            return
    with next(get_session()) as session:
        job = _job_for_pr(session, [pr["number"]])
        if job:
            previous_state = job.state
            job.state = "merged"
            job.is_simulated = int(bool(job.is_simulated or simulated))
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
            await report(job, previous_state)


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
