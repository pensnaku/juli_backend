"""Pydantic schemas for authentication feature"""
from app.features.auth.domain.schemas.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
)
from app.features.auth.domain.schemas.user_settings import (
    UserSettingsBase,
    UserSettingsCreate,
    UserSettingsUpdate,
    UserSettingsResponse,
)
from app.features.auth.domain.schemas.token import Token, TokenData

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    # User settings schemas
    "UserSettingsBase",
    "UserSettingsCreate",
    "UserSettingsUpdate",
    "UserSettingsResponse",
    # Token schemas
    "Token",
    "TokenData",
]
