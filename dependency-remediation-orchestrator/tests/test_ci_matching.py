"""check_suite results must resolve to the specific job by PR number — so two
concurrent jobs are never confused (the old code picked 'the latest waiting job')."""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base, Job
from triggers.github import _job_for_pr


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_matches_the_specific_pr_not_the_latest():
    s = _session()
    s.add_all([
        Job(issue_number=1, state="checks_running", pr_number=100),
        Job(issue_number=2, state="checks_running", pr_number=200),  # the "latest"
    ])
    s.commit()
    # a result for PR 100 must resolve to job 100, even though job 200 is newer
    assert _job_for_pr(s, [100]).pr_number == 100
    assert _job_for_pr(s, [200]).pr_number == 200


def test_no_pr_reference_or_no_match_returns_none():
    s = _session()
    s.add(Job(issue_number=1, state="checks_running", pr_number=100))
    s.commit()
    assert _job_for_pr(s, []) is None        # unrelated check_suite with no PRs
    assert _job_for_pr(s, [999]) is None     # PR nobody owns


def test_only_matches_active_jobs():
    s = _session()
    s.add(Job(issue_number=1, state="merged", pr_number=100))
    s.commit()
    assert _job_for_pr(s, [100]) is None      # already merged — not checks_running
