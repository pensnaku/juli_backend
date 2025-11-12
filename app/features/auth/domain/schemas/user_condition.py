"""UserCondition Pydantic schemas"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserConditionBase(BaseModel):
    """Base schema for user conditions"""
    condition_code: str = Field(..., description="SNOMED code for the condition")
    condition_label: str = Field(..., description="Human-readable condition label")
    condition_system: str = Field(default="snomed", description="Coding system")

    # Common fields
    diagnosed_by_physician: Optional[bool] = Field(None, description="Whether diagnosed by a physician")
    duration: Optional[str] = Field(None, description="Duration of condition (e.g., 'less-than-a-month')")
    physician_frequency: Optional[str] = Field(None, description="Frequency of physician visits")

    # Diabetes-specific fields
    diabetes_type: Optional[str] = Field(None, description="Type of diabetes (e.g., 'type-1-diabetes')")
    therapy_type: Optional[str] = Field(None, description="Therapy type (e.g., 'pills', 'pen-syringe')")
    wants_glucose_reminders: Optional[bool] = Field(None, description="Whether user wants glucose reminders")

    # Chronic pain-specific fields
    pain_type: Optional[str] = Field(None, description="Type of pain (e.g., 'musculoskeletal-pain')")


class UserConditionCreate(UserConditionBase):
    """Schema for creating a user condition"""
    pass


class UserConditionUpdate(BaseModel):
    """Schema for updating a user condition (all fields optional)"""
    condition_label: Optional[str] = None
    condition_system: Optional[str] = None
    diagnosed_by_physician: Optional[bool] = None
    duration: Optional[str] = None
    physician_frequency: Optional[str] = None
    diabetes_type: Optional[str] = None
    therapy_type: Optional[str] = None
    wants_glucose_reminders: Optional[bool] = None
    pain_type: Optional[str] = None


class UserConditionResponse(UserConditionBase):
    """Schema for user condition responses"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True