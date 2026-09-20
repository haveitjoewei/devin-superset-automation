"""Slack threading: root creates the thread, updates nest, a missing thread self-heals."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from reporters.slack import SlackReporter


def _job(**kw):
    base = dict(id=1, devin_session_id="s1", issue_url="https://github.com/o/r/issues/1",
                issue_number=1, state="fixing", pr_number=None, attempts=0, slack_thread_ts=None)
    base.update(kw)
    return SimpleNamespace(**base)


def _reporter(monkeypatch):
    # no-op the DB write inside _ensure_thread
    cm = MagicMock()
    cm.__enter__.return_value = MagicMock()
    cm.__exit__.return_value = False
    monkeypatch.setattr("reporters.slack.SessionLocal", lambda: cm)

    r = SlackReporter()
    r.slack = MagicMock()
    r.slack.bot_token = "xoxb-test"
    r.slack.post_message = AsyncMock(return_value={"ok": True, "ts": "111.22",
                                                   "message": {"ts": "111.22"}})
    r.slack.notify_oncall = AsyncMock(return_value={"ok": True})
    return r


def test_root_creates_thread_and_saves_ts(monkeypatch):
    r = _reporter(monkeypatch)
    job = _job()
    asyncio.run(r.report_state_transition(job, None))
    r.slack.post_message.assert_awaited_once()           # only the root
    assert job.slack_thread_ts == "111.22"               # ts captured in memory


def test_update_posts_into_existing_thread(monkeypatch):
    r = _reporter(monkeypatch)
    job = _job(state="checks_running", pr_number=29, slack_thread_ts="999.88")
    asyncio.run(r.report_state_transition(job, "fixing"))
    # posted the update with the existing thread_ts
    _, kwargs = r.slack.post_message.call_args
    args = r.slack.post_message.call_args.args
    assert "999.88" in (list(args) + list(kwargs.values()))


def test_missing_thread_self_heals(monkeypatch):
    r = _reporter(monkeypatch)
    job = _job(state="checks_running", pr_number=29, slack_thread_ts=None)
    asyncio.run(r.report_state_transition(job, "fixing"))
    # root created first, then the update -> two posts, no dropped message
    assert r.slack.post_message.await_count == 2
    assert job.slack_thread_ts == "111.22"
