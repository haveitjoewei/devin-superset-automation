from slack_client import SlackClient
from models import Job
from database import SessionLocal

class SlackReporter:
    def __init__(self):
        self.slack = SlackClient()
    
    async def report_state_transition(self, job: Job, previous_state: str = None):
        """Report job state transition to Slack"""
        if not self.slack.bot_token:
            return  # Skip if Slack not configured

        # Guarantee a thread root exists before any post. If this is the job's
        # first report, or the root was never persisted, create it now. This is
        # what keeps every update nested under one thread.
        thread_ts = await self._ensure_thread(job)
        if not thread_ts:
            return  # root post failed (error already logged)

        if previous_state is None:
            return  # first report was the root itself; nothing more to say

        # State transition - post into the thread
        message = self._get_state_message(job, previous_state)
        await self._post(message, thread_ts)

        # Special handling for final states
        if job.state == "checks_passed":
            await self._notify_oncall_success(job, thread_ts)
        elif job.state in ["checks_failed", "needs_human"]:
            await self._notify_oncall_failure(job, thread_ts)

    async def _ensure_thread(self, job: Job) -> str:
        """Return the job's thread_ts, creating (and persisting) the root if missing."""
        if job.slack_thread_ts:
            return job.slack_thread_ts

        session_link = f"<https://app.devin.ai/sessions/{job.devin_session_id}|Session>"
        issue_link = (
            f"<{job.issue_url}|Issue #{job.issue_number}>"
            if job.issue_url else f"Issue #{job.issue_number}"
        )
        message = f"Job #{job.id}: {issue_link}\n{session_link}\nStatus: {job.state}"
        response = await self._post(message)
        if not response or not response.get("ok"):
            return None

        # Slack returns the thread parent as the top-level `ts` (message.ts is the same).
        ts = response.get("ts") or response.get("message", {}).get("ts")
        job.slack_thread_ts = ts  # keep the in-memory object consistent for this run
        with SessionLocal() as session:
            session.query(Job).filter(Job.id == job.id).update({"slack_thread_ts": ts})
            session.commit()
        return ts

    async def _post(self, text: str, thread_ts: str = None) -> dict:
        """Post and surface Slack-level errors (raise_for_status only catches HTTP)."""
        response = await self.slack.post_message(text, thread_ts)
        if not response.get("ok"):
            print(f"Slack post failed: {response.get('error')} (thread_ts={thread_ts})")
        return response
    
    def _get_state_message(self, job: Job, previous_state: str) -> str:
        """Generate message for state transition"""
        messages = {
            "fixing": "Devin is working on the fix",
            "checks_running": f"PR #{job.pr_number} opened — automated checks running",
            "checks_passed": "Automated checks passed — ready for human review (not auto-merged)",
            "checks_failed": f"Automated checks failed after {job.attempts} attempt(s)",
            "needs_human": "Needs a human — Devin couldn't finish",
            "merged": f"🎉 PR #{job.pr_number} merged — fix shipped",
        }
        return messages.get(job.state, f"{previous_state} → {job.state}")
    
    async def _notify_oncall_success(self, job: Job, thread_ts: str):
        """Notify on-call for successful validation"""
        pr_link = f"<https://github.com/haveitjoewei/superset/pull/{job.pr_number}|PR #{job.pr_number}>" if job.pr_number else "No PR"
        message = f"Ready for human review: {pr_link}. Automated checks passed — not auto-merged."
        await self.slack.notify_oncall(message, thread_ts)
    
    async def _notify_oncall_failure(self, job: Job, thread_ts: str):
        """Notify on-call for failure"""
        reason = job.notes or "Unknown reason"
        message = f"Job needs attention: {reason}"
        await self.slack.notify_oncall(message, thread_ts)