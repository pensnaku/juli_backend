"""User profile update schemas (separate from UserUpdate which includes email/password)"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ConditionFieldsUpdate(BaseModel):
    """Schema for updating fields on an existing condition"""
    condition_code: str = Field(..., description="SNOMED code to identify which condition to update")
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


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile information (excludes email/password)"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="User's full name")
    age: Optional[int] = Field(None, ge=1, le=150, description="User's age")
    gender: Optional[str] = Field(None, description="User's gender")
    ethnicity: Optional[str] = Field(None, description="User's ethnicity")
    hispanic_latino: Optional[str] = Field(None, description="User's Hispanic/Latino origin")
    conditions: Optional[List[ConditionFieldsUpdate]] = Field(None, description="List of existing conditions to update (identified by condition_code)")


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    id: int
    email: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    ethnicity: Optional[str] = None
    hispanic_latino: Optional[str] = None

    class Config:
        from_attributes = True
