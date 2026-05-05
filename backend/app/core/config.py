from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KFC Forecast"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./kfc_forecast.db"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    forecast_timezone: str = "Asia/Jerusalem"
    forecast_run_hour: int = Field(default=2, ge=0, le=23)
    forecast_lookback_days: int = Field(default=14, ge=1, le=365)
    seed_database: bool = True
    enable_scheduler: bool = True
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
