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

    async def get(self, path: str, params=None):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/{path}", headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    async def verification(self, repo: str, pr_number: int):
        """Read explicitly configured checks on the PR's current head commit."""
        required = {name.strip() for name in settings.REQUIRED_CHECKS.split(",") if name.strip()}
        pr = await self.get(f"repos/{repo}/pulls/{pr_number}")
        sha = pr["head"]["sha"]
        if not required:
            return sha, "pending", "Set REQUIRED_CHECKS to the GitHub Actions checks to verify."
        runs = []
        page = 1
        while True:
            data = await self.get(f"repos/{repo}/commits/{sha}/check-runs",
                                  {"per_page": 100, "page": page, "filter": "latest"})
            batch = data["check_runs"]
            runs.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        latest = {}
        for run in runs:
            if run.get("head_sha") != sha or run.get("app", {}).get("slug") != "github-actions":
                continue
            name = run["name"]
            if name not in latest or run["id"] > latest[name]["id"]:
                latest[name] = run
        current = await self.get(f"repos/{repo}/pulls/{pr_number}")
        if current["head"]["sha"] != sha:
            return current["head"]["sha"], "pending", "Head commit changed during verification."
        selected = [latest.get(name) for name in required]
        if any(run is None or run["status"] != "completed" for run in selected):
            return sha, "pending", "Waiting for all configured checks on the current commit."
        if all(run["conclusion"] == "success" for run in selected):
            return sha, "success", f"Configured checks passed on {sha}."
        failures = [run for run in selected if run["conclusion"] != "success"]
        return sha, "failure", "; ".join(f"{run['name']}: {run.get('html_url', run['conclusion'])}" for run in failures)

    async def comment_on_issue(self, owner: str, repo: str, issue_number: int, body: str) -> dict:
        """Post comment on GitHub issue"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        payload = {"body": body}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
