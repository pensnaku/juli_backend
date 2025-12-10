"""UserReminder Pydantic schemas"""
from typing import Optional
from datetime import datetime
from datetime import time as time_type
from pydantic import BaseModel, Field


class UserReminderBase(BaseModel):
    """Base schema for user reminders"""
    reminder_type: str = Field(..., description="Type of reminder (e.g., 'daily_check_in', 'glucose_check', 'medication_reminder')")
    time: time_type = Field(..., description="Time of day for reminder")
    is_active: bool = Field(default=True, description="Whether reminder is active")


class UserReminderCreate(UserReminderBase):
    """Schema for creating a user reminder"""
    medication_id: Optional[int] = Field(None, description="Associated medication ID (for medication_reminder type)")


class UserReminderUpdate(BaseModel):
    """Schema for updating a user reminder (all fields optional)"""
    reminder_type: Optional[str] = None
    time: Optional[time_type] = None
    is_active: Optional[bool] = None


class UserReminderResponse(UserReminderBase):
    """Schema for user reminder responses"""
    id: int
    user_id: int
    medication_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True