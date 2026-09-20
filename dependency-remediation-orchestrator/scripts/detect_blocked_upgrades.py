"""Detect blocked dependency upgrades and file issues for human approval.

Scans a target repo's requirements/*.in for dependencies pinned with an upper
bound whose comment explains a *blocker* (a test breaks, a regression, needs
attention) — the exact "dead lane" this system fixes. For each one without an
existing open issue, it opens an issue (UNLABELED). A human then applies the
`devin-fix` label to approve, which triggers the pipeline.

Discovery is automated; the approval and the merge stay human. Security-motivated
caps (comments starting with "Security:"/CVE) are skipped — those are already
remediated, not blocked upgrades.

Usage:
    python scripts/detect_blocked_upgrades.py [--repo owner/repo] [--dry-run]

Requires: `gh` authenticated with issue read/write on the target repo.
"""
import argparse
import base64
import json
import re
import subprocess

DEFAULT_REPO = "haveitjoewei/superset"
REQ_FILES = ["requirements/base.in", "requirements/development.in"]

# a comment signals a *blocker* (vs a plain/security cap) if it mentions any of these
BLOCKER_HINTS = ["break", "regression", "known issue", "attention", "until",
                 "incompat", "do not", "doesn't", "does not", "blocked", "needs",
                 "deprecat"]
SKIP_HINTS = ["security:", "cve-"]  # already-remediated caps, not blocked upgrades

DEP_RE = re.compile(r"^([A-Za-z0-9._-]+(?:\[[^\]]+\])?)\s*(.*<[0-9].*)$")


def gh_json(args):
    return json.loads(subprocess.check_output(["gh"] + args))


def fetch_file(repo, path):
    try:
        data = gh_json(["api", f"repos/{repo}/contents/{path}"])
        return base64.b64decode(data["content"]).decode()
    except subprocess.CalledProcessError:
        return ""


def find_blocked(text, path):
    """Yield (name, constraint, reason, path) for capped deps with a blocker comment."""
    comment = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            comment.append(s.lstrip("# ").strip())
            continue
        if not s:
            comment = []
            continue
        m = DEP_RE.match(s)
        if m:
            reason = " ".join(comment).strip()
            low = reason.lower()
            if reason and any(h in low for h in BLOCKER_HINTS) and not any(h in low for h in SKIP_HINTS):
                yield m.group(1), m.group(2).strip(), reason, path
        comment = []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    blocked = []
    for path in REQ_FILES:
        text = fetch_file(args.repo, path)
        blocked.extend(find_blocked(text, path))

    open_titles = [i["title"].lower() for i in
                   gh_json(["issue", "list", "--repo", args.repo, "--state", "open",
                            "--limit", "200", "--json", "title"])]

    created, skipped = 0, 0
    for name, constraint, reason, path in blocked:
        title = f"chore(deps): unblock {name} (pinned {constraint})"
        if any(f"unblock {name.lower()}" in t for t in open_titles):
            print(f"skip (issue exists): {name}")
            skipped += 1
            continue
        body = (f"Automated detection: **{name}** is pinned `{constraint}` in `{path}`.\n\n"
                f"**Why it's blocked:** {reason}\n\n"
                f"**Task:** raise/remove the cap, fix the code/tests the upgrade breaks, "
                f"open a PR.\n\n"
                f"_Apply the `devin-fix` label to approve and hand this to Devin._")
        if args.dry_run:
            print(f"[dry-run] would create: {title}")
        else:
            subprocess.run(["gh", "issue", "create", "--repo", args.repo,
                            "--title", title, "--body", body], check=True)
            print(f"created: {title}")
        created += 1

    print(f"\nblocked found: {len(blocked)} | new: {created} | existing: {skipped}")


if __name__ == "__main__":
    main()
