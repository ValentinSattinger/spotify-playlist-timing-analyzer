"""Configuration settings for the Spotify analyzer application."""

import os
from functools import lru_cache
from typing import Optional

import streamlit as st
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or Streamlit secrets."""

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

    Loads settings from:
    1. Streamlit secrets (for deployed apps)
    2. Environment variables from .env file (for local development)

    Returns:
        Settings: Validated application settings

    Raises:
        ValidationError: If required settings are missing or invalid
    """
    # Try Streamlit secrets first (for deployed apps)
    try:
        if hasattr(st, 'secrets') and st.secrets:
            return Settings(
                spotify_client_id=st.secrets["spotify_client_id"],
                spotify_client_secret=st.secrets["spotify_client_secret"],
                default_timezone=st.secrets.get("default_timezone", "local")
            )
    except Exception:
        pass
    
    # Fall back to environment variables (for local development)
    load_dotenv()
    return Settings()
