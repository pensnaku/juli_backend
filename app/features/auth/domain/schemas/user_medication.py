"""Pydantic schemas for user medications"""
from typing import Optional, List
from datetime import datetime
from datetime import time as time_type
from pydantic import BaseModel, Field

from app.features.auth.domain.schemas.user_reminder import UserReminderResponse


class UserMedicationBase(BaseModel):
    """Base schema for user medications"""
    medication_name: str = Field(..., description="Name of the medication")
    dosage: Optional[str] = Field(None, description="Dosage information")
    times_per_day: Optional[int] = Field(None, description="Number of times per day to take medication")
    notes: Optional[str] = Field(None, description="Additional notes")
    reminder_enabled: bool = Field(default=True, description="Whether user wants reminders for this medication")


class UserMedicationCreate(UserMedicationBase):
    """Schema for creating a user medication"""
    notification_times: Optional[List[time_type]] = Field(None, description="List of times to send medication reminders")


class UserMedicationUpdate(BaseModel):
    """Schema for updating a user medication (all fields optional)"""
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    times_per_day: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    reminder_enabled: Optional[bool] = Field(None, description="Whether user wants reminders for this medication")
    notification_times: Optional[List[time_type]] = Field(None, description="List of times to send medication reminders (replaces existing)")


class UserMedicationResponse(UserMedicationBase):
    """Schema for user medication response"""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    reminders: List[UserReminderResponse] = Field(default_factory=list, description="Associated medication reminders")

    class Config:
        from_attributes = True