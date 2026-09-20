"""Simulate a GitHub `issues.labeled` webhook to trigger the pipeline locally.

GitHub can't reach a localhost API, so this replays the same signed event the
real webhook would send. Fetches the real issue + repo via `gh`.

Usage:
    python scripts/simulate_issue.py <issue_number> [--repo owner/repo]

Env: GITHUB_WEBHOOK_SECRET (from .env), API_URL (default http://localhost:8000)
"""
import sys, os, json, hmac, hashlib, subprocess, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import httpx
from config import settings

DEFAULT_REPO = "haveitjoewei/superset"


def gh_json(path):
    return json.loads(subprocess.check_output(["gh", "api", path]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue_number", type=int)
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--api-url", default=os.environ.get("API_URL", "http://localhost:8000"))
    args = ap.parse_args()

    issue = gh_json(f"repos/{args.repo}/issues/{args.issue_number}")
    repo = gh_json(f"repos/{args.repo}")
    payload = {"action": "labeled", "issue": issue, "repository": repo,
               "label": {"name": "devin-fix"}}
    body = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(settings.GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

    r = httpx.post(f"{args.api_url}/webhook/github", content=body,
                   headers={"x-hub-signature-256": sig, "x-github-event": "issues",
                            "content-type": "application/json"}, timeout=30)
    print("webhook:", r.status_code, r.text)


if __name__ == "__main__":
    main()
