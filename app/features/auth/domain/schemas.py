"""Pydantic schemas for authentication"""
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
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response schema"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token data schema"""
    email: Optional[str] = None
    user_id: Optional[int] = None