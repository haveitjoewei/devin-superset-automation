import asyncio
from unittest.mock import AsyncMock
import pytest
from models import Job
import worker
import metrics
from triggers import github
from github_client import GitHubClient

REPO = "haveitjoewei/superset"


def job(number=1, **kwargs):
    return Job(issue_number=number, issue_url=f"https://github.com/{REPO}/issues/{number}", **kwargs)


def setup_worker(monkeypatch):
    monkeypatch.setattr(worker, "devin_client", AsyncMock())
    monkeypatch.setattr(worker, "github_client", AsyncMock())
    monkeypatch.setattr(worker, "slack_reporter", AsyncMock())
    monkeypatch.setattr(worker, "github_reporter", AsyncMock())
    worker.github_client.get.return_value = {"title": "Upgrade", "labels": [{"name": "devin-fix"}]}
    worker.devin_client.create_session.return_value = {"session_id": "session"}
    worker.devin_client.get_session.return_value = {"status": "running", "acus_consumed": 1}


def test_webhooks_queue_and_worker_enforces_cap(jobs_db, monkeypatch):
    setup_worker(monkeypatch)
    monkeypatch.setattr(worker.settings, "CONCURRENCY_CAP", 1)
    for n in range(1, 4):
        asyncio.run(github.create_remediation_job({"number": n, "html_url": job(n).issue_url}, {"full_name": REPO}))
    worker.devin_client.create_session.assert_not_awaited()
    worker.process_jobs()
    worker.process_jobs()
    assert worker.devin_client.create_session.await_count == 1
    with jobs_db() as s:
        assert [j.state for j in s.query(Job).order_by(Job.id)] == ["fixing", "queued", "queued"]


def test_creation_timeout_is_visible_and_not_retried(jobs_db, monkeypatch):
    setup_worker(monkeypatch)
    worker.devin_client.create_session.side_effect = TimeoutError()
    with jobs_db() as s:
        s.add(job(state="queued")); s.commit()
    worker.process_jobs()
    worker.process_jobs()
    with jobs_db() as s:
        assert s.get(Job, 1).state == "needs_human"
    worker.devin_client.create_session.assert_awaited_once()


def test_reporter_outage_does_not_lose_pr(jobs_db, monkeypatch):
    setup_worker(monkeypatch)
    worker.slack_reporter.report_state_transition.side_effect = RuntimeError()
    worker.devin_client.get_session.return_value = {"pull_requests": [{"pr_url": f"https://github.com/{REPO}/pull/2"}]}
    with jobs_db() as s:
        j = job(state="fixing", devin_session_id="session"); s.add(j); s.commit()
        worker.poll_session(j, s)
        assert (j.state, j.pr_number) == ("checks_running", 2)
    worker.github_reporter.report_state_transition.assert_awaited_once()


def test_read_timeout_retries_without_changing_outcome(jobs_db, monkeypatch):
    setup_worker(monkeypatch)
    worker.devin_client.get_session.side_effect = TimeoutError()
    with jobs_db() as s:
        j = job(state="fixing", devin_session_id="session"); s.add(j); s.commit()
        worker.poll_session(j, s)
        assert j.state == "fixing"


def test_metrics_count_escalations_and_exclude_samples(jobs_db):
    with jobs_db() as s:
        s.add(job(state="checks_passed", ci_head_sha="a", acu_usage=1, effort_hours=2))
        s.add_all(job(n, state="needs_human") for n in range(2, 11))
        s.add(job(11, state="merged", is_simulated=1, acu_usage=999))
        s.add(job(12, state="merged", devin_session_id="demo-1"))
        s.commit()
    result = metrics.get_job_metrics()
    assert result["success_rate"] == 10
    assert result["total_jobs"] == 10
    assert result["excluded_simulated_jobs"] == 2
    assert result["acu_usage"] == 1
    assert result["net_saved"] is None


def test_fake_active_session_never_polled(jobs_db, monkeypatch):
    setup_worker(monkeypatch)
    with jobs_db() as s:
        s.add(job(state="fixing", devin_session_id="demo-1")); s.commit()
    worker.process_jobs()
    worker.devin_client.get_session.assert_not_awaited()


def run(name, conclusion="success", status="completed", sha="a", identifier=1):
    return {"id": identifier, "name": name, "conclusion": conclusion, "status": status,
            "head_sha": sha, "app": {"slug": "github-actions"}, "html_url": "https://github.com/check"}


@pytest.mark.parametrize("runs,expected", [
    ([run("unit"), run("integration")], "success"),
    ([run("unit")], "pending"),
    ([run("unit"), run("integration", "failure")], "failure"),
    ([run("unit"), run("integration", None, "in_progress")], "pending"),
    ([run("unit"), run("integration", sha="old")], "pending"),
    ([run("unit"), run("integration", "skipped")], "failure"),
    ([run("unit"), run("integration"), run("integration", "failure", identifier=2)], "failure"),
])
def test_checks_require_complete_current_commit(monkeypatch, runs, expected):
    monkeypatch.setattr(worker.settings, "REQUIRED_CHECKS", "unit,integration")
    client = GitHubClient()
    client.get = AsyncMock(side_effect=[{"head": {"sha": "a"}}, {"check_runs": runs}, {"head": {"sha": "a"}}])
    sha, result, _ = asyncio.run(client.verification(REPO, 2))
    assert (sha, result) == ("a", expected)


def test_head_changed_while_reading_checks(monkeypatch):
    monkeypatch.setattr(worker.settings, "REQUIRED_CHECKS", "unit")
    client = GitHubClient()
    client.get = AsyncMock(side_effect=[{"head": {"sha": "a"}}, {"check_runs": [run("unit")]}, {"head": {"sha": "b"}}])
    assert asyncio.run(client.verification(REPO, 2))[:2] == ("b", "pending")


def test_empty_verification_configuration_never_passes(monkeypatch):
    monkeypatch.setattr(worker.settings, "REQUIRED_CHECKS", "")
    client = GitHubClient()
    client.get = AsyncMock(return_value={"head": {"sha": "a"}})
    assert asyncio.run(client.verification(REPO, 2))[1] == "pending"
