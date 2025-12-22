"""Air quality schemas"""
from pydantic import BaseModel


class AirQualityResponse(BaseModel):
    """Air quality index response"""
    airQualityIndex: int
    mainPollutant: str
