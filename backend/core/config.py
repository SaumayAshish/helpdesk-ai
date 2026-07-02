"""
Application configuration loaded from environment variables.

Uses Pydantic Settings for type-safe config with automatic .env loading.
All settings are validated at app startup — invalid config crashes early.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # =====================================================
    # Pydantic settings configuration
    # =====================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # =====================================================
    # Application
    # =====================================================
    APP_NAME: str = "helpdesk-ai"
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"

    # =====================================================
    # FastAPI Server
    # =====================================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # =====================================================
    # Database (PostgreSQL)
    # =====================================================
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "helpdesk_ai"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = Field(..., description="Postgres password — required")
    DATABASE_URL: PostgresDsn

    # Connection pool tuning
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False  # set True to log all SQL (dev debugging)

    # =====================================================
    # JWT Authentication (used in Milestone 3)
    # =====================================================
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # =====================================================
    # Logging
    # =====================================================
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"

    # =====================================================
    # Rate limiting (Milestone 10) — brute-force protection
    # =====================================================
    # Strings use slowapi/limits syntax: "<count>/<period>"
    # (period is one of second, minute, hour, day).
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"

    # =====================================================
    # CORS
    # =====================================================
    FRONTEND_URL: str = "http://localhost:8501"
    CORS_ORIGINS: list[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]

    # =====================================================
    # ML
    # =====================================================
    ML_MODEL_PATH: str = "ml/models/"
    ML_PRIORITY_MODEL: str = "priority_classifier.pkl"
    ML_DEPARTMENT_MODEL: str = "department_classifier.pkl"
    ML_SLA_MODEL: str = "sla_predictor.pkl"

    # =====================================================
    # Computed properties
    # =====================================================
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def log_file_full_path(self) -> Path:
        """Ensure log directory exists and return absolute path."""
        path = Path(self.LOG_FILE_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret isn't a placeholder value."""
        weak_values = {
            "changeme",
            "secret",
            "your-secret-key",
            "replace_with_long_random_string_min_32_chars",
        }
        if v.lower() in weak_values:
            raise ValueError("JWT_SECRET_KEY appears to be a placeholder — set a real secret")
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    @lru_cache ensures we read .env only once per process.
    Used as a FastAPI dependency: `settings: Settings = Depends(get_settings)`.
    """
    return Settings()


# Convenience singleton (for use outside FastAPI DI, e.g., scripts)
settings = get_settings()
