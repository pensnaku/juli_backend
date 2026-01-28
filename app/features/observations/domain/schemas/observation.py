"""Pydantic schemas for observations"""
from typing import Optional, List, Union, Dict
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


class ObservationBase(BaseModel):
    """Base schema for observations"""
    code: str = Field(..., max_length=100, description="Observation type code (e.g., 'sleep', 'mood', 'heart-rate')")
    variant: Optional[str] = Field(None, max_length=100, description="Observation variant (e.g., 'deep', 'running')")

    value_integer: Optional[int] = Field(None, description="Integer value")
    value_decimal: Optional[Decimal] = Field(None, description="Decimal value")
    value_string: Optional[str] = Field(None, max_length=500, description="String value")
    value_boolean: Optional[bool] = Field(None, description="Boolean value")

    effective_at: datetime = Field(..., description="When the observation occurred")
    period_start: Optional[datetime] = Field(None, description="Start of observation period")
    period_end: Optional[datetime] = Field(None, description="End of observation period")

    category: Optional[str] = Field(None, max_length=50, description="Category (e.g., 'vital-signs', 'activity')")
    data_source: Optional[str] = Field(None, max_length=50, description="Data source (e.g., 'manual', 'apple-health')")
    unit: Optional[str] = Field(None, max_length=20, description="Unit of measurement")
    source_id: Optional[str] = Field(None, max_length=255, description="External source ID for deduplication")

    @model_validator(mode='after')
    def check_at_least_one_value(self):
        """Ensure at least one value field is populated"""
        if (self.value_integer is None and
            self.value_decimal is None and
            self.value_string is None and
            self.value_boolean is None):
            raise ValueError("At least one value field must be provided")
        return self


class ObservationCreate(ObservationBase):
    """Schema for creating an observation"""
    pass


class ObservationBulkCreate(BaseModel):
    """Schema for bulk creating observations"""
    observations: List[ObservationCreate] = Field(..., min_length=1, max_length=500)


class ObservationUpdate(BaseModel):
    """Schema for updating an observation"""
    value_integer: Optional[int] = None
    value_decimal: Optional[Decimal] = None
    value_string: Optional[str] = Field(None, max_length=500)
    value_boolean: Optional[bool] = None

    effective_at: Optional[datetime] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    category: Optional[str] = Field(None, max_length=50)
    data_source: Optional[str] = Field(None, max_length=50)
    unit: Optional[str] = Field(None, max_length=20)


class ObservationResponse(BaseModel):
    """Schema for observation response"""
    id: UUID
    code: str
    variant: Optional[str] = None

    value_integer: Optional[int] = None
    value_decimal: Optional[Decimal] = None
    value_string: Optional[str] = None
    value_boolean: Optional[bool] = None

    effective_at: datetime
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    category: Optional[str] = None
    data_source: Optional[str] = None
    unit: Optional[str] = None
    source_id: Optional[str] = None

    # Weather-specific fields
    icon: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None

    created_at: datetime

    class Config:
        from_attributes = True


class ObservationListResponse(BaseModel):
    """Schema for paginated observations list"""
    observations: List[ObservationResponse]
    total: int
    page: int
    page_size: int


# ========== Optimized Query Schemas ==========

class ObservationQueryRequest(BaseModel):
    """Request schema for querying observations by multiple codes and date range"""
    codes: List[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of observation codes to query"
    )
    start_date: datetime = Field(..., description="Start of date range (inclusive)")
    end_date: datetime = Field(..., description="End of date range (inclusive)")
    variants: Optional[List[str]] = Field(
        None,
        description="Optional list of variants to filter by"
    )
    data_sources: Optional[List[str]] = Field(
        None,
        description="Optional list of data sources to filter by"
    )
    group_by_code: bool = Field(
        False,
        description="If true, results are grouped by code in a dictionary"
    )
    limit_per_code: Optional[int] = Field(
        None,
        ge=1,
        le=100,
        description="Optional limit of results per code (max 100)"
    )


class ObservationQueryItem(BaseModel):
    """Minimal observation item for query responses (optimized for performance)"""
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

    # Weather-specific fields
    icon: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class ObservationQueryResponse(BaseModel):
    """Response schema for observation query - flat list"""
    observations: List[ObservationQueryItem]
    count: int


class ObservationQueryGroupedResponse(BaseModel):
    """Response schema for observation query - grouped by code"""
    observations: Dict[str, List[ObservationQueryItem]]
    count: int
