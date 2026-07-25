"""Application configuration using pydantic-settings."""

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project Root
# backend/app/config.py
# parents[0] = app
# parents[1] = backend
# parents[2] = project root
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================
    # Application
    # ==========================================================
    APP_NAME: str = "Crime Intelligence Platform"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "CRIME - INTELLIGENCE"

    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    API_V1_PREFIX: str = "/api/v1"

    @field_validator("API_V1_PREFIX", mode="before")
    @classmethod
    def fix_api_prefix(cls, value: object) -> str:
        """Ensure prefix is always /api/v1 regardless of env/shell path mangling."""
        return "/api/v1"

    # ==========================================================
    # Server
    # ==========================================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # ==========================================================
    # Database
    # ==========================================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/crime_intelligence"
    )

    DATABASE_URL_SYNC: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/crime_intelligence"
    )

    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # ==========================================================
    # Authentication
    # ==========================================================
    SECRET_KEY: str  # Must be set via environment variable

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==========================================================
    # Gemini AI
    # ==========================================================
    GEMINI_API_KEY: Optional[str] = None

    # ==========================================================
    # Chat Upload
    # ==========================================================
    CHAT_UPLOAD_DIR: Path = Path("uploads/chat")

    CHAT_UPLOAD_MAX_SIZE: int = 20 * 1024 * 1024

    # ==========================================================
    # Logging
    # ==========================================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = "logs/app.log"

    # ==========================================================
    # Rate Limiting
    # ==========================================================
    RATE_LIMIT_ENABLED: bool = True

    RATE_LIMIT_DEFAULT: str = "60/minute"

    LOGIN_RATE_LIMIT: str = "10/minute"

    # ==========================================================
    # Redis
    # ==========================================================
    REDIS_URL: Optional[str] = None

    CACHE_TTL_SECONDS: int = 300

    # ==========================================================
    # Security
    # ==========================================================
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, value: object) -> List[str]:
        """Parse ALLOWED_HOSTS from a comma-separated string or JSON list."""
        if isinstance(value, str):
            # Comma-separated: "localhost,127.0.0.1,example.com"
            parts = [h.strip() for h in value.split(",") if h.strip()]
            if parts:
                return parts
            # Empty string after stripping means wildcard
            return ["*"]
        if isinstance(value, list):
            return value
        return ["localhost", "127.0.0.1"]

    # ==========================================================
    # CORS
    # ==========================================================
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ==========================================================
    # Validators
    # ==========================================================
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"development", "staging", "production"}
        value = value.lower()

        if value not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")

        return value

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        value = value.upper()

        if value not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")

        return value

    # ==========================================================
    # Convenience Properties
    # ==========================================================
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def database_url_async(self) -> str:
        return self.DATABASE_URL

    @property
    def database_url_sync(self) -> str:
        return self.DATABASE_URL_SYNC


settings = Settings()
