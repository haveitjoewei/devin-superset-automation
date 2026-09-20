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
        
        if previous_state is None:
            # Job started - create root message with more context
            session_link = f"<https://app.devin.ai/sessions/{job.devin_session_id}|Session>"
            issue_link = f"<{job.issue_url}|Issue #{job.issue_number}>" if job.issue_url else f"Issue #{job.issue_number}"
            message = f"Job #{job.id}: {issue_link}\n{session_link}\nStatus: {job.state}"
            response = await self.slack.post_message(message)
            
            # Save thread_ts for future updates
            if response.get("ok"):
                with SessionLocal() as session:
                    session.query(Job).filter(Job.id == job.id).update({
                        "slack_thread_ts": response.get("message", {}).get("ts")
                    })
                    session.commit()
        else:
            # State transition - post to thread
            thread_ts = job.slack_thread_ts
            if not thread_ts:
                return  # No thread to post to
            
            message = self._get_state_message(job, previous_state)
            await self.slack.post_message(message, thread_ts)
            
            # Special handling for final states
            if job.state == "validated":
                await self._notify_oncall_success(job, thread_ts)
            elif job.state in ["failed", "needs_human"]:
                await self._notify_oncall_failure(job, thread_ts)
    
    def _get_state_message(self, job: Job, previous_state: str) -> str:
        """Generate message for state transition"""
        messages = {
            "session_started": f"Session started",
            "pr_opened": f"<https://github.com/haveitjoewei/superset/pull/{job.pr_number}|PR #{job.pr_number}>",
            "verifying": "CI verification in progress",
            "validated": "Validated successfully",
            "failed": f"Failed after {job.attempts} attempt(s)",
            "needs_human": "Requires human intervention"
        }
        return messages.get(job.state, f"{previous_state} → {job.state}")
    
    async def _notify_oncall_success(self, job: Job, thread_ts: str):
        """Notify on-call for successful validation"""
        pr_link = f"<https://github.com/haveitjoewei/superset/pull/{job.pr_number}|PR #{job.pr_number}>" if job.pr_number else "No PR"
        message = f"Ready for review: {pr_link}. CI green, rescan clear."
        await self.slack.notify_oncall(message, thread_ts)
    
    async def _notify_oncall_failure(self, job: Job, thread_ts: str):
        """Notify on-call for failure"""
        reason = job.notes or "Unknown reason"
        message = f"Job needs attention: {reason}"
        await self.slack.notify_oncall(message, thread_ts)