"""Posts Devin lifecycle status back to the GitHub issue and PR.

Mirrors SlackReporter so GitHub reflects the full lifecycle, not just "kicked off".
"""
from github_client import GitHubClient
from models import Job



class GitHubReporter:
    def __init__(self):
        self.gh = GitHubClient()

    def _owner_repo(self, job: Job):
        # job.issue_url = https://github.com/<owner>/<repo>/issues/<n>
        try:
            parts = job.issue_url.split("github.com/")[1].split("/")
            return parts[0], parts[1]
        except Exception:
            return None, None

    async def report_state_transition(self, job: Job, previous_state: str = None):
        if not job.issue_url:
            return
        owner, repo = self._owner_repo(job)
        if not owner:
            return

        if getattr(job, "is_simulated", False):
            await self.gh.comment_on_issue(owner, repo, job.issue_number,
                f"**SIMULATION — not verified:** job state {job.state}. No tests or merge were performed by this event.")
            return
        if job.state == "fixing":
            await self.gh.comment_on_issue(owner, repo, job.issue_number,
                f"Devin started the fix: https://app.devin.ai/sessions/{job.devin_session_id}")
        elif job.state == "checks_running" and job.pr_number:
            # PR opened — link it from the issue. (No PR-side comment: the PR
            # itself already announces it was opened.)
            await self.gh.comment_on_issue(
                owner, repo, job.issue_number,
                f"🤖 Devin opened PR #{job.pr_number} to fix this. Automated checks running.",
            )
        elif job.state == "checks_passed":
            body = (
                f"✅ **Automated checks passed** (PR #{job.pr_number}).\n\n"
                f"Ready for human review — **not auto-merged**.\n\n"
                f"{job.notes or 'Verified configured checks on the current commit.'}"
            )
            target = job.pr_number or job.issue_number
            await self.gh.comment_on_issue(owner, repo, target, body)
            if job.pr_number:
                await self.gh.comment_on_issue(
                    owner, repo, job.issue_number,
                    f"✅ PR #{job.pr_number} passed automated checks — awaiting review.",
                )
        elif job.state == "merged":
            await self.gh.comment_on_issue(
                owner, repo, job.issue_number,
                f"🎉 PR #{job.pr_number} merged — dependency fix shipped. Closing the loop.",
            )
        elif job.state in ("checks_failed", "needs_human"):
            reason = job.notes or "Unknown reason"
            target = job.pr_number or job.issue_number
            await self.gh.comment_on_issue(
                owner, repo, target,
                f"⚠️ Devin auto-fix needs attention ({job.state}): {reason}",
            )
