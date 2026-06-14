from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ALLOWED_USERS: list[int] = Field(default_factory=list)
    TELEGRAM_CHANNEL_ID: str = ""
    TELEGRAM_CHANNEL_THREAD_ID: int = 0
    REDIS_URL: str = "redis://localhost:6379/0"
    ASTERDEX_BASE_URL: str = "https://fapi.asterdex.com"
    OI_THRESHOLD_PERCENT: float = 15.0
    OI_THRESHOLD_USD: int = 100_000
    POLL_INTERVAL_SECONDS: int = 60
    HISTORY_TTL_SECONDS: int = 3600

    @field_validator("TELEGRAM_ALLOWED_USERS", mode="before")
    @classmethod
    def split_allowed_users(cls, value: Any) -> list[int]:
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [int(item) for item in value]
        return []


settings = Settings()
