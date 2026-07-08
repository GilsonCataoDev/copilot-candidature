from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Copilot Candidature"
    app_env: str = "development"
    storage_dir: Path = Path("storage")
    database_path: Path = Path("storage/app.db")
    google_api_key: str | None = None
    google_search_engine_id: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
