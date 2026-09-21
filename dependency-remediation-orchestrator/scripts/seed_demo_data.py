"""Seed representative demo data so the Superset dashboard shows a real steady state.

Generates ~8 weeks of jobs across states, streams, cost and time — a healthy
pipeline a leader would recognize (high success rate, a few failures, some active).
Only demo rows (devin_session_id LIKE 'demo-%') are cleared; real jobs are kept.

NOTE: this is representative demo data to illustrate the dashboard's shape, not
live production numbers.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timedelta, timezone

from database import SessionLocal, init_db
from models import Job

random.seed(42)  # reproducible

DEPS = [
    ("apispec", "dependency"), ("setuptools", "dependency"), ("async_timeout", "dependency"),
    ("testcontainers", "dependency"), ("cryptography", "dependency"), ("werkzeug", "dependency"),
    ("marshmallow-sqlalchemy", "dependency"), ("pyarrow", "dependency"), ("urllib3", "dependency"),
    ("sqlalchemy", "dependency"), ("flask", "dependency"), ("redis", "dependency"),
    ("pandas", "dependency"), ("celery", "dependency"), ("pyopenssl", "dependency"),
]
# outcome distribution (state, weight)
OUTCOMES = (["merged"] * 30 + ["checks_passed"] * 6 + ["checks_failed"] * 6 +
            ["needs_human"] * 3 + ["fixing"] * 2 + ["checks_running"] * 2)


def _note(dep, stream):
    if stream == "test":
        return f"Re-enabled skipped test after {dep} upgrade"
    if stream == "bug":
        return f"Fixed bug surfaced by {dep} upgrade"
    return f"Unblocked {dep} dependency upgrade"


def seed_demo_data():
    init_db()
    now = datetime.now(timezone.utc)
    with SessionLocal() as session:
        session.query(Job).filter(Job.devin_session_id.like("demo-%")).delete(synchronize_session=False)
        session.commit()

        n = 60
        for i in range(n):
            state = random.choice(OUTCOMES)
            # stream mix: ~68% dependency, ~20% test, ~12% bug
            stream = random.choices(["dependency", "test", "bug"], weights=[68, 20, 12])[0]
            dep = random.choice(DEPS)[0]

            labeled = now - timedelta(days=random.uniform(0, 56), hours=random.uniform(0, 24))
            effort = {"dependency": random.uniform(2, 4), "test": random.uniform(1, 3),
                      "bug": random.uniform(3, 6)}[stream]
            cost = round(random.uniform(3, 22), 2)

            job = Job(
                issue_number=9000 + i,
                issue_url=f"https://github.com/haveitjoewei/superset/issues/{9000 + i}",
                devin_session_id=f"demo-{i:03d}",
                state=state,
                attempts=1 if state == "checks_failed" else 0,
                cost=cost,
                effort_hours=round(effort, 1),
                notes=_note(dep, stream),
                labeled_at=labeled,
            )
            if state in ("merged", "checks_passed"):
                # MTTR: mostly hours, occasional multi-day
                mttr_h = random.choice([random.uniform(0.3, 8)] * 4 + [random.uniform(8, 72)])
                job.validated_at = labeled + timedelta(hours=mttr_h)
                job.pr_number = 4000 + i
            job.created_at = labeled
            job.updated_at = job.validated_at or labeled
            session.add(job)

        session.commit()
        total = session.query(Job).count()
        print(f"Seeded 60 demo jobs (kept real jobs). Total rows: {total}")


if __name__ == "__main__":
    seed_demo_data()
