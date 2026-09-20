import httpx
from config import settings

class DevinClient:
    def __init__(self):
        self.base_url = settings.DEVIN_API_BASE
        self.api_key = settings.DEVIN_API_KEY
        self.org_id = settings.DEVIN_ORG_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_session(self, prompt: str, session_links: list = None) -> dict:
        """Create a new Devin session"""
        url = f"{self.base_url}/organizations/{self.org_id}/sessions"
        payload = {
            "prompt": prompt,
            "session_links": session_links or [],
            "structured_output_required": True,
            "structured_output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "dependency_name": {"type": "string"},
                    "current_version": {"type": "string"},
                    "target_version": {"type": "string"},
                    "files_changed": {"type": "array", "items": {"type": "string"}},
                    "fix_summary": {"type": "string"},
                    "validation_status": {"type": "string"}
                }
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_session(self, session_id: str) -> dict:
        """Get session status"""
        url = f"{self.base_url}/organizations/{self.org_id}/sessions/{session_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def send_message(self, session_id: str, message: str) -> dict:
        """Send a follow-up message to a session"""
        url = f"{self.base_url}/organizations/{self.org_id}/sessions/{session_id}/messages"
        payload = {"message": message}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
