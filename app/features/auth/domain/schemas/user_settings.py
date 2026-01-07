"""UserSettings-related Pydantic schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserSettingsBase(BaseModel):
    """Base schema for user settings"""
    store_country: Optional[str] = None
    store_region: Optional[str] = None
    timezone: Optional[str] = None
    phone_number: Optional[str] = None
    language_preference: str = "en"
    ethnicity: Optional[str] = None
    hispanic_latino: Optional[str] = None


class UserSettingsCreate(UserSettingsBase):
    """Schema for creating user settings"""
    pass


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings"""
    store_country: Optional[str] = None
    store_region: Optional[str] = None
    timezone: Optional[str] = None
    phone_number: Optional[str] = None
    language_preference: Optional[str] = None


class UserSettingsResponse(UserSettingsBase):
    """Schema for user settings response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
