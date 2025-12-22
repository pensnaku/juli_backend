"""Pollen schemas"""
from pydantic import BaseModel
from typing import Dict, Optional


class PollenRisk(BaseModel):
    """Risk levels by pollen type"""
    grass: str
    tree: str
    weed: str


class PollenCount(BaseModel):
    """Pollen counts by type"""
    grass: int
    tree: int
    weed: int


class SpeciesData(BaseModel):
    """Data for a specific pollen species"""
    count: int
    risk: Optional[str] = None


class PollenResponse(BaseModel):
    """Pollen response with risk, count, and species breakdown"""
    risk: PollenRisk
    count: PollenCount
    species: Dict[str, Dict[str, SpeciesData]]
