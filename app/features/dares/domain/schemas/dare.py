"""Pydantic schemas for dares"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DareBase(BaseModel):
    """Base schema for dares"""
    text: str = Field(..., description="The dare/challenge text")
    category: str = Field(..., description="Category: Activity, Nutrition, Sleep, Wellness")
    subcategory: Optional[str] = Field(None, description="Subcategory for Nutrition dares")
    points: int = Field(..., ge=1, le=5, description="Points awarded (1-5)")
    condition: Optional[str] = Field(None, description="Only show to users with this condition")


class DareCreate(DareBase):
    """Schema for creating a dare"""
    pass


class DareResponse(DareBase):
    """Schema for dare response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True