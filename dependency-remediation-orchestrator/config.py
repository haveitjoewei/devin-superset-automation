from pydantic_settings import BaseSettings
from pydantic import AliasChoices, Field

class Settings(BaseSettings):
    # Devin API
    DEVIN_API_KEY: str
    DEVIN_API_BASE: str = "https://api.devin.ai/v3"
    DEVIN_ORG_ID: str
    
    # GitHub
    GITHUB_TOKEN: str
    GITHUB_WEBHOOK_SECRET: str
    TARGET_REPO: str = "haveitjoewei/superset"
    REQUIRED_CHECKS: str = ""  # comma-separated GitHub Actions check names
    ALLOW_SIMULATED_EVENTS: bool = False
    
    # Slack
    SLACK_BOT_TOKEN: str = ""
    SLACK_CHANNEL_ID: str = ""
    ONCALL_SLACK_USER_ID: str = ""
    
    # Server
    WORKER_POLL_INTERVAL: int = 30
    CONCURRENCY_CAP: int = Field(default=2, ge=1)
    # Blocks new sessions after this much recorded live usage; not a hard budget.
    ACU_ADMISSION_CAP: float = Field(default=100.0, ge=0, validation_alias=AliasChoices("ACU_ADMISSION_CAP", "DAILY_COST_CAP"))
    
    # Database
    DATABASE_URL: str = "postgresql://josephwei@localhost:5432/devin_jobs"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
