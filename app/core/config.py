from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Credit Scoring Monitor", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    environment: str = Field(default="local", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/data_monitor",
        alias="DATABASE_URL",
    )
    drift_threshold: float = Field(default=0.5, alias="DRIFT_THRESHOLD")
    feature_drift_threshold: float = Field(default=0.4, alias="FEATURE_DRIFT_THRESHOLD")
    alert_threshold: float = Field(default=0.7, alias="ALERT_THRESHOLD")
    baseline_path: str = Field(default="data/baseline_credit_scoring.csv", alias="BASELINE_PATH")
    model_version: str = Field(default="credit_scoring_v1", alias="MODEL_VERSION")
    reports_dir: str = Field(default="reports", alias="REPORTS_DIR")
    timezone: str = Field(default="Europe/Minsk", alias="TIMEZONE")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:8000"],
        alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
