import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import BackgroundTasks
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Job
from triggers import github


@pytest.mark.parametrize("results, final_state, attempts", [
    (("success",), "checks_passed", 0),
    (("failure", "success"), "checks_passed", 1),
    (("failure", "failure"), "checks_failed", 1),
])
def test_ci_results_request_at_most_one_repair(monkeypatch, results, final_state, attempts):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)

    def get_session():
        with sessions() as session:
            yield session

    monkeypatch.setattr(github, "get_session", get_session)
    devin = AsyncMock()
    slack = AsyncMock()
    reporter = AsyncMock()
    monkeypatch.setattr(github, "devin_client", devin)
    monkeypatch.setattr(github, "slack_reporter", slack)
    monkeypatch.setattr(github, "github_reporter", reporter)

    with sessions() as session:
        job = Job(issue_number=1, pr_number=2, devin_session_id="test-session",
                  state="checks_running")
        session.add(job)
        session.commit()
        job_id = job.id

    async def deliver(conclusion):
        tasks = BackgroundTasks()
        await github.route("check_suite", {
            "action": "completed",
            "repository": {"full_name": "example/repo"},
            "check_suite": {"conclusion": conclusion},
        }, tasks)
        await tasks()

    try:
        for index, result in enumerate(results):
            asyncio.run(deliver(result))
            if index == 0 and result == "failure":
                with sessions() as session:
                    job = session.get(Job, job_id)
                    assert (job.state, job.attempts) == ("checks_running", 1)
                devin.send_message.assert_awaited_once()
                assert devin.send_message.call_args.args[0] == "test-session"
                reporter.report_state_transition.assert_not_awaited()
                slack.report_state_transition.assert_not_awaited()

        with sessions() as session:
            job = session.get(Job, job_id)
            assert (job.state, job.attempts) == (final_state, attempts)
        assert devin.send_message.await_count == attempts
        reporter.report_state_transition.assert_awaited_once()
        slack.report_state_transition.assert_awaited_once()
    finally:
        engine.dispose()
