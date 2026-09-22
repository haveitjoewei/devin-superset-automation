"""Simulate a GitHub `check_suite=success` webhook to validate the checking job.

Deliberately simulated: Apache Superset's PR CI is heavy/slow and fork PRs need
maintainer approval before CI runs, so for the demo we drive validation locally.
In production this event comes from GitHub's real check_suite webhook.

Usage:
    python scripts/simulate_ci.py <pr_number> [--repo owner/repo] [--conclusion success|failure]

The PR number is required: the API matches the check result to the specific job that
owns that PR (so concurrent jobs are never confused), exactly as a real check_suite
webhook carries its `pull_requests`.

Env: GITHUB_WEBHOOK_SECRET (from .env), API_URL (default http://localhost:8000)
"""
import sys, os, json, hmac, hashlib, subprocess, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import httpx
from config import settings

DEFAULT_REPO = "haveitjoewei/superset"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pr_number", type=int, help="the PR whose checks completed")
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--conclusion", default="success", choices=["success", "failure"])
    ap.add_argument("--api-url", default=os.environ.get("API_URL", "http://localhost:8000"))
    args = ap.parse_args()

    repo = json.loads(subprocess.check_output(["gh", "api", f"repos/{args.repo}"]))
    payload = {
        "check_suite": {
            "conclusion": args.conclusion,
            "id": 0,
            "pull_requests": [{"number": args.pr_number}],
        },
        "repository": repo,
    }
    body = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(settings.GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

    r = httpx.post(f"{args.api_url}/webhook/github", content=body,
                   headers={"x-hub-signature-256": sig, "x-github-event": "check_suite",
                            "content-type": "application/json"}, timeout=30)
    print("check_suite:", r.status_code, r.text)


if __name__ == "__main__":
    main()
