import asyncio
from unittest.mock import AsyncMock
import pytest
from fastapi import BackgroundTasks
from models import Job
from triggers import github

REPO = "haveitjoewei/superset"


@pytest.fixture
def ci(jobs_db, monkeypatch):
    with jobs_db() as session:
        session.add(Job(issue_number=1, issue_url=f"https://github.com/{REPO}/issues/1",
                        pr_number=2, devin_session_id="test", state="checks_running"))
        session.commit()
    for name in ("devin_client", "github_client", "slack_reporter", "github_reporter"):
        monkeypatch.setattr(github, name, AsyncMock())
    return jobs_db


def deliver(result, sha="a"):
    github.github_client.verification.return_value = (sha, result, "test details")
    asyncio.run(github.reconcile_ci(2))


@pytest.mark.parametrize("results,state,attempts", [
    ([('a', 'success')], 'checks_passed', 0),
    ([('a', 'failure'), ('b', 'success')], 'checks_passed', 1),
    ([('a', 'failure'), ('b', 'failure')], 'checks_failed', 1),
    ([('a', 'failure'), ('a', 'failure')], 'checks_running', 1),
    ([('a', 'success'), ('a', 'failure')], 'checks_running', 1),
    ([('a', 'success'), ('b', 'pending')], 'checks_running', 0),
])
def test_ci_transitions(ci, results, state, attempts):
    for sha, result in results:
        deliver(result, sha)
    with ci() as session:
        job = session.get(Job, 1)
        assert (job.state, job.attempts) == (state, attempts)
    assert github.devin_client.send_message.await_count == attempts


def test_foreign_repository_is_ignored(ci):
    async def run():
        tasks = BackgroundTasks()
        await github.route("check_suite", {"action": "completed", "repository": {"full_name": "other/repo"},
                         "check_suite": {"pull_requests": [{"number": 2}], "conclusion": "success"}}, tasks)
        await tasks()
    asyncio.run(run())
    github.github_client.verification.assert_not_awaited()


def test_simulation_requires_opt_in(ci, monkeypatch):
    monkeypatch.setattr(github.settings, "ALLOW_SIMULATED_EVENTS", False)
    asyncio.run(github.reconcile_ci(2, {"head_sha": "sim-a", "conclusion": "success"}))
    with ci() as session:
        assert session.get(Job, 1).state == "checks_running"
    monkeypatch.setattr(github.settings, "ALLOW_SIMULATED_EVENTS", True)
    asyncio.run(github.reconcile_ci(2, {"head_sha": "sim-a", "conclusion": "success"}))
    with ci() as session:
        assert session.get(Job, 1).is_simulated == 1


def test_repair_timeout_does_not_send_twice(ci):
    github.devin_client.send_message.side_effect = TimeoutError()
    deliver("failure")
    deliver("failure")
    with ci() as session:
        assert session.get(Job, 1).state == "needs_human"
    github.devin_client.send_message.assert_awaited_once()


def test_notification_failure_preserves_verified_state(ci):
    github.slack_reporter.report_state_transition.side_effect = RuntimeError()
    deliver("success")
    with ci() as session:
        assert session.get(Job, 1).state == "checks_passed"
    github.github_reporter.report_state_transition.assert_awaited_once()


def test_delayed_read_cannot_overwrite_newer_result(ci):
    async def stale_read(*args):
        with ci() as session:
            job = session.get(Job, 1)
            from datetime import datetime, timezone, timedelta
            job.updated_at = datetime.now(timezone.utc) + timedelta(seconds=1)
            job.state = "checks_failed"
            session.commit()
        return "old", "success", "stale response"
    github.github_client.verification.side_effect = stale_read
    asyncio.run(github.reconcile_ci(2))
    with ci() as session:
        assert session.get(Job, 1).state == "checks_failed"
