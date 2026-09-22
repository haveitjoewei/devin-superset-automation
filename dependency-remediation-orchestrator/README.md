# Run Devin Auto-Fix

This folder contains the app: a GitHub event receiver, a worker that checks Devin's progress, and a Postgres database. See the [project overview](../README.md) for the demo.

## Start with Docker

You need Docker Compose, Devin API credentials, and a GitHub token with access to the target repository.

From the repository root:

```bash
cd dependency-remediation-orchestrator
cp .env.example .env
```

Fill in `DEVIN_API_KEY`, `DEVIN_ORG_ID`, `GITHUB_TOKEN`, and `GITHUB_WEBHOOK_SECRET` in `.env`. For Slack updates, also set `SLACK_BOT_TOKEN` and `SLACK_CHANNEL_ID`; `ONCALL_SLACK_USER_ID` chooses who gets notified when checks pass.

```bash
docker compose up --build
```

This starts Postgres, the API at `http://localhost:8000`, and the worker.

### Run without Docker

Use Python 3.12 and an existing Postgres database. Set `DATABASE_URL` in `.env`, then run:

```bash
python -m pip install -r requirements.txt
python -m uvicorn api:app --port 8000
```

In another terminal, from this folder:

```bash
python worker.py
```

## Start a fix

Configure a GitHub webhook on the target repository:

- URL: your publicly reachable API address followed by `/webhook/github`
- Content type: `application/json`
- Secret: the same `GITHUB_WEBHOOK_SECRET` as `.env`
- Events: Issues, Check suites, and Pull requests

For local development, `ngrok http 8000` can provide the public address. Update the webhook if that address changes.

Add `devin-fix` to an issue to start Devin. This creates a real session and uses Devin credits.

Once Devin opens a PR, the app handles passing checks, requests one repair after a failure, and flags a second failure for a person. See [CI behavior and demo steps](../docs/DEMO_CI_SCENARIOS.md) for the supported outcomes and current limits.

### Replay events locally

With Python dependencies installed and the GitHub CLI (`gh`) signed in, you can send events directly to the local API. Run these from this folder, one step at a time:

```bash
# Use an existing issue that already has the devin-fix label.
python scripts/simulate_issue.py <issue_number> --repo owner/repo

# Wait for a PR and the checks_running state, then simulate passing checks.
python scripts/simulate_ci.py --repo owner/repo

# Simulate a merge for that PR.
python scripts/simulate_merge.py <pr_number> --repo owner/repo
```

These scripts default to `haveitjoewei/superset` if `--repo` is omitted. The issue replay starts real work; the other two commands only simulate results. They do not run tests or merge a PR. Use one active job at a time because check results currently apply to the latest waiting job.

## Check progress

| Where | What it shows |
|---|---|
| Slack and GitHub | Updates for each job |
| `GET /jobs` | Jobs and their current states |
| `GET /metrics` | Counts, timing, and estimated savings |
| `GET /health` | Whether the API responds |

For a Superset dashboard, connect Superset to this app's Postgres database and create a dataset from `vw_job_metrics`. If Superset runs in Docker on your Mac and Postgres uses the published host port, use `host.docker.internal:5432` as the database address. The API creates the view on startup; build the dashboard charts in Superset.

Savings figures use assumptions. See [metric limits](../docs/EVIDENCE.md#dashboard-figures).

## Where the code lives

| Files | Responsibility |
|---|---|
| `api.py` | Receive GitHub events and serve status endpoints |
| `triggers/github.py` | Start jobs and handle CI results and merges |
| `worker.py` | Check Devin sessions for progress and pull requests |
| `devin_client.py`, `github_client.py`, `slack_client.py` | Call the external services |
| `reporters/` | Format and send progress updates |
| `config.py`, `database.py`, `models.py`, `metrics.py` | Settings, stored jobs, and reporting figures |
| `scripts/`, `tests/` | Local tools and app tests |

## Other scripts

| Script | Purpose |
|---|---|
| `scripts/detect_blocked_upgrades.py` | Find blocked upgrades and open issues; use `--dry-run` to preview |
| `scripts/seed_demo_data.py` | Add sample jobs for the dashboard |
| `scripts/export_metrics_csv.py` | Export the older SQLite metrics view to CSV |
| `scripts/migrate_to_postgres.py` | Move an older SQLite job store to Postgres |

`scripts/setup_superset.py` still targets the old SQLite database. Use the Postgres steps above instead.

## Run tests

From this folder:

```bash
python -m pip install pytest
python -m pytest tests -q
```

Run the separate demo check from the repository root:

```bash
python -m pytest tests/test_demo_ci.py -q
```
