from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://localhost/campus_connect"

    # Shared secret that Next.js's server (never the browser) presents on
    # every call to any /internal/* route. This is the trust boundary
    # described in the Phase 2 build notes: core-api trusts a caller-
    # supplied user id ONLY when this secret is also present and correct.
    # Dev-only default below — MUST be overridden via env var before any
    # shared/staging/prod deployment, same as db/grants.sql's passwords.
    internal_shared_secret: str = "dev-only-change-me"


settings = Settings()
