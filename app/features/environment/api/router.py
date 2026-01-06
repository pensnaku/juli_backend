"""API router for environment feature - weather, air quality, pollen"""
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.domain.entities import User
from app.features.environment.service import WeatherService, AirQualityService
from app.features.environment.domain.schemas import (
    WeatherResponse,
    AirQualityResponse,
    PollenResponse,
)
from app.features.environment.exceptions import WeatherException, AirQualityException
from app.features.observations.repository import ObservationRepository
from app.features.observations.constants import (
    ObservationCodes,
    EnvironmentVariants,
    ObservationDataSources,
)


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


@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_environment_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch and save current environment data (weather, air quality, pollen) as observations.

    This endpoint:
    1. Fetches current weather, air quality, and pollen data for the given location
    2. Stores all metrics as observations with code='environment' and appropriate variants
    3. Returns a summary of saved observations

    All observations are stored with the current timestamp.

    Returns:
        Dictionary with counts of saved observations by category
    """
    observation_repo = ObservationRepository(db)
    current_time = datetime.now(timezone.utc)
    saved_count = 0

    try:
        # Fetch all environment data
        weather_service = _get_weather_service()
        air_quality_service = _get_air_quality_service()

        weather = await weather_service.get_weather(lat, lon)
        air_quality = await air_quality_service.get_air_quality(lat, lon)
        pollen = await air_quality_service.get_pollen(lat, lon)

        # Save air quality
        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.AIR_QUALITY_INDEX,
            value_integer=air_quality.airQualityIndex,
            category="environment",
            data_source=ObservationDataSources.AMBEE,
            effective_at=current_time,
        )
        saved_count += 1

        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.AIR_QUALITY_POLLUTANT,
            value_string=air_quality.mainPollutant,
            category="environment",
            data_source=ObservationDataSources.AMBEE,
            effective_at=current_time,
        )
        saved_count += 1

        # Save pollen data
        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.POLLEN_GRASS,
            value_integer=pollen.count.grass,
            category="environment",
            data_source=ObservationDataSources.AMBEE,
            effective_at=current_time,
        )
        saved_count += 1

        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.POLLEN_TREE,
            value_integer=pollen.count.tree,
            category="environment",
            data_source=ObservationDataSources.AMBEE,
            effective_at=current_time,
        )
        saved_count += 1

        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.POLLEN_WEED,
            value_integer=pollen.count.weed,
            category="environment",
            data_source=ObservationDataSources.AMBEE,
            effective_at=current_time,
        )
        saved_count += 1

        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.POLLEN_TOTAL,
            value_integer=pollen.count.grass + pollen.count.tree + pollen.count.weed,
            category="environment",
            data_source=ObservationDataSources.AMBEE,
            effective_at=current_time,
        )
        saved_count += 1

        # Save weather data
        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.TEMPERATURE,
            value_decimal=weather.current.temperature,
            unit="celsius",
            category="environment",
            data_source=ObservationDataSources.OPENWEATHERMAP,
            effective_at=current_time,
        )
        saved_count += 1

        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.HUMIDITY,
            value_integer=weather.current.humidity,
            unit="percent",
            category="environment",
            data_source=ObservationDataSources.OPENWEATHERMAP,
            effective_at=current_time,
        )
        saved_count += 1

        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.AIR_PRESSURE,
            value_integer=weather.current.atmosphericPressure,
            unit="hPa",
            category="environment",
            data_source=ObservationDataSources.OPENWEATHERMAP,
            effective_at=current_time,
        )
        saved_count += 1

        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.WIND_SPEED,
            value_decimal=weather.current.windStrength,
            unit="m/s",
            category="environment",
            data_source=ObservationDataSources.OPENWEATHERMAP,
            effective_at=current_time,
        )
        saved_count += 1

        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.WIND_DIRECTION,
            value_integer=weather.current.windDirection,
            unit="degrees",
            category="environment",
            data_source=ObservationDataSources.OPENWEATHERMAP,
            effective_at=current_time,
        )
        saved_count += 1

        # Save sunrise/sunset as timestamps
        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.SUNRISE,
            value_string=weather.current.sunrise.isoformat(),
            category="environment",
            data_source=ObservationDataSources.OPENWEATHERMAP,
            effective_at=current_time,
        )
        saved_count += 1

        observation_repo.create(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            variant=EnvironmentVariants.SUNSET,
            value_string=weather.current.sunset.isoformat(),
            category="environment",
            data_source=ObservationDataSources.OPENWEATHERMAP,
            effective_at=current_time,
        )
        saved_count += 1

        db.commit()

        return {
            "message": "Environment data saved successfully",
            "saved_observations": saved_count,
            "timestamp": current_time.isoformat(),
            "location": {
                "lat": lat,
                "lon": lon,
                "city": weather.location.city,
                "country": weather.location.country,
            },
        }

    except (WeatherException, AirQualityException) as e:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail={"error": "Cannot fetch data from external API", "code": "external_api_error"},
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error": f"Failed to save environment data: {str(e)}", "code": "internal_error"},
        )
