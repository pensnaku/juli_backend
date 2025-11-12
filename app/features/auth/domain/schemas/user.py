"""User-related Pydantic schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user response (excludes password)"""
    id: int
    is_active: bool
    is_superuser: bool
    is_legacy_user: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    settings: Optional["UserSettingsResponse"] = None  # Forward reference

    class Config:
        from_attributes = True


# Import for forward reference resolution
from app.features.auth.domain.schemas.user_settings import UserSettingsResponse
UserResponse.model_rebuild()
