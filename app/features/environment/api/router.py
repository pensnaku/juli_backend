"""API router for environment feature - weather, air quality, pollen"""
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.features.environment.service import WeatherService, AirQualityService
from app.features.environment.domain.schemas import (
    WeatherResponse,
    AirQualityResponse,
    PollenResponse,
)
from app.features.environment.exceptions import WeatherException, AirQualityException


router = APIRouter()


def _get_weather_service() -> WeatherService:
    """Get weather service with API key from settings"""
    if not settings.OPENWEATHERMAP_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={"error": "Weather service not configured", "code": "service_unavailable"},
        )
    return WeatherService(settings.OPENWEATHERMAP_API_KEY)


def _get_air_quality_service() -> AirQualityService:
    """Get air quality service with API key from settings"""
    if not settings.AMBEE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={"error": "Air quality service not configured", "code": "service_unavailable"},
        )
    return AirQualityService(settings.AMBEE_API_KEY)


@router.get("/weather", response_model=WeatherResponse)
async def get_weather(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
):
    """
    Get current weather and forecast for a location.

    Returns current weather conditions and up to 12 forecast entries.
    Uses OpenWeatherMap API.
    """
    service = _get_weather_service()

    try:
        return await service.get_weather(lat, lon)
    except WeatherException as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "Cannot fetch data from external API", "code": "external_api_error"},
        )


@router.get("/air-quality", response_model=AirQualityResponse)
async def get_air_quality(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
):
    """
    Get air quality index for a location.

    Returns AQI value (0-500) and main pollutant.
    Uses Ambee API.

    AQI Scale:
    - 0-50: Good
    - 51-100: Moderate
    - 101-150: Unhealthy for Sensitive Groups
    - 151-200: Unhealthy
    - 201-300: Very Unhealthy
    - 301-500: Hazardous
    """
    service = _get_air_quality_service()

    try:
        return await service.get_air_quality(lat, lon)
    except AirQualityException as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "Cannot fetch data from external API", "code": "external_api_error"},
        )


@router.get("/air-quality/pollen", response_model=PollenResponse)
async def get_pollen(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
):
    """
    Get pollen levels and risk for a location.

    Returns risk levels (Low, Moderate, High, Very High) and counts
    for grass, tree, and weed pollen, plus detailed species breakdown.
    Uses Ambee API.
    """
    service = _get_air_quality_service()

    try:
        return await service.get_pollen(lat, lon)
    except AirQualityException as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "Cannot fetch data from external API", "code": "external_api_error"},
        )
