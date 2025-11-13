"""Token-related Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.features.auth.domain.schemas.user import UserResponse


class Token(BaseModel):
    """JWT token response schema with onboarding status"""
    access_token: str
    token_type: str = "bearer"
    onboarding_completed: bool = Field(..., description="Whether user has completed onboarding questionnaire")
    user: "UserResponse" = Field(..., description="User information (excluding password)")

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    """Decoded token data schema"""
    email: Optional[str] = None
    user_id: Optional[int] = None


# Import for forward reference resolution
from app.features.auth.domain.schemas.user import UserResponse
Token.model_rebuild()
