"""Pydantic schemas for Juli Score"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field


class FactorBreakdown(BaseModel):
    """Breakdown of a single factor's contribution to the score"""
    name: str = Field(..., description="Factor name (e.g., 'air_quality', 'sleep')")
    input_value: Optional[Decimal] = Field(None, description="Raw observation value")
    score: Optional[Decimal] = Field(None, description="Calculated score contribution")
    weight: int = Field(..., description="Factor weight")
    available: bool = Field(True, description="Whether data was available for this factor")


class JuliScoreResponse(BaseModel):
    """Response schema for a single Juli Score"""
    id: UUID
    condition_code: str = Field(..., description="SNOMED-CT condition code")
    condition_name: str = Field(..., description="Human-readable condition name")
    score: int = Field(..., ge=0, le=100, description="Final score (0-100)")
    effective_at: datetime = Field(..., description="When the score was calculated for")
    factors: List[FactorBreakdown] = Field(default_factory=list, description="Factor breakdown")
    data_points_used: int = Field(..., description="Number of data points used")
    total_weight: int = Field(..., description="Sum of all factor weights")
    created_at: datetime

    class Config:
        from_attributes = True


class JuliScoreListResponse(BaseModel):
    """Paginated list of Juli Scores"""
    scores: List[JuliScoreResponse]
    total: int
    page: int
    page_size: int


class JuliScoreLatestResponse(BaseModel):
    """Response with latest scores for all user conditions"""
    scores: List[JuliScoreResponse]
    conditions_without_score: List[str] = Field(
        default_factory=list,
        description="Condition codes without calculated scores"
    )
