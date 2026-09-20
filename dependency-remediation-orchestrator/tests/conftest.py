"""Test setup: dummy env + path so app modules import without real credentials."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DEVIN_API_KEY", "test")
os.environ.setdefault("DEVIN_ORG_ID", "test")
os.environ.setdefault("GITHUB_TOKEN", "test")
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "testsecret")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
