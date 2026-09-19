from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://localhost/campus_connect"
    reviewer_database_url: str | None = None
    internal_shared_secret: str = "dev-only-change-me"
    moderation_reviewer_token: str | None = None
    core_api_internal_url: str = "http://localhost:8000"
    safety_service_internal_url: str = "http://localhost:8001"


settings = Settings()
