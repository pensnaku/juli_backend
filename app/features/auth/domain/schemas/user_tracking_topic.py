"""Pydantic schemas for user tracking topics"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserTrackingTopicBase(BaseModel):
    """Base schema for user tracking topics"""
    topic_code: str = Field(..., description="Code of the tracking topic (e.g., 'coffee-consumption')")
    topic_label: str = Field(..., description="Human-readable label (e.g., 'Coffee consumption')")


class UserTrackingTopicCreate(UserTrackingTopicBase):
    """Schema for creating a user tracking topic"""
    pass


class UserTrackingTopicUpdate(BaseModel):
    """Schema for updating a user tracking topic (all fields optional)"""
    topic_label: Optional[str] = None
    is_active: Optional[bool] = None


class UserTrackingTopicResponse(UserTrackingTopicBase):
    """Schema for user tracking topic response"""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True