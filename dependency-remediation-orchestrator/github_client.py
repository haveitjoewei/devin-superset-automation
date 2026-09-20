import httpx
from config import settings

class GitHubClient:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.token = settings.GITHUB_TOKEN
        self.headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }
    
    async def get_issue(self, owner: str, repo: str, issue_number: int) -> dict:
        """Get GitHub issue details"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def comment_on_issue(self, owner: str, repo: str, issue_number: int, body: str) -> dict:
        """Post comment on GitHub issue"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        payload = {"body": body}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_pr(self, owner: str, repo: str, pr_number: int) -> dict:
        """Get pull request details"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_check_runs(self, owner: str, repo: str, commit_sha: str) -> dict:
        """Get check runs for a commit"""
        url = f"{self.base_url}/repos/{owner}/{repo}/commits/{commit_sha}/check-runs"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
