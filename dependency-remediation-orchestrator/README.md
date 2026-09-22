# Run Devin Auto-Fix

This folder contains the app: a GitHub event receiver, a worker that checks Devin's progress, and a Postgres database. See the [project overview](../README.md) for the demo.

## Start with Docker

You need Docker Compose, Devin API credentials, and a GitHub token with access to the target repository.

From the repository root:

```bash
cd dependency-remediation-orchestrator
cp .env.example .env
```

Fill in `DEVIN_API_KEY`, `DEVIN_ORG_ID`, `GITHUB_TOKEN`, and `GITHUB_WEBHOOK_SECRET` in `.env`. Set `TARGET_REPO` to your fork. Set `REQUIRED_CHECKS` to the exact, comma-separated GitHub Actions check names you require; leave it empty only if you want jobs to keep waiting for verification. The token needs issue/PR access and read access to checks. For Slack updates, also set `SLACK_BOT_TOKEN` and `SLACK_CHANNEL_ID`; `ONCALL_SLACK_USER_ID` chooses who gets notified when checks pass.

```bash
docker compose up --build
```

This starts Postgres, the API at `http://localhost:8000`, and one worker. The worker starts queued jobs up to `CONCURRENCY_CAP`. `.dockerignore` keeps `.env` out of the image.

On an existing installation, startup adds the new verification and usage columns without removing jobs. `ACU_ADMISSION_CAP` limits new starts based on total recorded live ACUs, not daily dollars. The old `DAILY_COST_CAP` name is accepted as an alias. Neither setting stops running sessions or accounts for unreported usage. A timed-out session creation needs manual inspection before retrying, to avoid duplicate paid work.

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

Add `devin-fix` to an issue to queue a fix. The worker starts a real Devin session when a slot is available; this uses credits.

Once Devin opens a PR, the app handles passing checks, requests one repair after a failure, and flags a second failure for a person. See [CI behavior and demo steps](../docs/DEMO_CI_SCENARIOS.md) for the supported outcomes and current limits.

### Replay events locally

Set `ALLOW_SIMULATED_EVENTS=true` in a local demo environment and restart the API and worker. Keep it false for real use. With Python dependencies installed and the GitHub CLI (`gh`) signed in, you can send events directly to the local API. Run these from this folder, one step at a time:

```bash
# Use an existing issue that already has the devin-fix label.
python scripts/simulate_issue.py <issue_number> --repo owner/repo

# Wait for a PR and the checks_running state, then simulate passing checks.
python scripts/simulate_ci.py <pr_number> --repo owner/repo

# Simulate a merge for that PR.
python scripts/simulate_merge.py <pr_number> --repo owner/repo
```

These scripts default to `haveitjoewei/superset` if `--repo` is omitted. The issue replay queues real work; the other two commands only simulate results. They do not run tests or merge a PR. Simulated outcomes are labeled and excluded from live metrics. Use a separate demo database to keep the workflows apart.

## Check progress

| Where | What it shows |
|---|---|
| Slack and GitHub | Updates for each job |
| `GET /jobs` | Jobs and their current states |
| `GET /metrics` | Live counts, timing, estimated effort, and ACU usage |
| `GET /health` | Whether the API responds |

For a Superset dashboard, connect Superset to this app's Postgres database and create a dataset from `vw_job_metrics`. If Superset runs in Docker on your Mac and Postgres uses the published host port, use `host.docker.internal:5432` as the database address. The API creates the view on startup; build the dashboard charts in Superset. The view excludes sample and simulated rows and historical successes without a verified commit. Use `acu_usage` for usage; the old `cost` column is now null because it mixed units. There is no dollar-savings calculation.

Savings figures use assumptions. See [metric limits](../docs/EVIDENCE.md#dashboard-figures).

## Where the code lives

| Files | Responsibility |
|---|---|
| `api.py` | Receive GitHub events and serve status endpoints |
| `triggers/github.py` | Queue approved issues and handle CI results and merges |
| `worker.py` | Start queued sessions, poll progress, and reconcile checks |
| `devin_client.py`, `github_client.py`, `slack_client.py` | Call the external services |
| `reporters/` | Format and send progress updates |
| `config.py`, `database.py`, `models.py`, `metrics.py` | Settings, stored jobs, and reporting figures |
| `scripts/`, `tests/` | Local tools and app tests |

## Other scripts

| Script | Purpose |
|---|---|
| `scripts/detect_blocked_upgrades.py` | Find blocked upgrades and open issues; use `--dry-run` to preview |
| `scripts/seed_demo_data.py` | Add sample jobs for the dashboard |

The old SQLite migration is retained in [`scripts/legacy/`](scripts/legacy/migrate_to_postgres.py) for reference. It reads `scripts/jobs.db` and uses a hard-coded local Postgres connection; it is not part of the current setup.

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
