"""Simulate a GitHub `pull_request` merged webhook -> marks the job `merged`.

The real event fires when a human merges the PR (we never auto-merge). This lets
the demo show the full lifecycle end state locally.

Usage:
    python scripts/simulate_merge.py <pr_number> [--repo owner/repo]

Env: GITHUB_WEBHOOK_SECRET (from .env), API_URL (default http://localhost:8000)
"""
import sys, os, json, hmac, hashlib, subprocess, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import httpx
from config import settings

DEFAULT_REPO = "haveitjoewei/superset"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pr_number", type=int)
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--api-url", default=os.environ.get("API_URL", "http://localhost:8000"))
    args = ap.parse_args()
    if not settings.ALLOW_SIMULATED_EVENTS:
        ap.error("Set ALLOW_SIMULATED_EVENTS=true in the local demo environment first.")

    repo = json.loads(subprocess.check_output(["gh", "api", f"repos/{args.repo}"]))
    payload = {"simulated": True, "action": "closed",
               "pull_request": {"number": args.pr_number, "merged": True},
               "repository": repo}
    body = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(settings.GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

    r = httpx.post(f"{args.api_url}/webhook/github", content=body,
                   headers={"x-hub-signature-256": sig, "x-github-event": "pull_request",
                            "content-type": "application/json"}, timeout=30)
    print("pull_request(merged):", r.status_code, r.text)


if __name__ == "__main__":
    main()
