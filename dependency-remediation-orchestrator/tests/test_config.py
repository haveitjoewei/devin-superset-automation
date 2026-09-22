from config import Settings


def test_old_env_entries_do_not_break_settings(tmp_path, monkeypatch):
    monkeypatch.delenv("CONCURRENCY_CAP", raising=False)
    env_file = tmp_path / ".env"
    retired = {
        "API_PORT": "9000",
        "SUPERSET_HOST": "http://localhost:8088",
        "SUPERSET_USERNAME": "admin",
        "SUPERSET_PASSWORD": "unused",
        "SUPERSET_DATABASE_NAME": "devin_jobs",
    }
    env_file.write_text("CONCURRENCY_CAP=3\n" + "\n".join(
        f"{key}={value}" for key, value in retired.items()
    ))

    settings = Settings(_env_file=env_file)

    assert settings.CONCURRENCY_CAP == 3
    assert not retired.keys() & settings.model_dump().keys()
