"""The worker's PR-number extraction — the field-name bug that stalled the lifecycle."""
from worker import extract_pr_number


def test_extracts_from_devin_pr_url():
    prs = [{"pr_url": "https://github.com/o/r/pull/29", "pr_state": "open"}]
    assert extract_pr_number(prs) == 29


def test_extracts_from_legacy_url_field():
    prs = [{"url": "https://github.com/o/r/pull/7"}]
    assert extract_pr_number(prs) == 7


def test_none_when_no_pr():
    assert extract_pr_number([]) is None
    assert extract_pr_number(None) is None


def test_none_when_url_has_no_pull_segment():
    assert extract_pr_number([{"pr_url": "https://github.com/o/r"}]) is None
