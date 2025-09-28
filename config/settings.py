"""Configuration settings for the Spotify analyzer application."""

import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    spotify_client_id: str
    spotify_client_secret: str
    default_timezone: Optional[str] = "local"

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings.

    Loads environment variables from .env file if present,
    then validates and returns the settings.

    Returns:
        Settings: Validated application settings

    Raises:
        ValidationError: If required settings are missing or invalid
    """
    load_dotenv()
    return Settings()
