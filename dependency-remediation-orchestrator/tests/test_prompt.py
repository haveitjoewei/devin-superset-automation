"""The Devin prompt carries the issue context."""
from triggers.github import build_remediation_prompt


def test_prompt_includes_issue_and_repo():
    issue = {"title": "Unpin apispec", "body": "6.7.0 breaks a test"}
    repo = {"full_name": "haveitjoewei/superset"}
    prompt = build_remediation_prompt(issue, repo)
    assert "Unpin apispec" in prompt
    assert "6.7.0 breaks a test" in prompt
    assert "haveitjoewei/superset" in prompt
    assert "pull request" in prompt.lower()
