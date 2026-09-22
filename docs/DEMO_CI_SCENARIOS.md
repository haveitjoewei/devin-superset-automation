# Demo: when automated checks fail

The app gives Devin one chance to repair a failed check. If the next result also fails, the job becomes `checks_failed` and needs a person to investigate.

## Replay the two outcomes

Start the app using the [setup guide](../dependency-remediation-orchestrator/README.md). Use one job in `checks_running` at a time: the simulator and handler do not match check results to a specific PR.

From `dependency-remediation-orchestrator/`, send a failure:

```bash
python scripts/simulate_ci.py --repo owner/repo --conclusion failure
```

The app sends Devin a real repair request, increments `attempts` to 1, and keeps the job in `checks_running`.

Then choose the outcome to demonstrate:

| Next event | Command | Result |
|---|---|---|
| Checks pass | `python scripts/simulate_ci.py --repo owner/repo --conclusion success` | `checks_passed`; ready for review |
| Checks fail again | `python scripts/simulate_ci.py --repo owner/repo --conclusion failure` | `checks_failed`; no further repair request |

Use a fresh job to demonstrate the other outcome. These events test status handling; they do not run checks or prove Devin repaired the code. Review the job in `/jobs` and its Slack or GitHub updates. Merging remains a human decision.

## Trigger a real GitHub check failure

This repository's `Demo CI Test` workflow runs `tests/test_demo_ci.py` on pull requests. Adding either `TEMP_FAILURE_FIRST` or `TEMP_FAILURE_ALWAYS` to the root README makes that test fail. Removing the marker from the file and pushing the commit lets it pass.

Both markers behave the same way: they fail while present. Neither guarantees Devin will leave it in place for a second failure. To show the two-failure path reliably, use the event replay above.

Changing a PR description does not remove a marker from the file. The older `scripts/trigger-demo-ci.sh` helper uses outdated state names and gives that incorrect cleanup instruction; use this guide instead.
