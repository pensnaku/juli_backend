"""API router for environment feature - weather, air quality, pollen"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone, date, timedelta

from app.core.config import settings
from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.domain.entities import User
from app.features.environment.service import WeatherService, AirQualityService
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


def _save_weather_observations(
    repo: ObservationRepository,
    user_id: int,
    weather_data,
    effective_time: datetime,
):
    """Save weather observations for a specific datetime (7 observations with icon/status/description)"""
    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.TEMPERATURE,
        value_decimal=weather_data.temperature,
        unit="celsius",
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
        icon=weather_data.icon,
        status=weather_data.status.lower(),
        description=weather_data.description.lower(),
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.HUMIDITY,
        value_integer=weather_data.humidity,
        unit="percent",
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
        icon=weather_data.icon,
        status=weather_data.status.lower(),
        description=weather_data.description.lower(),
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.AIR_PRESSURE,
        value_integer=weather_data.atmosphericPressure,
        unit="hPa",
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
        icon=weather_data.icon,
        status=weather_data.status.lower(),
        description=weather_data.description.lower(),
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.WIND_SPEED,
        value_decimal=weather_data.windStrength,
        unit="m/s",
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
        icon=weather_data.icon,
        status=weather_data.status.lower(),
        description=weather_data.description.lower(),
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.WIND_DIRECTION,
        value_integer=weather_data.windDirection,
        unit="degrees",
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
        icon=weather_data.icon,
        status=weather_data.status.lower(),
        description=weather_data.description.lower(),
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.SUNRISE,
        value_string=weather_data.sunrise.isoformat(),
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
        icon=weather_data.icon,
        status=weather_data.status.lower(),
        description=weather_data.description.lower(),
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.SUNSET,
        value_string=weather_data.sunset.isoformat(),
        category="environment",
        data_source=ObservationDataSources.OPENWEATHERMAP,
        effective_at=effective_time,
        icon=weather_data.icon,
        status=weather_data.status.lower(),
        description=weather_data.description.lower(),
    )


def _save_air_quality_with_averaging(
    repo: ObservationRepository,
    user_id: int,
    air_quality,
    today: date,
    effective_time: datetime,
):
    """
    Save air quality, averaging with existing if present (matches old backend behavior).
    Main pollutant is always updated to latest.
    """
    existing_aqi = repo.get_latest_by_code(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.AIR_QUALITY_INDEX,
    )

    if existing_aqi and existing_aqi.effective_at.date() == today:
        new_value = round((existing_aqi.value_integer + air_quality.airQualityIndex) / 2)
        existing_aqi.value_integer = new_value
        repo.update(existing_aqi)
    else:
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


def _save_pollen_once_per_day(
    repo: ObservationRepository,
    user_id: int,
    pollen,
    today: date,
    effective_time: datetime,
):
    """
    Save pollen only if not already saved today (matches old backend behavior).
    """
    if not pollen:
        return

    existing_pollen = repo.get_latest_by_code(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.POLLEN_GRASS,
    )

    if existing_pollen and existing_pollen.effective_at.date() == today:
        return

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

    pollen_total = pollen.count.grass + pollen.count.tree + pollen.count.weed
    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.POLLEN_TOTAL,
        value_integer=pollen_total,
        category="environment",
        data_source=ObservationDataSources.AMBEE,
        effective_at=effective_time,
    )

    # Save pollen risk values
    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.POLLEN_RISK_GRASS,
        value_string=pollen.risk.grass,
        category="environment",
        data_source=ObservationDataSources.AMBEE,
        effective_at=effective_time,
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.POLLEN_RISK_TREE,
        value_string=pollen.risk.tree,
        category="environment",
        data_source=ObservationDataSources.AMBEE,
        effective_at=effective_time,
    )

    repo.create(
        user_id=user_id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.POLLEN_RISK_WEED,
        value_string=pollen.risk.weed,
        category="environment",
        data_source=ObservationDataSources.AMBEE,
        effective_at=effective_time,
    )


@router.post("/sync")
async def sync_environment_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sync environment data (weather, air quality, pollen) for the user.

    Call this when the app opens. This is a trigger endpoint that:
    1. If today's weather data exists → does nothing (returns immediately)
    2. If today's data is missing → fetches from APIs and stores as observations
    3. Backfills last 5 days of weather if missing (separate historical API call per day)

    Note: Air quality and pollen are only available for today (no historical API).
    Air quality is averaged if called multiple times per day.
    Pollen is only saved once per day.

    Data is stored as observations and should be retrieved via the observations API.

    Returns:
        Status indicating whether data was synced or already existed
    """
    observation_repo = ObservationRepository(db)
    today = date.today()
    start_date = today - timedelta(days=5)

    today_weather, _ = observation_repo.get_by_user_paginated(
        user_id=current_user.id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.TEMPERATURE,
        start_date=datetime.combine(today, datetime.min.time()),
        end_date=datetime.combine(today, datetime.max.time()),
        page=1,
        page_size=1,
    )

    if today_weather:
        return {
            "status": "ok",
            "synced": False,
            "message": "Environment data already exists for today",
        }

    existing_weather, _ = observation_repo.get_by_user_paginated(
        user_id=current_user.id,
        code=ObservationCodes.ENVIRONMENT,
        variant=EnvironmentVariants.TEMPERATURE,
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(today, datetime.max.time()),
        page=1,
        page_size=100,
    )

    existing_dates = set()
    for obs in existing_weather:
        existing_dates.add(obs.effective_at.date())

    all_dates = [start_date + timedelta(days=i) for i in range(6)]
    missing_dates = [d for d in all_dates if d not in existing_dates]

    if not missing_dates:
        return {
            "status": "ok",
            "synced": False,
            "message": "All environment data already exists for the past 6 days",
        }

    try:
        weather_service = _get_weather_service()
        air_quality_service = _get_air_quality_service()

        days_synced = 0

        if today in missing_dates:
            effective_time = datetime.now(timezone.utc)

            weather = await weather_service.get_weather(lat, lon)

            # Save current weather
            _save_weather_observations(
                observation_repo,
                current_user.id,
                weather.current,
                weather.current.datetime,
            )

            # Save all forecast data (12 entries, 3-hourly)
            for forecast in weather.forecast:
                _save_weather_observations(
                    observation_repo,
                    current_user.id,
                    forecast,
                    forecast.datetime,
                )

            air_quality = await air_quality_service.get_air_quality(lat, lon)
            _save_air_quality_with_averaging(observation_repo, current_user.id, air_quality, today, effective_time)

            pollen = None
            try:
                pollen = await air_quality_service.get_pollen(lat, lon)
            except AirQualityException:
                pass
            _save_pollen_once_per_day(observation_repo, current_user.id, pollen, today, effective_time)

            days_synced += 1

        for missing_date in missing_dates:
            if missing_date == today:
                continue

            effective_time = datetime.combine(
                missing_date, datetime.min.time().replace(hour=12)
            ).replace(tzinfo=timezone.utc)

            try:
                historical_weather = await weather_service.get_historical_weather(lat, lon, effective_time)

                # Save current weather with datetime from the response
                _save_weather_observations(
                    observation_repo,
                    current_user.id,
                    historical_weather.current,
                    historical_weather.current.datetime,
                )

                # Save all hourly weather data
                for hourly in historical_weather.hourly:
                    _save_weather_observations(
                        observation_repo,
                        current_user.id,
                        hourly,
                        hourly.datetime,
                    )

                days_synced += 1
            except WeatherException:
                pass

        db.commit()

        return {
            "status": "ok",
            "synced": True,
            "days_synced": days_synced,
            "message": f"Synced environment data for {days_synced} day(s)",
        }

    except (WeatherException, AirQualityException) as e:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail={"error": f"Cannot fetch data from external API: {str(e)}", "code": "external_api_error"},
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error": f"Failed to sync environment data: {str(e)}", "code": "internal_error"},
        )
