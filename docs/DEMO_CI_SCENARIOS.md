# Demo CI Failure Scenarios

This document explains how to demonstrate the CI failure handling in the dependency remediation orchestrator.

## Setup

Ensure the GitHub Actions workflow is enabled in your repository.

## Scenario 1: Bounded Repair Success

**Goal:** Demonstrate Devin successfully fixing a CI failure on the first retry attempt.

### Steps

1. **Create test issue with temporary failure marker:**
   ```bash
   gh issue create --repo haveitjoewei/devin-superset-automation \
     --title "Demo: Bounded repair success" \
     --body "This test adds TEMP_FAILURE_FIRST marker to README.md.
   The CI will fail on first attempt, Devin should remove it on retry."
   ```

2. **Add devin-fix label:**
   ```bash
   gh issue edit <issue-number> --add-label "devin-fix"
   ```

3. **Monitor:**
   - Devin session starts
   - Devin adds `TEMP_FAILURE_FIRST` to README.md
   - Devin creates PR
   - CI fails (GitHub Actions check suite)
   - Orchestrator sends bounded repair message to Devin
   - Devin removes `TEMP_FAILURE_FIRST` marker
   - CI passes
   - Job marked "validated"

### Expected Outcome

- **Job state:** `session_started` → `verifying` → `validated`
- **Attempts:** 1 (bounded repair attempt used)
- **GitHub comment:** "CI failed... Devin attempts fix"
- **Result:** CI passes on retry

## Scenario 2: Escalation to Human

**Goal:** Demonstrate automatic escalation when Devin cannot fix the issue.

### Steps

1. **Create test issue with permanent failure marker:**
   ```bash
   gh issue create --repo haveitjoewei/devin-superset-automation \
     --title "Demo: Escalation to human" \
     --body "This test adds TEMP_FAILURE_ALWAYS marker to README.md.
   The CI will always fail, requiring human intervention."
   ```

2. **Add devin-fix label:**
   ```bash
   gh issue edit <issue-number> --add-label "devin-fix"
   ```

3. **Monitor:**
   - Devin session starts
   - Devin adds `TEMP_FAILURE_ALWAYS` to README.md
   - Devin creates PR
   - CI fails (GitHub Actions check suite)
   - Orchestrator sends bounded repair message to Devin
   - Devin attempts fix but marker persists
   - CI fails again
   - Job marked "needs_human"

4. **Human intervention:**
   ```bash
   # Remove the marker manually
   gh pr edit <pr-number> --body "Removing TEMP_FAILURE_ALWAYS marker"
   # Or directly edit the file
   ```

### Expected Outcome

- **Job state:** `session_started` → `verifying` → `needs_human`
- **Attempts:** 1 (bounded repair attempt exhausted)
- **GitHub comment:** "CI failed... Devin attempted fix... needs human"
- **Result:** Human removes marker and closes PR

## Orchestrator Behavior

**Bounded repair logic:**
```python
if check_suite.conclusion == "failure" and job.attempts < 1:
    # Send one repair attempt to Devin
    devin_client.send_message(job.session_id, failure_details)
    job.attempts += 1
elif check_suite.conclusion == "failure" and job.attempts >= 1:
    # No more attempts, escalate to human
    job.state = "needs_human"
```

## For Presentation

**Key talking points:**
- "The orchestrator automatically handles CI failures with bounded retry"
- "One repair attempt prevents infinite loops"
- "When autonomous repair fails, it escalates to human review"
- "Human remains in control of critical merge decisions"

**Demo flow:**
1. Show Scenario 1 (bounded repair success)
2. Show Scenario 2 (escalation to human)
3. Contrast with manual process (human would need to investigate each failure)
