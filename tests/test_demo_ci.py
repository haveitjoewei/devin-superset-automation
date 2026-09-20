"""
Demo CI failure scenarios for dependency remediation orchestrator presentation.

This test provides controlled failure scenarios to demonstrate:
1. Bounded repair success ( Devin fixes the issue on retry)
2. Escalation to human (Devin cannot fix, human intervention required)
"""
import pytest


def test_demo_ci_failure_markers():
    """
    Demo test that fails based on temporary markers in README.md
    
    Scenarios:
    - TEMP_FAILURE_FIRST: Fails first attempt, Devin should remove marker
    - TEMP_FAILURE_ALWAYS: Always fails, requires human intervention
    """
    with open("README.md", "r") as f:
        content = f.read()
    
    if "TEMP_FAILURE_FIRST" in content:
        pytest.fail(
            "First attempt failure - Devin should remove TEMP_FAILURE_FIRST marker "
            "on bounded repair attempt. This demonstrates the bounded retry logic."
        )
    
    if "TEMP_FAILURE_ALWAYS" in content:
        pytest.fail(
            "Permanent failure - requires human intervention. "
            "This demonstrates escalation to 'needs_human' state when "
            "bounded repair attempts are exhausted."
        )
