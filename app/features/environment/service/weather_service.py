"""Weather service using OpenWeatherMap API"""
import logging
import httpx
from datetime import datetime, timezone
from typing import List

from app.features.environment.domain.schemas import (
    WeatherData,
    Location,
    WeatherResponse,
    HistoricalWeatherResponse,
)
from app.features.environment.exceptions import WeatherException

logger = logging.getLogger(__name__)

OPENWEATHERMAP_BASE_URL = "https://api.openweathermap.org/data/2.5"


class WeatherService:
    """Service for fetching weather data from OpenWeatherMap"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_weather(self, lat: float, lon: float) -> WeatherResponse:
        """
        Get current weather and forecast for a location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            WeatherResponse with current conditions and forecast

        Raises:
            WeatherException: If API call fails
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch current weather and forecast in parallel
            current_task = self._fetch_current(client, lat, lon)
            forecast_task = self._fetch_forecast(client, lat, lon)

            try:
                current_data = await current_task
                forecast_data = await forecast_task
            except httpx.HTTPError as e:
                logger.error(f"Weather API error: {e}")
                raise WeatherException(f"Failed to fetch weather data: {e}")

        return WeatherResponse(
            current=current_data["weather"],
            forecast=forecast_data["forecast"],
            location=current_data["location"],
        )

    async def _fetch_current(
        self, client: httpx.AsyncClient, lat: float, lon: float
    ) -> dict:
        """Fetch current weather from OpenWeatherMap"""
        url = f"{OPENWEATHERMAP_BASE_URL}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
        }

        response = await client.get(url, params=params)

        if response.status_code != 200:
            logger.error(f"OpenWeatherMap current weather error: {response.text}")
            raise WeatherException(
                f"OpenWeatherMap API error: {response.status_code}",
                status=response.status_code,
            )

        data = response.json()
        return {
            "weather": self._parse_weather_data(data),
            "location": Location(
                city=data.get("name", "Unknown"),
                country=data.get("sys", {}).get("country", ""),
            ),
        }

    async def _fetch_forecast(
        self, client: httpx.AsyncClient, lat: float, lon: float
    ) -> dict:
        """Fetch forecast from OpenWeatherMap"""
        url = f"{OPENWEATHERMAP_BASE_URL}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "cnt": 12,  # Limit to 12 forecast entries
        }

        response = await client.get(url, params=params)

        if response.status_code != 200:
            logger.error(f"OpenWeatherMap forecast error: {response.text}")
            raise WeatherException(
                f"OpenWeatherMap API error: {response.status_code}",
                status=response.status_code,
            )

        data = response.json()
        forecast_list = data.get("list", [])

        # Get sunrise/sunset from city data if available
        city_data = data.get("city", {})
        default_sunrise = city_data.get("sunrise")
        default_sunset = city_data.get("sunset")

        forecast = [
            self._parse_forecast_item(item, default_sunrise, default_sunset)
            for item in forecast_list
        ]

        return {"forecast": forecast}

    def _parse_weather_data(self, data: dict) -> WeatherData:
        """Parse OpenWeatherMap current weather response"""
        weather = data.get("weather", [{}])[0]
        main = data.get("main", {})
        wind = data.get("wind", {})
        sys = data.get("sys", {})

        return WeatherData(
            datetime=datetime.fromtimestamp(data.get("dt", 0), tz=timezone.utc),
            status=weather.get("main", "Unknown"),
            description=weather.get("description", ""),
            icon=weather.get("icon", ""),
            temperature=main.get("temp", 0),
            atmosphericPressure=main.get("pressure", 0),
            humidity=main.get("humidity", 0),
            windStrength=wind.get("speed", 0),
            windDirection=wind.get("deg", 0),
            sunrise=datetime.fromtimestamp(sys.get("sunrise", 0), tz=timezone.utc),
            sunset=datetime.fromtimestamp(sys.get("sunset", 0), tz=timezone.utc),
        )

    async def get_historical_weather(self, lat: float, lon: float, date: datetime) -> HistoricalWeatherResponse:
        """
        Fetch historical weather for a specific date using One Call Time Machine API.

        Args:
            lat: Latitude
            lon: Longitude
            date: The datetime to fetch historical weather for

        Returns:
            HistoricalWeatherResponse with current conditions and hourly data

        Raises:
            WeatherException: If API call fails
        """
        unix_timestamp = int(date.timestamp())
        url = f"{OPENWEATHERMAP_BASE_URL}/onecall/timemachine"
        params = {
            "lat": lat,
            "lon": lon,
            "dt": unix_timestamp,
            "appid": self.api_key,
            "units": "metric",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
            except httpx.HTTPError as e:
                logger.error(f"Historical weather API error: {e}")
                raise WeatherException(f"Failed to fetch historical weather data: {e}")

        if response.status_code != 200:
            logger.error(f"OpenWeatherMap historical weather error: {response.text}")
            raise WeatherException(
                f"OpenWeatherMap historical API error: {response.status_code}",
                status=response.status_code,
            )

        data = response.json()

        # Historical API uses different structure: data["current"] instead of data["main"]
        # Access fields directly - will raise KeyError if data is incomplete
        current = data["current"]
        weather_info = current["weather"][0]

        current_weather = WeatherData(
            datetime=datetime.fromtimestamp(current["dt"], tz=timezone.utc),
            status=weather_info["main"],
            description=weather_info["description"],
            icon=weather_info["icon"],
            temperature=current["temp"],
            atmosphericPressure=current["pressure"],
            humidity=current["humidity"],
            windStrength=current["wind_speed"],
            windDirection=current["wind_deg"],
            sunrise=datetime.fromtimestamp(current["sunrise"], tz=timezone.utc),
            sunset=datetime.fromtimestamp(current["sunset"], tz=timezone.utc),
        )

        hourly_data = data["hourly"]
        hourly_weather = [
            WeatherData(
                datetime=datetime.fromtimestamp(hourly["dt"], tz=timezone.utc),
                status=hourly["weather"][0]["main"],
                description=hourly["weather"][0]["description"],
                icon=hourly["weather"][0]["icon"],
                temperature=hourly["temp"],
                atmosphericPressure=hourly["pressure"],
                humidity=hourly["humidity"],
                windStrength=hourly["wind_speed"],
                windDirection=hourly["wind_deg"],
                sunrise=datetime.fromtimestamp(current["sunrise"], tz=timezone.utc),
                sunset=datetime.fromtimestamp(current["sunset"], tz=timezone.utc),
            )
            for hourly in hourly_data
        ]

        return HistoricalWeatherResponse(
            current=current_weather,
            hourly=hourly_weather,
        )

    def _parse_forecast_item(
        self, item: dict, default_sunrise: int = None, default_sunset: int = None
    ) -> WeatherData:
        """Parse OpenWeatherMap forecast item"""
        weather = item.get("weather", [{}])[0]
        main = item.get("main", {})
        wind = item.get("wind", {})

        # Forecast doesn't include sunrise/sunset per item, use defaults
        sunrise = default_sunrise or 0
        sunset = default_sunset or 0

        return WeatherData(
            datetime=datetime.fromtimestamp(item.get("dt", 0), tz=timezone.utc),
            status=weather.get("main", "Unknown"),
            description=weather.get("description", ""),
            icon=weather.get("icon", ""),
            temperature=main.get("temp", 0),
            atmosphericPressure=main.get("pressure", 0),
            humidity=main.get("humidity", 0),
            windStrength=wind.get("speed", 0),
            windDirection=wind.get("deg", 0),
            sunrise=datetime.fromtimestamp(sunrise, tz=timezone.utc),
            sunset=datetime.fromtimestamp(sunset, tz=timezone.utc),
        )
