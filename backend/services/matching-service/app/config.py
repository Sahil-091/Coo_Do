from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://localhost/campus_connect"
    internal_shared_secret: str = "dev-only-change-me"
    core_api_internal_url: str = "http://localhost:8000"


settings = Settings()
