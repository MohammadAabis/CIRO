"""
Live ingestion utilities for external data sources (e.g., OpenWeatherMap).
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.schemas import GeoLocation, IngestedSignal, SignalSource, WeatherMetrics
from app.store import store

logger = logging.getLogger("ciro.ingestion.live")
logger.setLevel(logging.INFO)

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def _build_weather_signal(payload: dict) -> IngestedSignal:
    weather_list = payload.get("weather") or []
    weather_main = ""
    weather_desc = ""
    if weather_list:
        weather_main = weather_list[0].get("main") or ""
        weather_desc = weather_list[0].get("description") or ""

    main = payload.get("main") or {}
    wind = payload.get("wind") or {}
    rain = payload.get("rain") or {}

    temp_c = main.get("temp")
    humidity = main.get("humidity")
    rainfall_mm = rain.get("1h", 0.0)
    wind_speed_kmh = None
    if wind.get("speed") is not None:
        wind_speed_kmh = float(wind["speed"]) * 3.6

    summary = weather_desc or weather_main or "live weather update"
    raw_text = (
        f"OpenWeatherMap: {summary} in {settings.LIVE_WEATHER_LABEL}. "
        f"Temp {temp_c}C, humidity {humidity}%, rain {rainfall_mm}mm."
    )

    return IngestedSignal(
        source=SignalSource.WEATHER_API,
        raw_text=raw_text,
        location=GeoLocation(
            latitude=settings.LIVE_WEATHER_LAT,
            longitude=settings.LIVE_WEATHER_LON,
            label=settings.LIVE_WEATHER_LABEL,
        ),
        weather=WeatherMetrics(
            temperature_c=temp_c,
            humidity_pct=humidity,
            rainfall_mm=rainfall_mm,
            wind_speed_kmh=wind_speed_kmh,
        ),
        reliability_score=0.9,
    )


async def fetch_openweather_signal() -> Optional[IngestedSignal]:
    if not settings.OPENWEATHER_API_KEY:
        logger.error("OPENWEATHER_API_KEY missing; cannot fetch live weather.")
        return None

    params = {
        "lat": settings.LIVE_WEATHER_LAT,
        "lon": settings.LIVE_WEATHER_LON,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPENWEATHER_URL, params=params)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("OpenWeatherMap request failed: %s", exc)
        return None

    try:
        payload = response.json()
        return _build_weather_signal(payload)
    except (TypeError, ValueError, KeyError) as exc:
        logger.error("OpenWeatherMap payload error: %s", exc)
        return None


async def seed_live_signals() -> int:
    signals: list[IngestedSignal] = []

    weather_signal = await fetch_openweather_signal()
    if weather_signal:
        signals.append(weather_signal)

    for sig in signals:
        await store.add_signal(sig)

    if signals:
        logger.info("Live ingestion seeded %d signal(s).", len(signals))
    return len(signals)
