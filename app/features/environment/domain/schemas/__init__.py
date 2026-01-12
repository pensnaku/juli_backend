"""Schemas for environment feature"""
from app.features.environment.domain.schemas.weather import (
    WeatherData,
    Location,
    WeatherResponse,
    HistoricalWeatherResponse,
)
from app.features.environment.domain.schemas.air_quality import (
    AirQualityResponse,
)
from app.features.environment.domain.schemas.pollen import (
    PollenRisk,
    PollenCount,
    SpeciesData,
    PollenResponse,
)

__all__ = [
    "WeatherData",
    "Location",
    "WeatherResponse",
    "HistoricalWeatherResponse",
    "AirQualityResponse",
    "PollenRisk",
    "PollenCount",
    "SpeciesData",
    "PollenResponse",
]
