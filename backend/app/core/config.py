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

    # ── Google Gemini / ADK (REQUIRED) ──────────────
    GOOGLE_API_KEY: str = "AIzaSyCgM_IOZPnl-_z1Z3AxUkUlbgNEi6mr_P8"
    GEMINI_MODEL: str = "gemini-flash-latest"

    # ── Google Maps (REQUIRED for Flutter map widget) ─
    GOOGLE_MAPS_API_KEY: str = "AIzaSyB3Yjt4vr-b-6ZCmJiDP0fZl2Co8BmRPLQ"

    # ── OpenWeatherMap (OPTIONAL) ───────────────────
    OPENWEATHER_API_KEY: str = ""

    # ── TomTom Traffic (OPTIONAL) ───────────────────
    TOMTOM_API_KEY: str = ""

    # ── Live Ingestion / Stress Testing ────────────
    USE_LIVE_APIS: bool = False
    SIGNAL_DEDUP_WINDOW_SECONDS: int = 180
    SIGNAL_MAX_AGE_MINUTES: int = 120
    LIVE_WEATHER_LAT: float = 33.6844
    LIVE_WEATHER_LON: float = 73.0479
    LIVE_WEATHER_LABEL: str = "Islamabad"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
