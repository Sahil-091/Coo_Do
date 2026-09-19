from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Secrets are supplied by the deployment, never the client."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://localhost/campus_connect"
    reviewer_database_url: str | None = None
    internal_shared_secret: str = "dev-only-change-me"
    safety_reviewer_token: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    safety_resources_file: Path = Path("/app/config/crisis_resources.india.json")


settings = Settings()
