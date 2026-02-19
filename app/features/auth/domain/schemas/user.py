"""User-related Pydantic schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a new user - requires email, password, and legal confirmations"""
    password: str = Field(..., min_length=8, max_length=72, description="Password must be between 8 and 72 characters")
    terms_accepted: bool = Field(..., description="User must accept terms and conditions")
    age_confirmed: bool = Field(..., description="User must confirm they meet minimum age requirement")
    store_country: Optional[str] = Field(None, description="App store country code")
    store_region: Optional[str] = Field(None, description="App store region")


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=72, description="Password must be between 8 and 72 characters")


class ResetPasswordLinkRequest(BaseModel):
    """Schema for requesting a password reset email"""
    email: EmailStr = Field(..., description="Email address to send reset link to")


class ResetPasswordRequest(BaseModel):
    """Schema for resetting password with a signed token"""
    signed_payload: str = Field(..., description="Signed token from the reset email link")
    password: str = Field(..., min_length=8, max_length=72, description="New password")


class EmailValidationRequest(BaseModel):
    """Schema for email validation request"""
    email: EmailStr = Field(..., description="Email address to validate")


class EmailValidationResponse(BaseModel):
    """Schema for email validation response"""
    email: str
    is_valid: bool = Field(..., description="Whether the email format is valid")
    is_available: bool = Field(..., description="Whether the email is available (not already registered)")
    message: str = Field(..., description="Descriptive message about the validation result")


class UserResponse(UserBase):
    """Schema for user response (excludes password)"""
    id: int
    full_name: Optional[str] = None  # Populated during onboarding
    age: Optional[int] = None
    gender: Optional[str] = None
    is_active: bool
    is_superuser: bool
    is_legacy_user: bool
    email_confirmed: bool
    terms_accepted: bool
    age_confirmed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    settings: Optional["UserSettingsResponse"] = None  # Forward reference
    conditions: list["UserConditionResponse"] = []  # User's health conditions ordered by priority

    @classmethod
    def from_orm(cls, obj):
        """Override from_orm to use ordered_conditions instead of conditions"""
        # Get the dict representation
        data = super().from_orm(obj).__dict__
        # Replace conditions with ordered_conditions if available
        if hasattr(obj, 'ordered_conditions'):
            data['conditions'] = obj.ordered_conditions
        return cls(**data)

    class Config:
        from_attributes = True


class UserWithOnboardingStatus(UserResponse):
    """Schema for user response with onboarding completion status"""
    onboarding_completed: bool = Field(..., description="Whether user has completed onboarding questionnaire")

    class Config:
        from_attributes = True


# Import for forward reference resolution
from app.features.auth.domain.schemas.user_settings import UserSettingsResponse
from app.features.auth.domain.schemas.user_condition import UserConditionResponse
UserResponse.model_rebuild()
UserWithOnboardingStatus.model_rebuild()
