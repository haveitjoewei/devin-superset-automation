from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Devin API
    DEVIN_API_KEY: str
    DEVIN_API_BASE: str = "https://api.devin.ai/v3"
    DEVIN_ORG_ID: str
    
    # GitHub
    GITHUB_TOKEN: str
    GITHUB_WEBHOOK_SECRET: str
    
    # Slack
    SLACK_BOT_TOKEN: str = ""
    SLACK_CHANNEL_ID: str = ""
    ONCALL_SLACK_USER_ID: str = ""
    
    # Server
    WORKER_POLL_INTERVAL: int = 30
    CONCURRENCY_CAP: int = 2
    # Cost guard: max Devin spend (ACUs) to start new work per day. 0 disables.
    DAILY_COST_CAP: float = 100.0
    
    # Database
    DATABASE_URL: str = "postgresql://josephwei@localhost:5432/devin_jobs"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
