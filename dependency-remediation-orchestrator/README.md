# Dependency Remediation Orchestrator

Production-grade orchestrator for autonomous dependency remediation using Devin API.

## Architecture

**Stack:**
- Python FastAPI (webhook API)
- Background worker (polling loop)
- SQLite (job state)
- Docker Compose (api + worker services)

**Event Handlers (GitHub webhooks) — return fast, never block on Devin:**
- `issues.labeled` — when label == devin-remediate: create a job + kick off a Devin session
- `pull_request` (opened) — match PR back to a job (branch/issue ref), begin verification
- `check_suite.completed` — if conclusion == failure AND tied to a Devin PR: send one bounded follow-up message to that session with the failing check logs; else if success, mark job validated

**Job Lifecycle (SQLite jobs table):**
- `id, issue_number, devin_session_id, pr_number, state, attempts, created_at, updated_at, cost, notes`
- States: `queued → session_started → pr_opened → verifying → validated | failed | needs_human`

**Devin API Usage:**
- Create session: `POST https://api.devin.ai/v3/organizations/{org_id}/sessions`
- Poll status: `GET https://api.devin.ai/v3/organizations/{org_id}/sessions/{id}`
- Follow-up (CI repair): `POST https://api.devin.ai/v3/organizations/{org_id}/sessions/{id}/messages`
- Concurrency cap = 2 active sessions (worker respects it)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Devin API Key
DEVIN_API_KEY=your-devin-api-key
DEVIN_ORG_ID=your-org-id

# GitHub Token
GITHUB_TOKEN=ghp-your-github-token
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Worker Configuration
WORKER_POLL_INTERVAL=30
CONCURRENCY_CAP=2
```

### 3. Run Locally

**API Server:**
```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

**Worker:**
```bash
python worker.py
```

### 4. Run with Docker Compose

```bash
docker-compose up
```

## Usage

### Triggering Remediation

1. **Label a GitHub issue** with `devin-remediate`
2. **Orchestrator creates a job** and starts a Devin session
3. **Worker polls session status** and updates job state
4. **When Devin creates a PR**, orchestrator matches it to the job
5. **When CI runs**, orchestrator monitors check results
6. **If CI fails**, orchestrator sends one bounded repair attempt to Devin
7. **When CI passes**, job is marked as validated

### Monitoring

**Check job status:**
```bash
curl http://localhost:8000/jobs
```

**Health check:**
```bash
curl http://localhost:8000/health
```

## Business Value

### Why This Matters

Superset faces real-world upgrade blockers that prevent security updates:

- **2,059** dependency-bump PRs merged (last 12 months)
- **128** security-labeled PRs/commits
- **6** upgrades explicitly deferred as "needs eng attention"

**Estimated annual cost:** $67k for engineering time spent on dependency upgrade toil

### Devin Advantage

- **Scanners find, bots bump — neither fixes.** Devin edits code, runs tests, iterates until green
- **Throughput scales with sessions, not headcount.**
- **Async + unattended.** Event fires, PR waiting at standup.
- **One workflow, many problems.** Different upgrade problems delegated to autonomous agent.

## API Endpoints

### POST /webhook/github
**GitHub webhook handler**

**Events handled:**
- `issues.labeled` — Triggers remediation when `devin-remediate` label added
- `pull_request.opened` — Matches PR to job for verification
- `check_suite.completed` — Handles CI failure with bounded repair attempt

### GET /health
**Health check endpoint**

### GET /jobs
**List all jobs**

Returns job state and metadata.

## Security

- **Webhook signature verification** using GitHub secrets
- **Bounded repair attempts** (max 1 per job)
- **Concurrency cap** prevents resource exhaustion
- **Job state tracking** for audit and monitoring

## License

MIT
