# CI checks and automatic repair

This app can respond when a Devin pull request fails automated tests or build checks. Those checks are called **CI**, short for continuous integration. The app asks Devin to repair a failure once, then hands it back to a person if checks still fail.

This guide explains the implemented behavior, how to connect real check results, and how to demonstrate it without waiting for Superset's full test suite.

## What is supported

The job must already exist: a person labels an issue `devin-fix`, Devin opens a pull request, and the worker moves the job to `checks_running`.

| Result received | What the app does | Job state |
|---|---|---|
| Checks pass | Posts that the fix is ready for human review | `checks_passed` |
| Checks fail for the first time | Sends a repair request to the same Devin session and waits for another result | Stays `checks_running`; `attempts` becomes 1 |
| Checks pass after that repair request | Posts that the fix is ready for human review | `checks_passed` |
| Checks fail again | Stops requesting repairs and posts that a person needs to investigate | `checks_failed` |

Final results are posted to GitHub and, when configured, Slack. The first failure sends Devin a message and records a note; it does not post a separate Slack or GitHub update. A person always decides whether to merge.

The app does not start repairs for arbitrary failing PRs. It handles results for work started through the labeled-issue flow.

## Real CI results versus the demo

GitHub runs the checks. This app receives their result through a signed `check_suite` webhook; it does not run a test suite itself. Configure the target repository's webhook using the [setup guide](../dependency-remediation-orchestrator/README.md#start-a-fix), including **Check suites** in the selected events.

The demo's `simulate_ci.py` sends a made-up pass or fail result to the same handler. This lets you show the repair workflow while Superset's fork checks await approval. A simulated failure sends a **real message to Devin** and may use credits. A simulated pass does not prove the fix works.

### Current limits

- **Results are not matched to a PR or commit.** The handler chooses the latest job in `checks_running`, even if the result belongs to another PR. Use a controlled demo with one waiting job and no unrelated check events.
- **Only `success` and `failure` are handled.** Cancelled, timed-out, skipped, and other results leave the job unchanged. The app does not combine multiple check suites into an overall verdict.
- **Duplicate failures are not filtered.** A repeated webhook can use up the one repair attempt. Results received before the job reaches `checks_running` are ignored.
- **Comments still assume a demo.** The GitHub success comment includes a simulation disclaimer even for a real result.

The handler is in [`triggers/github.py`](../dependency-remediation-orchestrator/triggers/github.py). These limits need fixing before relying on it across real PRs.

## Try the workflow locally

Use the [setup guide](../dependency-remediation-orchestrator/README.md) to start the API and worker, install Python dependencies, and sign in to the GitHub CLI (`gh`). Then:

1. Start a fix for a labeled issue. Wait until Devin opens a PR and `GET /jobs` shows `checks_running`.
2. From `dependency-remediation-orchestrator/`, send the first failure:

   ```bash
   python scripts/simulate_ci.py --repo owner/repo --conclusion failure
   ```

   Check the Devin session for the repair request. The job should remain `checks_running`.

3. Choose the outcome to demonstrate:

   ```bash
   # Show a successful repair outcome.
   python scripts/simulate_ci.py --repo owner/repo --conclusion success
   ```

   Or:

   ```bash
   # Show a second failure that needs a person.
   python scripts/simulate_ci.py --repo owner/repo --conclusion failure
   ```

4. Check `/jobs` and the GitHub or Slack update. Expect `checks_passed` for success or `checks_failed` for another failure.

Replace `owner/repo` with the target repository. Use a fresh job to demonstrate the other outcome. To show checks passing on the first try, send `success` at step 2 instead.

## What this repository's GitHub Actions workflows do

These are separate from the app's response to a target PR:

| Workflow | Purpose |
|---|---|
| [`CI`](../.github/workflows/ci.yml) | Runs the app's unit tests on pushes to `main` and on pull requests |
| [`Demo CI Test`](../.github/workflows/demo-ci.yml) | Runs a small test on PRs to this repo so a demo can deliberately fail a real check |

The demo test fails while either `TEMP_FAILURE_FIRST` or `TEMP_FAILURE_ALWAYS` appears in the root README. Both behave the same way. Remove the marker from the file and push the change to make that test pass; editing the PR description does not remove it.

A failing demo check only reaches the app if this repository's webhook is configured. It does not create a tracked job by itself. The older `scripts/trigger-demo-ci.sh` helper has outdated instructions; use the steps above.
