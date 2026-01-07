"""Pydantic schemas for tracking data with observations"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field


class TrackingObservation(BaseModel):
    """Observation item for tracking data"""
    id: UUID
    code: str
    variant: Optional[str] = None
    value_integer: Optional[int] = None
    value_decimal: Optional[Decimal] = None
    value_string: Optional[str] = None
    value_boolean: Optional[bool] = None
    effective_at: datetime
    unit: Optional[str] = None
    data_source: Optional[str] = None

    class Config:
        from_attributes = True


class IndividualTrackingTopicData(BaseModel):
    """Response schema for a single tracking topic with its observations"""
    topic_code: str = Field(..., description="Topic code (e.g., 'coffee-consumption')")
    topic_label: str = Field(..., description="Display label for the topic")
    question: Optional[str] = Field(None, description="Question text for this topic")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    emoji: Optional[str] = Field(None, description="Emoji icon for the topic")
    data_type: Optional[str] = Field(None, description="Data type (number, boolean, string)")
    min_value: Optional[int] = Field(None, description="Minimum value for number type")
    max_value: Optional[int] = Field(None, description="Maximum value for number type")
    observations: List[TrackingObservation] = Field(default_factory=list, description="Observations for this topic")


class IndividualTrackingDataResponse(BaseModel):
    """Response schema for individual tracking topics with observations"""
    topics: List[IndividualTrackingTopicData]
    count: int = Field(..., description="Total number of observations across all topics")
