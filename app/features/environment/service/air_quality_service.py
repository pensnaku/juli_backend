"""Air quality and pollen service using Ambee API"""
import logging
import httpx
from typing import Dict

from app.features.environment.domain.schemas import (
    AirQualityResponse,
    PollenRisk,
    PollenCount,
    SpeciesData,
    PollenResponse,
)
from app.features.environment.exceptions import AirQualityException

logger = logging.getLogger(__name__)

AMBEE_BASE_URL = "https://api.ambeedata.com"


class AirQualityService:
    """Service for fetching air quality and pollen data from Ambee"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_air_quality(self, lat: float, lon: float) -> AirQualityResponse:
        """
        Get air quality index for a location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            AirQualityResponse with AQI and main pollutant

        Raises:
            AirQualityException: If API call fails
        """
        url = f"{AMBEE_BASE_URL}/latest/by-lat-lng"
        params = {"lat": lat, "lng": lon}
        headers = {"x-api-key": self.api_key}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
            except httpx.HTTPError as e:
                logger.error(f"Ambee air quality API error: {e}")
                raise AirQualityException(f"Failed to fetch air quality data: {e}")

        if response.status_code != 200:
            logger.error(f"Ambee air quality error: {response.text}")
            raise AirQualityException(
                f"Ambee API error: {response.status_code}",
                status=response.status_code,
            )

        data = response.json()
        stations = data.get("stations", [])

        if not stations:
            raise AirQualityException("No air quality data available for this location")

        # Use the first station's data
        station = stations[0]

        return AirQualityResponse(
            airQualityIndex=station.get("AQI", 0),
            mainPollutant=station.get("aqiInfo", {}).get("pollutant", "pm25"),
        )

    async def get_pollen(self, lat: float, lon: float) -> PollenResponse:
        """
        Get pollen levels and risk for a location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            PollenResponse with risk, count, and species breakdown

        Raises:
            AirQualityException: If API call fails
        """
        url = f"{AMBEE_BASE_URL}/latest/pollen/by-lat-lng"
        params = {"lat": lat, "lng": lon, "speciesRisk": "true"}
        headers = {"x-api-key": self.api_key}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
            except httpx.HTTPError as e:
                logger.error(f"Ambee pollen API error: {e}")
                raise AirQualityException(f"Failed to fetch pollen data: {e}")

        if response.status_code != 200:
            logger.error(f"Ambee pollen error: {response.text}")
            raise AirQualityException(
                f"Ambee API error: {response.status_code}",
                status=response.status_code,
            )

        data = response.json()
        pollen_data = data.get("data", [])

        if not pollen_data:
            raise AirQualityException("No pollen data available for this location")

        # Use the first data entry
        entry = pollen_data[0]
        count_data = entry.get("Count", {})
        risk_data = entry.get("Risk", {})
        species_data = entry.get("Species", {})

        return PollenResponse(
            risk=PollenRisk(
                grass=risk_data.get("grass_pollen", "Low"),
                tree=risk_data.get("tree_pollen", "Low"),
                weed=risk_data.get("weed_pollen", "Low"),
            ),
            count=PollenCount(
                grass=count_data.get("grass_pollen", 0),
                tree=count_data.get("tree_pollen", 0),
                weed=count_data.get("weed_pollen", 0),
            ),
            species=self._parse_species(species_data),
        )

    def _parse_species(self, species_data: dict) -> Dict[str, Dict[str, SpeciesData]]:
        """Parse species data from Ambee response"""
        result = {}

        for category, species_list in species_data.items():
            result[category] = {}
            if isinstance(species_list, dict):
                for species_name, species_info in species_list.items():
                    if isinstance(species_info, dict):
                        result[category][species_name] = SpeciesData(
                            count=species_info.get("count", 0),
                            risk=species_info.get("risk"),
                        )

        return result
