# Devin Auto-Fix — Autonomous Dependency Remediation

Event-driven automation that uses the [Devin API](https://docs.devin.ai/api-reference/overview)
to do the engineering work dependency bots leave undone: when a dependency upgrade
breaks the build, Devin investigates, fixes the code and tests, and opens a
validated PR — triggered by a GitHub event, tracked to a merge, and reported to
Slack and a Superset dashboard.

Target repository: [apache/superset](https://github.com/apache/superset) (via a fork).

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
Issue labeled `devin-remediate`
  → api creates a Devin session
  → Devin fixes code + tests, opens a PR
  → worker tracks it: checks_running → checks_passed → merged
  → Slack thread + GitHub comments + Superset dashboard
```

Full detail and the state machine: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

### Lifecycle states
`queued → fixing → checks_running → checks_passed → merged`
(plus `checks_failed`, `needs_human`). `checks_passed` means checks are green and
it's **ready for human review — never auto-merged**.

## Quickstart

```bash
cd dependency-remediation-orchestrator
cp .env.example .env          # fill in Devin, GitHub, Slack creds
docker compose up             # api + worker
```

Postgres and Superset run alongside (see the orchestrator README). Then trigger
a run:

```bash
# fire the pipeline for a labeled issue (replays the GitHub event locally)
python scripts/simulate_issue.py <issue_number>
# after Devin opens the PR, simulate CI success -> checks_passed (disclaimed)
python scripts/simulate_ci.py
# after a human merges -> merged
python scripts/simulate_merge.py <pr_number>
```

## Observability

- **Slack** (operational): one thread per job, threaded updates, on-call @mention
  when checks pass.
- **Superset** (leadership): "Devin Auto-Fix — Effectiveness" dashboard — success
  rate, throughput, dev-hours saved, net $ saved, MTTR, tasks by state. Reads the
  `vw_job_metrics` Postgres view. The dashboard *replaces the estimated ROI inputs
  with live measured numbers*.
- **`GET /metrics`** — the same numbers as JSON.

## A note on the demo's CI step

The demo drives the `check_suite` success event locally (`scripts/simulate_ci.py`)
because Apache Superset's PR CI is heavy/slow and fork PRs need maintainer approval
before CI runs. This is **clearly disclaimed in every validated PR comment**, and
production uses the real GitHub `check_suite` webhook. `checks_passed` is evidence,
not proof — merges stay human-gated.

## Extensibility

The trigger is pluggable. The same engine runs off any event that means "a fix is
needed" — a Dependabot PR that fails CI, a scanner finding, or a ticket in
Linear/Jira. Only the webhook adapter changes; the Devin session logic is the same.

## Repo layout

```
dependency-remediation-orchestrator/   the app (api, worker, reporters, clients)
  scripts/                             setup + demo/simulate helpers
docs/ARCHITECTURE.md                   how it works, state machine, decisions
docs/DEMO_CI_SCENARIOS.md              bounded-repair demo walkthrough
tests/                                 CI-failure scenario tests
```
