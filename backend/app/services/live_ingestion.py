"""
Live ingestion utilities for external data sources (e.g., Open-Meteo weather API).
Uses free Open-Meteo API (no API key required) for worldwide weather data.
Also includes mock IoT sensors for flood/infrastructure detection.
"""

from __future__ import annotations

import logging
import random
from typing import Optional

import httpx

from app.core.config import settings
from app.schemas import GeoLocation, IngestedSignal, SignalSource, WeatherMetrics
from app.store import store

logger = logging.getLogger("ciro.ingestion.live")
logger.setLevel(logging.INFO)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def _build_weather_signal(data: dict) -> Optional[IngestedSignal]:
    """Convert Open-Meteo forecast data to IngestedSignal."""
    try:
        # Extract current weather from Open-Meteo response
        current = data.get("current", {})
        
        temp_c = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        precipitation = current.get("precipitation", 0.0)
        rain = current.get("rain", 0.0)
        wind_speed_kmh = current.get("wind_speed_10m")
        
        # Determine weather condition from WMO code
        wmo_code = current.get("weather_code", 0)
        weather_desc = _decode_wmo_code(wmo_code)
        
        # Calculate rainfall (precipitation includes all types)
        rainfall_mm = max(precipitation, rain)
        
        summary = weather_desc or "Live weather update"
        raw_text = (
            f"Open-Meteo weather: {summary} in {settings.LIVE_WEATHER_LABEL}. "
            f"Temp {temp_c}°C, humidity {humidity}%, rain {rainfall_mm}mm, "
            f"wind {wind_speed_kmh} km/h."
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
            reliability_score=0.95,  # Open-Meteo is very reliable
        )
    except (KeyError, TypeError) as e:
        logger.error("Error parsing Open-Meteo response: %s", e)
        return None


def _decode_wmo_code(code: int) -> str:
    """Decode WMO weather code to human-readable description."""
    # WMO Weather interpretation codes
    wmo_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return wmo_codes.get(code, f"Weather code {code}")


async def fetch_weather_signal() -> Optional[IngestedSignal]:
    """Fetch current weather from Open-Meteo API (free, no API key required)."""
    params = {
        "latitude": settings.LIVE_WEATHER_LAT,
        "longitude": settings.LIVE_WEATHER_LON,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation,rain",
        "timezone": "Asia/Karachi",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Open-Meteo request failed: %s", exc)
        return None

    try:
        data = response.json()
        logger.debug("Open-Meteo response: %s", data)
        return _build_weather_signal(data)
    except (TypeError, ValueError, KeyError) as exc:
        logger.error("Open-Meteo response parsing error: %s", exc)
        return None


async def seed_live_signals() -> int:
    """Seed live signals from Open-Meteo weather API and mock IoT sensors."""
    signals: list[IngestedSignal] = []

    # Fetch live weather
    weather_signal = await fetch_weather_signal()
    if weather_signal:
        signals.append(weather_signal)
        logger.info("Fetched live weather signal from Open-Meteo for %s", settings.LIVE_WEATHER_LABEL)
    else:
        logger.warning("Failed to fetch live weather signal; skipping.")

    # Fetch mock sensor readings
    sensor_signals = await fetch_mock_sensor_signals()
    signals.extend(sensor_signals)
    logger.info("Generated %d mock IoT sensor readings.", len(sensor_signals))

    for sig in signals:
        await store.add_signal(sig)

    if signals:
        logger.info("Live ingestion seeded %d signal(s) total (weather + sensors).", len(signals))
    else:
        logger.info("No live signals to seed.")
    return len(signals)


def _build_mock_sensor_signal(sensor_type: str, location_label: str, lat: float, lon: float) -> IngestedSignal:
    """Generate mock IoT sensor reading for flood/infrastructure detection."""
    
    if sensor_type == "water_level":
        # Mock water level sensor reading
        water_level_cm = random.uniform(15, 85)  # 15-85 cm = normal to flooding
        is_critical = water_level_cm > 60
        
        raw_text = (
            f"IoT WATER LEVEL SENSOR @ {location_label}: "
            f"Level {water_level_cm:.1f}cm ({'⚠️ CRITICAL' if is_critical else '✓ normal'}). "
            f"Threshold: 60cm. Drainage pump status: active."
        )
    elif sensor_type == "air_quality":
        # Mock air quality sensor (useful for chemical spills)
        pm25 = random.uniform(15, 150)  # Particulate matter
        is_poor = pm25 > 100
        
        raw_text = (
            f"IoT AIR QUALITY @ {location_label}: "
            f"PM2.5 {pm25:.0f} µg/m³ ({'⚠️ HAZARDOUS' if is_poor else '✓ good'}). "
            f"Wind direction: NE at 8 km/h."
        )
    else:  # temperature
        temp = random.uniform(28, 48)  # 28-48°C
        is_extreme = temp > 42
        
        raw_text = (
            f"IoT TEMPERATURE SENSOR @ {location_label}: "
            f"{temp:.1f}°C ({'🔥 EXTREME HEAT' if is_extreme else '✓ normal'}). "
            f"Heat index: {temp + random.uniform(0, 8):.1f}°C."
        )
    
    return IngestedSignal(
        source=SignalSource.IOT_DEVICE,
        raw_text=raw_text,
        location=GeoLocation(latitude=lat, longitude=lon, label=location_label),
        reliability_score=0.85,  # IoT sensors are quite reliable
        metadata={
            "sensor_type": sensor_type,
            "device_id": f"IOT-{sensor_type.upper()}-{random.randint(100, 999)}"
        }
    )


async def fetch_mock_sensor_signals() -> list[IngestedSignal]:
    """Generate mock sensor readings from multiple locations."""
    signals = []
    
    # Mock sensor locations in Islamabad
    sensor_locations = [
        ("G-10 Sector", 33.7, 73.0, ["water_level", "temperature"]),
        ("F-8 Markaz", 33.67, 73.18, ["temperature", "air_quality"]),
        ("Aabpara", 33.72, 73.02, ["water_level"]),
    ]
    
    for label, lat, lon, sensor_types in sensor_locations:
        # Randomly pick 1-2 sensor types from each location
        for sensor_type in random.sample(sensor_types, k=random.randint(1, len(sensor_types))):
            sig = _build_mock_sensor_signal(sensor_type, label, lat, lon)
            signals.append(sig)
    
    return signals

