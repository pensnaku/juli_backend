"""Weather schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import List


class WeatherData(BaseModel):
    """Weather data for a point in time"""
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
    """Location information"""
    city: str
    country: str


class WeatherResponse(BaseModel):
    """Weather response with current conditions and forecast"""
    current: WeatherData
    forecast: List[WeatherData]
    location: Location


class HistoricalWeatherResponse(BaseModel):
    """Historical weather response with current conditions and hourly data"""
    current: WeatherData
    hourly: List[WeatherData]
