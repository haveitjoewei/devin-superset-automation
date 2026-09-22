from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from database import SessionLocal
from models import Job

SUCCESS_STATES = {"checks_passed", "merged"}
STATES = ["queued", "starting", "fixing", "checks_running", "checks_passed", "merged", "checks_failed", "needs_human"]


def get_job_metrics():
    with SessionLocal() as session:
        all_jobs = session.execute(select(Job)).scalars().all()
        jobs = [j for j in all_jobs if not j.is_simulated and not (j.devin_session_id or "").startswith("demo-")]
        # Historical passes lack a verified commit; do not present them as measured success.
        passed = [j for j in jobs if j.state in SUCCESS_STATES and j.ci_head_sha]
        failed = sum(j.state == "checks_failed" for j in jobs)
        needs_human = sum(j.state == "needs_human" for j in jobs)
        unverified = sum(j.state in SUCCESS_STATES and not j.ci_head_sha for j in jobs)
        completed = len(passed) + failed + needs_human + unverified
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        weekly = sum(j.validated_at is not None and j.validated_at.replace(tzinfo=timezone.utc) >= week_ago for j in passed)
        durations = [(j.validated_at - j.labeled_at).total_seconds() / 3600 for j in passed if j.validated_at and j.labeled_at]
        return {
            "success_rate": round(100 * len(passed) / completed, 2) if completed else 0,
            "success_rate_basis": "Verified successes / (successes + failures + escalations + unverified outcomes)",
            "throughput_per_day": round(weekly / 7, 2),
            "throughput_per_week": weekly,
            "estimated_dev_hours_saved": round(sum(j.effort_hours for j in passed), 2),
            "acu_usage": round(sum(j.acu_usage or 0 for j in jobs), 2),
            "usage_unknown_jobs": sum(j.acu_usage is None for j in jobs),
            "devin_cost": None,
            "net_saved": None,
            "mttr_hours": round(sum(durations) / len(durations), 2) if durations else 0,
            "state_breakdown": {state: sum(j.state == state for j in jobs) for state in STATES},
            "total_jobs": len(jobs),
            "validated_jobs": len(passed),
            "failed_jobs": failed,
            "needs_human_jobs": needs_human,
            "unverified_outcomes": unverified,
            "excluded_simulated_jobs": len(all_jobs) - len(jobs),
        }
