"""Auth domain layer - entities and schemas"""

# Export entities
from app.features.auth.domain.entities import (
    User,
    UserSettings,
    UserCondition,
    UserReminder
)

# Export schemas
from app.features.auth.domain.schemas import (
    UserBase,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    UserWithOnboardingStatus,
    EmailValidationRequest,
    EmailValidationResponse,
    UserSettingsBase,
    UserSettingsCreate,
    UserSettingsUpdate,
    UserSettingsResponse,
    Token,
    TokenData,
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

__all__ = [
    # Entities
    "User",
    "UserSettings",
    "UserCondition",
    "UserReminder",
    # User schemas
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "UserWithOnboardingStatus",
    "EmailValidationRequest",
    "EmailValidationResponse",
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
