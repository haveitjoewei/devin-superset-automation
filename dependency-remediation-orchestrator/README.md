# Dependency Auto-Fix Orchestrator

The app behind [Devin Auto-Fix](../README.md): a FastAPI webhook API + a polling
worker that create and manage Devin sessions, tracking each dependency fix from a
labeled issue to a merged PR. See [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
for the design.

## Stack
- **FastAPI** (`api.py`) — GitHub webhook receiver
- **Worker** (`worker.py`) — polls Devin sessions, advances job state
- **Postgres** — job store + Superset data source (`vw_job_metrics` view)
- **SlackReporter / GitHubReporter** — lifecycle status out
- **Superset** — leadership dashboard

## Setup

### 1. Environment
```bash
cp .env.example .env
```
```env
DEVIN_API_KEY=...           DEVIN_ORG_ID=...
GITHUB_TOKEN=...            GITHUB_WEBHOOK_SECRET=...
SLACK_BOT_TOKEN=xoxb-...    SLACK_CHANNEL_ID=...   ONCALL_SLACK_USER_ID=...
DATABASE_URL=postgresql://<user>@localhost:5432/devin_jobs
WORKER_POLL_INTERVAL=30     CONCURRENCY_CAP=2
```

### 2. Run
```bash
docker compose up            # api + worker
# or locally:
python -m uvicorn api:app --host 0.0.0.0 --port 8000
python worker.py
```

### 3. Dashboard (Superset)
```bash
python scripts/setup_superset.py     # prints connection + dataset setup steps
```
Point a Superset database connection at Postgres via `host.docker.internal`
(Superset runs in Docker; the job DB is on the host), add a dataset on
`vw_job_metrics`, and build the "Devin Auto-Fix — Effectiveness" dashboard.

## Trigger a run
```bash
python scripts/simulate_issue.py <issue_number>   # replay a labeled-issue event
python scripts/simulate_ci.py                      # simulate check_suite success
python scripts/simulate_merge.py <pr_number>       # simulate PR merged
```
In production these come from real GitHub webhooks (`issues`, `check_suite`,
`pull_request`). The simulate scripts exist because Superset's fork-PR CI needs
maintainer approval — see the disclaimer in [../README.md](../README.md).

## Scripts
| Script | Purpose |
|---|---|
| `scripts/detect_blocked_upgrades.py` | scan requirements/*.in for blocked upgrades, open issues for approval (`--dry-run` to preview) |
| `scripts/seed_demo_data.py` | seed demo jobs so the dashboard renders |
| `scripts/migrate_to_postgres.py` | migrate an old SQLite job store to Postgres |
| `scripts/setup_superset.py` | print Superset connection/dataset setup steps |
| `scripts/export_metrics_csv.py` | export metrics to CSV |
| `scripts/simulate_*.py` | replay GitHub events against the local API |
| `scripts/trigger-demo-ci.sh` | trigger the bounded-repair demo scenarios |

## Endpoints
- `POST /webhook/github` — issues / check_suite / pull_request events
- `GET /metrics` — live metrics JSON
- `GET /jobs` — job list
- `GET /health`
