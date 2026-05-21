"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration — reads from .env automatically."""

    # App
    APP_NAME: str = "CIRO"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Live Ingestion / Stress Testing ────────────
    USE_LIVE_APIS: bool = True
    SIGNAL_DEDUP_WINDOW_SECONDS: int = 180
    SIGNAL_MAX_AGE_MINUTES: int = 120
    LIVE_WEATHER_LAT: float = 33.6844
    LIVE_WEATHER_LON: float = 73.0479
    LIVE_WEATHER_LABEL: str = "Islamabad"

    model_config = {"extra": "ignore"}


settings = Settings()
