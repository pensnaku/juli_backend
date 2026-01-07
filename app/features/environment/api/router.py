"""API router for environment feature - weather, air quality, pollen"""
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, date, timedelta
from collections import defaultdict

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


def _save_environment_observations(
    repo: ObservationRepository,
    user_id: int,
    weather,
    air_quality,
    pollen,
    effective_time: datetime,
):
    """Helper function to save all 13 environment observations for a specific datetime"""
    # Save air quality (2 observations)
    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.AIR_QUALITY_INDEX,
        value_integer=air_quality.airQualityIndex,
        category="environment",
        data_source=ObservationDataSources.AMBEE,
        effective_at=effective_time,
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.AIR_QUALITY_POLLUTANT,
        value_string=air_quality.mainPollutant,
        category="environment",
        data_source=ObservationDataSources.AMBEE,
        effective_at=effective_time,
    )

    # Save pollen data (4 observations)
    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.POLLEN_GRASS,
        value_integer=pollen.count.grass,
        category="environment",
        data_source=ObservationDataSources.AMBEE,
        effective_at=effective_time,
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.POLLEN_TREE,
        value_integer=pollen.count.tree,
        category="environment",
        data_source=ObservationDataSources.AMBEE,
        effective_at=effective_time,
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.POLLEN_WEED,
        value_integer=pollen.count.weed,
        category="environment",
        data_source=ObservationDataSources.AMBEE,
        effective_at=effective_time,
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.POLLEN_TOTAL,
        value_integer=pollen.count.grass + pollen.count.tree + pollen.count.weed,
        category="environment",
        data_source=ObservationDataSources.AMBEE,
        effective_at=effective_time,
    )

    # Save weather data (7 observations)
    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.TEMPERATURE,
        value_decimal=weather.current.temperature,
        unit="celsius",
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.HUMIDITY,
        value_integer=weather.current.humidity,
        unit="percent",
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.AIR_PRESSURE,
        value_integer=weather.current.atmosphericPressure,
        unit="hPa",
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.WIND_SPEED,
        value_decimal=weather.current.windStrength,
        unit="m/s",
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.WIND_DIRECTION,
        value_integer=weather.current.windDirection,
        unit="degrees",
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.SUNRISE,
        value_string=weather.current.sunrise.isoformat(),
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.SUNSET,
        value_string=weather.current.sunset.isoformat(),
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
    )


@router.get("/data")
async def get_environment_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get 7-day environment data with smart backfilling.

    Window: 5 days in the past + today + 2 days forecast = 7 days total

    This endpoint:
    1. Checks what environment data already exists for the past 5 days
    2. Fetches missing historical days from external APIs
    3. Fetches current day and 2-day forecast
    4. Stores all new data as observations
    5. Returns complete 7-day dataset grouped by date

    Smart backfilling: only fetches data for historical days that don't have observations.

    Returns:
        Dictionary with 7 days of environment data grouped by date
    """
    observation_repo = ObservationRepository(db)
    today = date.today()

    # Calculate the date range: 5 days back + today = 6 historical days
    start_date = today - timedelta(days=5)
    historical_dates = [start_date + timedelta(days=i) for i in range(6)]  # 6 days including today

    # Check which historical days already have environment data
    existing_observations, _ = observation_repo.get_by_user_paginated(
        user_id=current_user.id,
        code=ObservationCodes.ENVIRONMENT,
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(today, datetime.max.time()),
        page=1,
        page_size=1000,
    )

    # Group existing observations by date
    existing_dates = set()
    for obs in existing_observations:
        obs_date = obs.effective_at.date()
        existing_dates.add(obs_date)

    # Determine which historical dates need data
    missing_historical_dates = [d for d in historical_dates if d not in existing_dates]

    saved_count = 0

    try:
        weather_service = _get_weather_service()
        air_quality_service = _get_air_quality_service()

        # Step 1: Backfill missing historical dates
        for missing_date in missing_historical_dates:
            # Use noon of the missing date as effective time
            effective_time = datetime.combine(
                missing_date, datetime.min.time().replace(hour=12)
            ).replace(tzinfo=timezone.utc)

            # Fetch current data (APIs only provide current, not historical)
            weather = await weather_service.get_weather(lat, lon)
            air_quality = await air_quality_service.get_air_quality(lat, lon)
            pollen = await air_quality_service.get_pollen(lat, lon)

            # Save with the historical date's timestamp
            _save_environment_observations(
                observation_repo,
                current_user.id,
                weather,
                air_quality,
                pollen,
                effective_time,
            )
            saved_count += 13  # 13 observations per day

        # Step 2: Always fetch and save today's data + 2-day forecast
        current_time = datetime.now(timezone.utc)
        weather = await weather_service.get_weather(lat, lon)
        air_quality = await air_quality_service.get_air_quality(lat, lon)
        pollen = await air_quality_service.get_pollen(lat, lon)

        # Save today's data
        if today not in existing_dates:
            _save_environment_observations(
                observation_repo,
                current_user.id,
                weather,
                air_quality,
                pollen,
                current_time,
            )
            saved_count += 13

        # Save 2-day forecast (from weather forecast data)
        # Forecast entries come from weather.forecast (next 2 days at noon)
        for i in range(1, 3):  # Day +1 and Day +2
            forecast_date = today + timedelta(days=i)
            forecast_time = datetime.combine(
                forecast_date, datetime.min.time().replace(hour=12)
            ).replace(tzinfo=timezone.utc)

            # Check if forecast already exists for this date
            forecast_obs, _ = observation_repo.get_by_user_paginated(
                user_id=current_user.id,
                code=ObservationCodes.ENVIRONMENT,
                start_date=datetime.combine(forecast_date, datetime.min.time()),
                end_date=datetime.combine(forecast_date, datetime.max.time()),
                page=1,
                page_size=1,
            )

            if not forecast_obs:
                # Use current air quality/pollen for forecast (APIs don't provide future AQ/pollen)
                _save_environment_observations(
                    observation_repo,
                    current_user.id,
                    weather,  # Has forecast data
                    air_quality,  # Use current values
                    pollen,  # Use current values
                    forecast_time,
                )
                saved_count += 13

        db.commit()

        # Step 3: Fetch all 7 days of data to return
        all_start = start_date
        all_end = today + timedelta(days=2)

        all_observations, _ = observation_repo.get_by_user_paginated(
            user_id=current_user.id,
            code=ObservationCodes.ENVIRONMENT,
            start_date=datetime.combine(all_start, datetime.min.time()),
            end_date=datetime.combine(all_end, datetime.max.time()),
            page=1,
            page_size=1000,
        )

        # Group observations by date and variant
        data_by_date = defaultdict(dict)
        for obs in all_observations:
            obs_date = obs.effective_at.date().isoformat()
            variant = obs.variant

            # Extract value based on type
            if obs.value_decimal is not None:
                value = float(obs.value_decimal)
            elif obs.value_integer is not None:
                value = obs.value_integer
            elif obs.value_string is not None:
                value = obs.value_string
            else:
                value = None

            data_by_date[obs_date][variant] = {
                "value": value,
                "unit": obs.unit,
                "source": obs.data_source,
            }

        # Get location from weather response
        location_info = {
            "lat": lat,
            "lon": lon,
            "city": weather.location.city,
            "country": weather.location.country,
        }

        return {
            "location": location_info,
            "date_range": {
                "start": all_start.isoformat(),
                "end": all_end.isoformat(),
                "total_days": 7,
            },
            "backfilled_days": len(missing_historical_dates),
            "saved_observations": saved_count,
            "data": dict(data_by_date),
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
            detail={"error": f"Failed to fetch environment data: {str(e)}", "code": "internal_error"},
        )


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
