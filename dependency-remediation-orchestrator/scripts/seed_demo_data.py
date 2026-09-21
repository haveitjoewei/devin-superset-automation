"""Seed a small, believable baseline so the dashboard looks alive — then run a REAL
job in the demo to visibly move the needle.

Generates ~10 jobs over the last few weeks (a young pipeline a leader would
recognize), then during the demo you label a real issue (e.g. apispec) and watch
the tiles update live. Only demo rows (devin_session_id LIKE 'demo-%') are cleared;
real jobs are kept.

  python scripts/seed_demo_data.py [count]      # default 10

NOTE: representative demo data to show the dashboard's shape; production is live.
`apispec` is intentionally excluded — reserve it for the live demo run.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timedelta, timezone

from database import SessionLocal, init_db
from models import Job

random.seed(42)  # reproducible

# apispec deliberately omitted — leave it for the live demo run.
DEPS = ["werkzeug", "cryptography", "urllib3", "pyarrow", "marshmallow-sqlalchemy",
        "redis", "celery", "sqlalchemy", "flask", "setuptools", "pyopenssl"]
# a small young-pipeline mix: mostly shipped, one failure, one escalation, one active
OUTCOMES = (["merged"] * 6 + ["checks_passed"] * 1 + ["checks_failed"] * 1 +
            ["needs_human"] * 1 + ["fixing"] * 1)


def _note(dep, stream):
    if stream == "test":
        return f"Re-enabled skipped test after {dep} upgrade"
    if stream == "bug":
        return f"Fixed bug surfaced by {dep} upgrade"
    return f"Unblocked {dep} dependency upgrade"


def seed_demo_data(count=10):
    init_db()
    now = datetime.now(timezone.utc)
    with SessionLocal() as session:
        session.query(Job).filter(Job.devin_session_id.like("demo-%")).delete(synchronize_session=False)
        session.commit()

        pool = OUTCOMES[:]
        random.shuffle(pool)
        for i in range(count):
            state = pool[i % len(pool)]
            stream = random.choices(["dependency", "test", "bug"], weights=[70, 20, 10])[0]
            dep = random.choice(DEPS)

            labeled = now - timedelta(days=random.uniform(0, 21), hours=random.uniform(0, 24))
            effort = {"dependency": random.uniform(2, 4), "test": random.uniform(1, 3),
                      "bug": random.uniform(3, 6)}[stream]
            cost = round(random.uniform(4, 18), 2)

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
                mttr_h = random.choice([random.uniform(0.3, 8)] * 4 + [random.uniform(8, 48)])
                job.validated_at = labeled + timedelta(hours=mttr_h)
                job.pr_number = 4000 + i
            job.created_at = labeled
            job.updated_at = job.validated_at or labeled
            session.add(job)

        session.commit()
        total = session.query(Job).count()
        print(f"Seeded {count} demo jobs (kept real jobs). Total rows: {total}")


if __name__ == "__main__":
    seed_demo_data(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
