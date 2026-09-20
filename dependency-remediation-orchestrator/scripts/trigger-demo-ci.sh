#!/bin/bash

# Demo CI Failure Scenario Triggers
# This script helps trigger the two demo scenarios for the presentation

set -e

REPO="haveitjoewei/devin-superset-automation"

echo "=== Demo CI Failure Scenarios ==="
echo ""
echo "1. Bounded repair success (Devin fixes on retry)"
echo "2. Escalation to human (Devin cannot fix)"
echo ""
read -p "Select scenario (1 or 2): " scenario

if [ "$scenario" = "1" ]; then
    echo "Creating issue for bounded repair success scenario..."
    
    ISSUE_URL=$(gh issue create --repo "$REPO" \
      --title "Demo: Bounded repair success" \
      --body "This test adds TEMP_FAILURE_FIRST marker to README.md.
The CI will fail on first attempt, Devin should remove it on retry.

**Expected behavior:**
1. Devin adds TEMP_FAILURE_FIRST to README.md
2. CI fails on first PR
3. Orchestrator sends bounded repair message
4. Devin removes TEMP_FAILURE_FIRST
5. CI passes on retry
6. Job marked as validated")
    
    ISSUE_NUMBER=$(echo "$ISSUE_URL" | grep -o '[0-9]*$')
    
    echo "Adding devin-fix label..."
    gh issue edit "$ISSUE_NUMBER" --repo "$REPO" --add-label "devin-fix"
    
    echo "✅ Scenario 1 triggered: $ISSUE_URL"
    echo "Monitor the orchestrator logs and GitHub Actions workflow."

elif [ "$scenario" = "2" ]; then
    echo "Creating issue for escalation to human scenario..."
    
    ISSUE_URL=$(gh issue create --repo "$REPO" \
      --title "Demo: Escalation to human" \
      --body "This test adds TEMP_FAILURE_ALWAYS marker to README.md.
The CI will always fail, requiring human intervention.

**Expected behavior:**
1. Devin adds TEMP_FAILURE_ALWAYS to README.md
2. CI fails on first PR
3. Orchestrator sends bounded repair message
4. Devin attempts fix but marker persists
5. CI fails again
6. Job marked as needs_human
7. Human removes marker manually")
    
    ISSUE_NUMBER=$(echo "$ISSUE_URL" | grep -o '[0-9]*$')
    
    echo "Adding devin-fix label..."
    gh issue edit "$ISSUE_NUMBER" --repo "$REPO" --add-label "devin-fix"
    
    echo "✅ Scenario 2 triggered: $ISSUE_URL"
    echo "Monitor the orchestrator logs and GitHub Actions workflow."
    echo "When job reaches 'needs_human' state, remove the marker manually:"
    echo "  gh pr edit <pr-number> --body 'Removing TEMP_FAILURE_ALWAYS marker'"

else
    echo "Invalid selection. Please choose 1 or 2."
    exit 1
fi
