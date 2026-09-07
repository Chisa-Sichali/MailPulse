from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "MailPulse"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    database_url: str = Field(
        default="postgresql+asyncpg://mailpulse:mailpulse@localhost:5433/mailpulse",
        description="Async SQLAlchemy database URL",
    )

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for queues and token blocklist",
    )

    jwt_secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for signing JWT access tokens",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cron_secret_key: str | None = Field(
        default=None,
        description="Bearer token that must accompany automated cron requests "
        "(verified via secrets.compare_digest in app/core/security/cron.py)",
    )

    credential_encryption_key: str | None = Field(
        default=None,
        description="Dedicated key for encrypting mailbox credentials at rest",
    )

    email_monitor_poll_interval_seconds: int = Field(
        default=60,
        ge=30,
        description="Interval between mailbox monitor sweeps",
    )
    arq_max_tries: int = Field(default=4, ge=1, le=10)
    arq_job_timeout: int = Field(default=300, ge=30)

    webhook_max_attempts: int = Field(default=4, ge=1, le=10)
    webhook_retry_delays_seconds: list[int] = Field(
        default=[60, 300, 1800, 7200],
        description="Retry delays for failed webhook deliveries",
    )

    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ],
        description="Allowed CORS origins for the dashboard",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
