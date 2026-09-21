# Devin Auto-Fix — Autonomous Dependency Remediation

[![CI](https://github.com/haveitjoewei/devin-superset-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/haveitjoewei/devin-superset-automation/actions/workflows/ci.yml)

Event-driven automation that uses the [Devin API](https://docs.devin.ai/api-reference/overview)
to do the engineering work dependency bots leave undone: when a dependency upgrade
breaks the build, Devin investigates, fixes the code and tests, and opens a
validated PR — triggered by a GitHub event, tracked to a merge, and reported to
Slack and a Superset dashboard.

Target repository: [apache/superset](https://github.com/apache/superset) (via a fork).

## Submission artifacts

- **Loom walkthrough:** https://www.loom.com/share/8458da2bc6a64c43893ee9ed99355578
- **Solution repo:** this repo — quickstart below, architecture in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Forked Superset:** [haveitjoewei/superset](https://github.com/haveitjoewei/superset)
  - Issues remediated: apispec [#28](https://github.com/haveitjoewei/superset/issues/28) · [#31](https://github.com/haveitjoewei/superset/issues/31) · paramiko [#35](https://github.com/haveitjoewei/superset/issues/35)
  - Resulting PRs: apispec [#29](https://github.com/haveitjoewei/superset/pull/29) · **paramiko [#37](https://github.com/haveitjoewei/superset/pull/37)** (the meaty one — a `DSSKey` compat shim)
- **Independent verification** (I ran the tests, didn't trust the agent): [docs/DEMO_VERIFICATION.md](docs/DEMO_VERIFICATION.md)
- **Leadership dashboard:** "Devin Auto-Fix — Effectiveness" (Superset) — see [docs/images/](docs/images)
- **Pitch deck:** [docs/deck.html](docs/deck.html)

## The problem

Scanners find vulnerable deps and Dependabot proposes upgrades — but both stop
when the upgrade **breaks the app**. Someone still has to investigate, fix call
sites, unbreak tests, and validate. That last mile is unbounded toil.

Measured on apache/superset (last 12 months):

- **2,658** Dependabot PRs; **~17%** need human code work (not a clean bump)
- → **~450 upgrades/year** that fall out of the "merge in 6h" fast lane
- ≈ **1,350 developer-hours/year** (~$73k–122k) sitting in a dead lane
- CVE exposure (advisory → fix landed): median **34 days**, tail into years

Devin turns that dead lane back into the fast lane.

## How it works

```
detect blocked upgrades (nightly)  → files an issue
  → human labels `devin-fix`        (approval gate — decides what's worth fixing)
  → api creates a Devin session
  → Devin fixes code + tests, opens a PR
  → worker tracks it: checks_running → checks_passed → merged
  → Slack thread + GitHub comments + Superset dashboard
```

Each stage is owned by the right actor: **discovery** and the **fix** are automated;
the two judgment calls — *what to fix* (the label) and *what to merge* — stay human.
A nightly job (`scripts/detect_blocked_upgrades.py`, `.github/workflows/detect-blocked-deps.yml`)
scans `requirements/*.in` for capped deps whose comments flag a blocker and opens
unlabeled issues; a person approves by labeling.

Full detail and the state machine: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

### Lifecycle states
`queued → fixing → checks_running → checks_passed → merged`
(plus `checks_failed`, `needs_human`). `checks_passed` means checks are green and
it's **ready for human review — never auto-merged**.

## Run / simulate the workflow

### Prerequisites
- Docker (for the self-contained stack) **or** Python 3.12 + a local Postgres.
- Credentials in `.env` (copy `.env.example`): `DEVIN_API_KEY`, `DEVIN_ORG_ID`,
  `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET`, and optionally `SLACK_BOT_TOKEN` /
  `SLACK_CHANNEL_ID` / `ONCALL_SLACK_USER_ID`. Without Devin + GitHub creds the pipeline
  runs but can't open real sessions/PRs — see the Loom for a live run.

### 1. Start the services
```bash
cd dependency-remediation-orchestrator
cp .env.example .env            # fill in your credentials
docker compose up               # postgres + api (:8000) + worker
```
(Native alternative — runs against your own Postgres so the Superset dashboard sees the
data: `pip install -r requirements.txt`, then `uvicorn api:app --port 8000` and
`python worker.py` in two shells.)

### 2. Trigger a remediation — two ways

**A. Simulate the event locally (no public URL needed — recommended for a quick run):**
```bash
python scripts/simulate_issue.py <issue_number>   # replays a signed "issue labeled" webhook
python scripts/simulate_ci.py                      # simulate check_suite success -> checks_passed
python scripts/simulate_merge.py <pr_number>       # simulate PR merged -> merged
```
Each replays exactly the GitHub event the real webhook would send, POSTed to the local API.

**B. Real GitHub events (fully event-driven):** expose the API publicly and point a
GitHub webhook at it, then just **label an issue `devin-fix`**:
```bash
ngrok http 8000                 # gives https://<id>.ngrok-free.app
# set the fork's webhook URL to https://<id>.ngrok-free.app/webhook/github,
# content-type application/json, secret = GITHUB_WEBHOOK_SECRET, events: issues, check_suite, pull_request
```
(ngrok free URLs change on restart — update the webhook URL each time. The simulate
scripts above avoid this entirely.)

### 3. Watch it work
- **Slack** — a threaded update per job (if Slack creds set).
- **GitHub** — lifecycle comments on the issue + PR.
- **API** — `GET /jobs` and `GET /metrics` (JSON), `GET /health`.
- **Superset** — the "Devin Auto-Fix — Effectiveness" dashboard (native run).

Lifecycle: `queued → fixing → checks_running → checks_passed → merged` (or
`checks_failed` / `needs_human`).

## Observability

- **Slack** (operational): one thread per job, threaded updates, on-call @mention
  when checks pass.
- **Superset** (leadership): "Devin Auto-Fix — Effectiveness" dashboard — success
  rate, throughput, dev-hours saved, net $ saved, MTTR, tasks by state. Reads the
  `vw_job_metrics` Postgres view. The dashboard *replaces the estimated ROI inputs
  with live measured numbers*.
- **`GET /metrics`** — the same numbers as JSON.

## Screenshots

| Superset dashboard | Slack thread | GitHub PR |
|---|---|---|
| ![dashboard](docs/images/dashboard.png) | ![slack](docs/images/slack-thread.png) | ![pr](docs/images/pr.png) |

*(Live examples: the "Devin Auto-Fix — Effectiveness" dashboard, a per-job Slack
thread with the on-call ping, and a Devin PR with lifecycle comments.)*

## A note on the demo's CI step

The demo drives the `check_suite` success event locally (`scripts/simulate_ci.py`)
because Apache Superset's PR CI is heavy/slow and fork PRs need maintainer approval
before CI runs. This is **clearly disclaimed in every validated PR comment**, and
production uses the real GitHub `check_suite` webhook. `checks_passed` is evidence,
not proof — merges stay human-gated.

## Extensibility

The trigger is pluggable. The same engine runs off any event that means "a fix is
needed" — a Dependabot PR that fails CI, a scanner finding, or a ticket in
Linear/Jira. Only the trigger adapter (`triggers/<source>.py`) changes; the Devin
session logic and reporters are shared.

**Two trigger modes:**
- **Human-gated (this demo):** a person labels an issue `devin-fix` — a deliberate
  approval gate deciding *what* is worth Devin's time. Real-world fit: an engineer or
  security triager promotes a Dependabot alert / blocked upgrade into the work queue.
- **Fully automated (production):** trigger straight off a **Dependabot PR whose CI
  fails** (`pull_request` / `check_suite`) — no issue, no label. This is the hands-off
  "dead-lane" catch. The seam is in `triggers/github.py`; see the note in
  `handle_check_suite_event`.

> Note: Dependabot itself opens **PRs and security alerts, not issues** — so the
> labeled-issue flow is a human on-ramp, not a Dependabot behavior.

## Production considerations

This repo is a working demo, scoped deliberately. In a real customer engagement,
these are where *their* engineering team would invest next — noted here to mark the
boundary, not because they're required for the demo:

- **Auth on `/jobs` and `/metrics`** (currently open; the webhook is HMAC-verified).
- **Idempotency** on webhook delivery id (GitHub retries deliveries).
- **Durable retries / dead-letter** for failed Devin or GitHub calls (today: timeouts + a bounded CI repair).
- **Secrets** via a manager (Vault/SSM) instead of `.env`.
- **Rate limits & backoff** against the Devin and GitHub APIs at higher volume.
- **Scaling the worker** beyond a single polling loop (queue + multiple workers).

What *is* built for cost-safety: a per-day Devin spend cap (`DAILY_COST_CAP`) and a
concurrency cap on active sessions.

## Repo layout

```
dependency-remediation-orchestrator/   the app (api, worker, reporters, clients)
  scripts/                             setup + demo/simulate helpers
docs/ARCHITECTURE.md                   how it works, state machine, decisions
docs/DEMO_CI_SCENARIOS.md              bounded-repair demo walkthrough
tests/                                 CI-failure scenario tests
```
