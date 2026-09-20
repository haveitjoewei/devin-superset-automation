"""GitHub lifecycle comments: no redundant PR comment on open, disclaimer on pass, merged msg."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from reporters.github import GitHubReporter


def _job(**kw):
    base = dict(issue_url="https://github.com/haveitjoewei/superset/issues/28",
                issue_number=28, pr_number=29, state="checks_running", notes="")
    base.update(kw)
    return SimpleNamespace(**base)


def _reporter():
    r = GitHubReporter()
    r.gh = AsyncMock()
    return r


def test_pr_opened_comments_issue_only_not_pr():
    r = _reporter()
    asyncio.run(r.report_state_transition(_job(state="checks_running"), "fixing"))
    # exactly one comment (on the issue) — the redundant PR-side comment was removed
    assert r.gh.comment_on_issue.await_count == 1
    target = r.gh.comment_on_issue.call_args.args[2]
    assert target == 28


def test_checks_passed_posts_disclaimer():
    r = _reporter()
    asyncio.run(r.report_state_transition(_job(state="checks_passed"), "checks_running"))
    bodies = " ".join(str(c.args[3]) for c in r.gh.comment_on_issue.call_args_list)
    assert "simulated" in bodies.lower()
    assert "not auto-merged" in bodies.lower()


def test_merged_comment():
    r = _reporter()
    asyncio.run(r.report_state_transition(_job(state="merged"), "checks_passed"))
    body = r.gh.comment_on_issue.call_args.args[3]
    assert "merged" in body.lower()


def test_needs_human_comment():
    r = _reporter()
    asyncio.run(r.report_state_transition(_job(state="needs_human", notes="no PR"), "fixing"))
    body = r.gh.comment_on_issue.call_args.args[3]
    assert "needs attention" in body.lower()
