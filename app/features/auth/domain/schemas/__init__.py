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
from app.features.auth.domain.schemas.user_condition import (
    UserConditionBase,
    UserConditionCreate,
    UserConditionUpdate,
    UserConditionResponse,
)
from app.features.auth.domain.schemas.user_reminder import (
    UserReminderBase,
    UserReminderCreate,
    UserReminderUpdate,
    UserReminderResponse,
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
    # User condition schemas
    "UserConditionBase",
    "UserConditionCreate",
    "UserConditionUpdate",
    "UserConditionResponse",
    # User reminder schemas
    "UserReminderBase",
    "UserReminderCreate",
    "UserReminderUpdate",
    "UserReminderResponse",
    # Token schemas
    "Token",
    "TokenData",
]
