from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    finnhub_api_key: str | None = None
    anthropic_api_key: str | None = None
    admin_user: str = "signal-admin"
    admin_password: str | None = None
    hubspot_access_token: str | None = None
    public_base_url: str = "http://localhost:8000"
    tz: str = "UTC"

    @field_validator("database_url")
    @classmethod
    def _use_psycopg3_driver(cls, v: str) -> str:
        # Railway's Postgres plugin (and most hosts) hand out a bare "postgres://" or
        # "postgresql://" URL, which makes SQLAlchemy default to psycopg2 — not installed,
        # since this project uses psycopg3 (see requirements.txt). Rewrite the scheme so
        # deploys work without needing a hand-constructed DATABASE_URL in the dashboard.
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix) and "+psycopg" not in v.split("://", 1)[0]:
                return "postgresql+psycopg://" + v[len(prefix) :]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
