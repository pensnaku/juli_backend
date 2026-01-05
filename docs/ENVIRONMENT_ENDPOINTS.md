# Environment Endpoints Documentation

This document describes the weather, air quality, and pollen endpoints to be implemented.

---

## Endpoints Overview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/weather/$location` | GET | Get current weather and forecast |
| `/air-quality/$location` | GET | Get air quality index |
| `/air-quality/pollen/$location` | GET | Get pollen levels and risk |

---

## 1. GET /weather/$location

Get current weather and forecast for a location.

### Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `lat` | float | Yes | Latitude |
| `lon` | float | Yes | Longitude |

### External API

- **Provider:** OpenWeatherMap
- **Base URL:** `https://api.openweathermap.org/data/2.5`
- **Config Key:** `OPENWEATHERMAP_API_KEY`
- **Endpoints Used:**
  - `/weather` - Current weather
  - `/forecast` - Forecast data

### Response

```json
{
  "current": {
    "datetime": "2025-01-15T10:00:00Z",
    "status": "Clear",
    "description": "clear sky",
    "icon": "01d",
    "temperature": 22.5,
    "atmosphericPressure": 1013,
    "humidity": 65,
    "windStrength": 5.2,
    "windDirection": 180,
    "sunrise": "2025-01-15T06:30:00Z",
    "sunset": "2025-01-15T18:00:00Z"
  },
  "forecast": [
    {
      "datetime": "2025-01-15T13:00:00Z",
      "status": "Clouds",
      "description": "scattered clouds",
      "icon": "03d",
      "temperature": 24.0,
      "atmosphericPressure": 1012,
      "humidity": 60,
      "windStrength": 6.0,
      "windDirection": 190,
      "sunrise": "2025-01-15T06:30:00Z",
      "sunset": "2025-01-15T18:00:00Z"
    }
  ],
  "location": {
    "city": "Berlin",
    "country": "DE"
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `current` | object | Current weather conditions |
| `current.datetime` | string | ISO 8601 timestamp |
| `current.status` | string | Weather condition (Clear, Clouds, Rain, etc.) |
| `current.description` | string | Detailed description |
| `current.icon` | string | OpenWeatherMap icon code |
| `current.temperature` | float | Temperature in Celsius |
| `current.atmosphericPressure` | int | Pressure in hPa |
| `current.humidity` | int | Humidity percentage |
| `current.windStrength` | float | Wind speed in m/s |
| `current.windDirection` | int | Wind direction in degrees |
| `current.sunrise` | string | Sunrise time (ISO 8601) |
| `current.sunset` | string | Sunset time (ISO 8601) |
| `forecast` | array | Up to 12 forecast entries (same structure as current) |
| `location.city` | string | City name |
| `location.country` | string | Country code |

### Errors

| Status | Code | Description |
|--------|------|-------------|
| 422 | `bad_request` | Missing lat or lon |
| 422 | `external_api_error` | OpenWeatherMap API failure |

---

## 2. GET /air-quality/$location

Get current air quality index for a location.

### Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `lat` | float | Yes | Latitude |
| `lon` | float | Yes | Longitude |

### External API

- **Provider:** Ambee
- **Base URL:** `https://api.ambeedata.com`
- **Config Key:** `AMBEE_API_KEY`
- **Endpoint Used:** `/latest/by-lat-lng`
- **Auth Header:** `x-api-key`

### Response

```json
{
  "airQualityIndex": 42,
  "mainPollutant": "pm25"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `airQualityIndex` | int | AQI value (0-500) |
| `mainPollutant` | string | Primary pollutant (pm25, pm10, o3, no2, so2, co) |

### AQI Scale

| AQI Range | Level | Health Implications |
|-----------|-------|---------------------|
| 0-50 | Good | Satisfactory |
| 51-100 | Moderate | Acceptable |
| 101-150 | Unhealthy for Sensitive Groups | Risk for sensitive people |
| 151-200 | Unhealthy | Everyone may experience effects |
| 201-300 | Very Unhealthy | Health alert |
| 301-500 | Hazardous | Emergency conditions |

### Errors

| Status | Code | Description |
|--------|------|-------------|
| 422 | `bad_request` | Missing lat or lon |
| 422 | `external_api_error` | Ambee API failure |

---

## 3. GET /air-quality/pollen/$location

Get pollen levels and risk by type for a location.

### Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `lat` | float | Yes | Latitude |
| `lon` | float | Yes | Longitude |

### External API

- **Provider:** Ambee
- **Base URL:** `https://api.ambeedata.com`
- **Config Key:** `AMBEE_API_KEY`
- **Endpoint Used:** `/latest/pollen/by-lat-lng?speciesRisk=true`
- **Auth Header:** `x-api-key`

### Response

```json
{
  "risk": {
    "grass": "Low",
    "tree": "High",
    "weed": "Moderate"
  },
  "count": {
    "grass": 12,
    "tree": 150,
    "weed": 45
  },
  "species": {
    "Grass": {
      "Poaceae": { "count": 12, "risk": "Low" }
    },
    "Tree": {
      "Birch": { "count": 80, "risk": "High" },
      "Oak": { "count": 70, "risk": "Moderate" }
    },
    "Weed": {
      "Ragweed": { "count": 45, "risk": "Moderate" }
    },
    "Others": {
      "Others": { "count": 5, "risk": null }
    }
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `risk` | object | Risk levels by pollen type |
| `risk.grass` | string | Grass pollen risk (Low, Moderate, High, Very High) |
| `risk.tree` | string | Tree pollen risk |
| `risk.weed` | string | Weed pollen risk |
| `count` | object | Pollen counts by type |
| `count.grass` | int | Grass pollen count |
| `count.tree` | int | Tree pollen count |
| `count.weed` | int | Weed pollen count |
| `species` | object | Detailed breakdown by species |
| `species.{Category}.{Species}.count` | int | Species pollen count |
| `species.{Category}.{Species}.risk` | string | Species risk level |

### Risk Levels

| Level | Description |
|-------|-------------|
| Low | Minimal impact |
| Moderate | May affect sensitive individuals |
| High | Likely to affect allergy sufferers |
| Very High | Severe impact expected |

### Errors

| Status | Code | Description |
|--------|------|-------------|
| 422 | `bad_request` | Missing lat or lon |
| 422 | `external_api_error` | Ambee API failure |

---

## Implementation Notes

### Configuration Required

```python
# .env
OPENWEATHERMAP_API_KEY=your_key_here
AMBEE_API_KEY=your_key_here
```

### Suggested Project Structure

```
app/
  features/
    environment/
      __init__.py
      api/
        __init__.py
        router.py          # FastAPI routes
      service/
        __init__.py
        weather_service.py
        air_quality_service.py
      domain/
        __init__.py
        schemas/
          weather.py
          air_quality.py
          pollen.py
      exceptions.py
```

### Pydantic Schemas

```python
# weather.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class WeatherData(BaseModel):
    datetime: datetime
    status: str
    description: str
    icon: str
    temperature: float
    atmosphericPressure: int
    humidity: int
    windStrength: float
    windDirection: int
    sunrise: datetime
    sunset: datetime

class Location(BaseModel):
    city: str
    country: str

class WeatherResponse(BaseModel):
    current: WeatherData
    forecast: list[WeatherData]
    location: Location

# air_quality.py
class AirQualityResponse(BaseModel):
    airQualityIndex: int
    mainPollutant: str

# pollen.py
class PollenRisk(BaseModel):
    grass: str
    tree: str
    weed: str

class PollenCount(BaseModel):
    grass: int
    tree: int
    weed: int

class SpeciesData(BaseModel):
    count: int
    risk: Optional[str]

class PollenResponse(BaseModel):
    risk: PollenRisk
    count: PollenCount
    species: dict[str, dict[str, SpeciesData]]
```

### Error Handling

```python
from fastapi import HTTPException

class WeatherException(Exception):
    pass

class AirQualityException(Exception):
    pass

class AmbeeException(AirQualityException):
    def __init__(self, message: str, status: int = None, operation_code: str = None):
        self.message = message
        self.status = status
        self.operation_code = operation_code
        super().__init__(self.message)

# In router
@router.get("/weather/$location")
async def get_weather(lat: float, lon: float):
    if not lat or not lon:
        raise HTTPException(status_code=422, detail={
            "error": "Coordinates are required",
            "code": "bad_request"
        })
    try:
        return await weather_service.get_weather(lat, lon)
    except WeatherException:
        raise HTTPException(status_code=422, detail={
            "error": "Cannot fetch data from external API",
            "code": "external_api_error"
        })
```

---

## History Recording (Optional)

If you need to save environment data as observations for a patient:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/weather/$update-history-records` | POST | Save weather to patient observations |
| `/air-quality/$update-history-records` | POST | Save AQI as observation |
| `/air-quality/pollen/$update-history-records` | POST | Save pollen as observation |

### Observation Codes

| Code | Variant | Description |
|------|---------|-------------|
| `air-quality` | NULL | Air quality index |
| `pollen` | `tree-risk` | Tree pollen risk level |
| `pollen` | `tree-count` | Tree pollen count |
| `pollen` | `grass-risk` | Grass pollen risk level |
| `pollen` | `grass-count` | Grass pollen count |
| `pollen` | `weed-risk` | Weed pollen risk level |
| `pollen` | `weed-count` | Weed pollen count |
