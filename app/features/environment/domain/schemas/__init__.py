"""Schemas for environment feature"""
from app.features.environment.domain.schemas.weather import (
    WeatherData,
    Location,
    WeatherResponse,
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
    "AirQualityResponse",
    "PollenRisk",
    "PollenCount",
    "SpeciesData",
    "PollenResponse",
]
