import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Devin API
    DEVIN_API_KEY: str
    DEVIN_API_BASE: str = "https://api.devin.ai/v3"
    DEVIN_ORG_ID: str
    
    # GitHub
    GITHUB_TOKEN: str
    GITHUB_WEBHOOK_SECRET: str
    
    # Server
    API_PORT: int = 8000
    WORKER_POLL_INTERVAL: int = 30
    CONCURRENCY_CAP: int = 2
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./jobs.db"
    
    class Config:
        env_file = ".env"

def get_settings():
    return Settings()

settings = get_settings()
