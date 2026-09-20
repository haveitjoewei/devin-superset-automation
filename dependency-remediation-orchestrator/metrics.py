from sqlalchemy import func, text
from datetime import datetime, timedelta, timezone
from database import SessionLocal
from models import Job

def get_job_metrics():
    """Calculate job metrics for reporting"""
    with SessionLocal() as session:
        # Basic counts
        total_jobs = session.query(func.count(Job.id)).scalar()
        validated_jobs = session.query(func.count(Job.id)).filter(Job.state == "checks_passed").scalar()
        failed_jobs = session.query(func.count(Job.id)).filter(Job.state == "checks_failed").scalar()
        needs_human_jobs = session.query(func.count(Job.id)).filter(Job.state == "needs_human").scalar()

        # Success rate
        completed_jobs = validated_jobs + failed_jobs
        success_rate = (validated_jobs / completed_jobs * 100) if completed_jobs > 0 else 0

        # Throughput (per day/week)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        validated_this_week = session.query(func.count(Job.id)).filter(
            Job.state == "checks_passed",
            Job.validated_at >= week_ago
        ).scalar()
        throughput_per_day = validated_this_week / 7
        throughput_per_week = validated_this_week
        
        # Dev hours saved
        dev_hours_saved = session.query(func.sum(Job.effort_hours)).filter(
            Job.state == "checks_passed"
        ).scalar() or 0
        
        # Devin cost
        devin_cost = session.query(func.sum(Job.cost)).scalar() or 0
        
        # Net saved (assuming $90/hour for dev time)
        net_saved = (dev_hours_saved * 90) - devin_cost
        
        # MTTR (Mean Time To Remediation) - PostgreSQL version
        mttr_results = session.query(
            func.avg(
                func.extract('epoch', Job.validated_at - Job.labeled_at) / 3600
            )
        ).filter(
            Job.state == "checks_passed",
            Job.validated_at.isnot(None),
            Job.labeled_at.isnot(None)
        ).scalar()
        mttr_hours = float(mttr_results) if mttr_results else 0

        # State breakdown
        state_breakdown = {}
        for state in ["queued", "fixing", "checks_running", "checks_passed", "merged", "checks_failed", "needs_human"]:
            count = session.query(func.count(Job.id)).filter(Job.state == state).scalar()
            state_breakdown[state] = count
        
        return {
            "success_rate": round(success_rate, 2),
            "throughput_per_day": round(throughput_per_day, 2),
            "throughput_per_week": throughput_per_week,
            "dev_hours_saved": round(dev_hours_saved, 2),
            "devin_cost": round(devin_cost, 2),
            "net_saved": round(net_saved, 2),
            "mttr_hours": round(mttr_hours, 2),
            "state_breakdown": state_breakdown,
            "total_jobs": total_jobs,
            "validated_jobs": validated_jobs,
            "failed_jobs": failed_jobs,
            "needs_human_jobs": needs_human_jobs
        }