# CI checks and automatic repair

CI means the automated tests and build checks on a pull request. This app verifies an approved Devin fix, requests one repair if checks fail, and leaves merging to a person.

## Real checks

Set `TARGET_REPO` to your fork and `REQUIRED_CHECKS` to the exact GitHub Actions check names that must pass, separated by commas. Use the names displayed in the PR's checks, including any matrix suffixes. The token needs read access to checks. Subscribe the webhook to Issues, Check suites, and Pull requests.

The app reads the PR’s **current commit** and fetches its checks from GitHub. It waits until all configured checks finish. Each must report `success`; skipped or cancelled checks do not count as a pass. Empty configuration or missing checks leaves the job waiting. This is an explicit verification policy, not automatic discovery of branch-protection rules. Classic commit statuses are not supported.

| Result | Outcome |
|---|---|
| All configured checks pass | `checks_passed`; ready for human review |
| First failing commit | Request one repair in the same Devin session; keep waiting |
| Repeated failure on that same commit | No additional repair or escalation |
| Checks pass after repair | `checks_passed` |
| Replacement commit still fails | `checks_failed`; a person investigates |
| New commit or checks still running | `checks_running`; previous success is withdrawn |

The worker rechecks PRs, so events arriving before it discovers a PR are not permanently lost. GitHub read errors are retried on a later poll. Notification failures are logged without changing the engineering outcome.

Use one repair owner: disable Devin's separate native CI-repair automation for these PRs if this app owns the follow-up. This app cannot limit work started independently by another integration.

## Simulate the workflow

Use a separate local demo database and set `ALLOW_SIMULATED_EVENTS=true`. Restart the API and worker. Keep this setting false for real use. See the [setup guide](../dependency-remediation-orchestrator/README.md).

1. Label an issue `devin-fix` and wait for its PR and `checks_running` state.
2. From `dependency-remediation-orchestrator/`, send a first failure:

   ```bash
   python scripts/simulate_ci.py <pr_number> --repo owner/repo --conclusion failure --attempt 1
   ```

3. Show the repaired commit passing:

   ```bash
   python scripts/simulate_ci.py <pr_number> --repo owner/repo --conclusion success --attempt 2
   ```

   Or use `--conclusion failure --attempt 2` to show escalation. Repeating attempt 1 demonstrates duplicate handling; it does not exhaust the repair.

4. Inspect `/jobs` and GitHub or Slack. Simulated outcomes are labeled and excluded from live metrics.

A simulated failure sends a **real repair request to Devin** and may use credits. A simulated pass runs no tests. The merge simulator records a demo outcome; it does not merge a PR. Use a fresh job for another scenario.

## This repository's workflows

These are separate from the app's response to a Superset PR:

| Workflow | Purpose |
|---|---|
| [CI](../.github/workflows/ci.yml) | Run the app tests on pushes to main and pull requests |
| [Demo CI Test](../.github/workflows/demo-ci.yml) | A deliberately breakable check for demonstrations |

The demo check fails while `TEMP_FAILURE_FIRST` or `TEMP_FAILURE_ALWAYS` appears in the root README. Both markers behave the same way. Remove the marker and push to make it pass. A failing check does not create a tracked remediation job by itself.
