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

    # Phase 6 Tiny Action Voice Layer.  The key is consumed only by the
    # core-api container; it is never sent to Next.js or a browser.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    tiny_action_voice_timeout_seconds: float = 8.0
    # Comma-separated Fernet keys, newest first. There is deliberately no
    # fallback: a deployment without a managed secret must refuse to start.
    # Keeping retired keys after the primary key permits a planned rotation.
    journal_encryption_keys: str
    # Managed, newest-first Fernet keyring for trusted-contact identity and
    # destination data. Separate from journal keys to allow independent
    # rotation and access controls.
    trusted_contact_encryption_keys: str
    moderation_service_internal_url: str = "http://localhost:8003"
    notification_service_internal_url: str = "http://localhost:8004"


settings = Settings()
