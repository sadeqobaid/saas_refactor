"""
Configuration settings for the SaaS Platform.

This module provides centralized configuration management using Pydantic.
"""

import os
import secrets
from typing import Any, Optional, List
from dotenv import load_dotenv
from pydantic import PostgresDsn, validator
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

# Generate a secret key if not provided
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Email settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "user@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "password")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@example.com")


class Settings(BaseSettings):
    """
    Application settings class using Pydantic for validation.

    This class provides type validation and default values for all application settings.
    """
    PROJECT_NAME: str = "SaaS Platform"
    API_V1_STR: str = ""

    # Database settings
    DATABASE_URL: PostgresDsn
    DB_POOL_SIZE: int = 5  # Default value for connection pool size
    DB_MAX_OVERFLOW: int = 10  # Default value for max overflow

    # Redis settings
    REDIS_URL: str

    # Security settings
    SECRET_KEY: str = SECRET_KEY
    ALGORITHM: str = ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 10

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # Allow all origins by default

    # Email settings
    SMTP_SERVER: str = SMTP_SERVER
    SMTP_PORT: int = SMTP_PORT
    SMTP_USERNAME: str = SMTP_USERNAME
    SMTP_PASSWORD: str = SMTP_PASSWORD
    EMAIL_FROM: str = EMAIL_FROM

    # Validators
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: Optional[str]) -> Any:
        """Validate and format the database URL."""
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user="postgres",
            password="password",
            host="localhost",
            path="/saas_platform",
        )

    @validator("DB_POOL_SIZE", "DB_MAX_OVERFLOW", pre=True)
    def validate_pool_settings(cls, v: str) -> int:
        """
        Validate and convert pool settings to integers.
        Ensures that DB_POOL_SIZE and DB_MAX_OVERFLOW are valid integers.
        """
        if isinstance(v, str):
            return int(v)
        return v

    class Config:
        """Pydantic config class."""
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()