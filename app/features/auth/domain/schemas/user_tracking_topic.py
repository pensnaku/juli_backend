"""Pydantic schemas for user tracking topics"""
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class UserTrackingTopicBase(BaseModel):
    """Base schema for user tracking topics"""
    topic_code: str = Field(..., description="Code of the tracking topic (e.g., 'coffee-consumption')")
    topic_label: str = Field(..., description="Human-readable label (e.g., 'Coffee consumption')")


class UserTrackingTopicCreate(BaseModel):
    """Schema for creating/activating a tracking topic (default or custom)"""
    topic_code: Optional[str] = Field(None, description="Code of the tracking topic (auto-generated for custom topics if not provided)")
    label: Optional[str] = Field(None, description="Human-readable label (required for custom topics)")
    question: Optional[str] = Field(None, description="Question to ask users (required for custom topics)")
    data_type: Optional[Literal["number", "boolean"]] = Field(None, description="Type of data (required for custom topics)")
    unit: Optional[str] = Field(None, description="Unit of measurement (optional, for number types)")
    emoji: Optional[str] = Field(None, description="Visual indicator emoji (optional)")
    min: Optional[int] = Field(None, description="Minimum value (optional, for number types)")
    max: Optional[int] = Field(None, description="Maximum value (optional, for number types)")

    @model_validator(mode="after")
    def validate_min_max(self):
        """Validate min/max only apply to number types and min <= max"""
        if self.data_type == "boolean":
            if self.min is not None or self.max is not None:
                raise ValueError("min and max are not applicable for boolean data types")
        if self.min is not None and self.max is not None:
            if self.min > self.max:
                raise ValueError("min cannot be greater than max")
        return self


class UserTrackingTopicUpdate(BaseModel):
    """Schema for updating a user tracking topic (all fields optional)"""
    topic_label: Optional[str] = None
    is_active: Optional[bool] = None


class TrackingTopicUpdate(BaseModel):
    """Schema for updating a tracking topic"""
    label: Optional[str] = Field(None, description="Human-readable label")
    question: Optional[str] = Field(None, description="Question to ask users")
    data_type: Optional[Literal["number", "boolean"]] = Field(None, description="Type of data")
    unit: Optional[str] = Field(None, description="Unit of measurement (for number types)")
    emoji: Optional[str] = Field(None, description="Visual indicator emoji")
    min: Optional[int] = Field(None, description="Minimum value (for number types)")
    max: Optional[int] = Field(None, description="Maximum value (for number types)")
    is_active: Optional[bool] = Field(None, description="Whether topic is active")


class UserTrackingTopicResponse(UserTrackingTopicBase):
    """Schema for user tracking topic response"""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrackingTopicResponse(BaseModel):
    """Schema for tracking topic with full metadata and activation status"""
    topic_code: str = Field(..., description="Code of the tracking topic")
    label: str = Field(..., description="Human-readable label")
    question: str = Field(..., description="Question to ask users")
    data_type: str = Field(..., description="Type of data (number, boolean)")
    unit: Optional[str] = Field(None, description="Unit of measurement (for number types)")
    emoji: Optional[str] = Field(None, description="Visual indicator emoji")
    min: Optional[int] = Field(None, description="Minimum value (for number types)")
    max: Optional[int] = Field(None, description="Maximum value (for number types)")
    is_active: bool = Field(..., description="Whether user has activated this topic")
    is_default: bool = Field(..., description="Whether this is a system default topic")


class TrackingTopicListResponse(BaseModel):
    """Schema for list of tracking topics"""
    topics: List[TrackingTopicResponse]