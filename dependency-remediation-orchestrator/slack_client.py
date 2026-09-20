import httpx
from config import settings

class SlackClient:
    def __init__(self):
        self.base_url = "https://slack.com/api"
        self.bot_token = settings.SLACK_BOT_TOKEN
        self.channel_id = settings.SLACK_CHANNEL_ID
        self.oncall_user_id = settings.ONCALL_SLACK_USER_ID
        self.headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
    
    async def post_message(self, text: str, thread_ts: str = None) -> dict:
        """Post a message to Slack, optionally in a thread"""
        url = f"{self.base_url}/chat.postMessage"
        payload = {
            "channel": self.channel_id,
            "text": text
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def notify_oncall(self, text: str, thread_ts: str = None) -> dict:
        """Notify on-call with @mention"""
        message = f"<@{self.oncall_user_id}> {text}"
        return await self.post_message(message, thread_ts)