"""Pydantic schemas for authentication feature"""
from app.features.auth.domain.schemas.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    UserWithOnboardingStatus,
    EmailValidationRequest,
    EmailValidationResponse,
    ResetPasswordLinkRequest,
    ResetPasswordRequest,
)
from app.features.auth.domain.schemas.user_profile import (
    UserProfileUpdate,
    UserProfileResponse,
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
from app.features.auth.domain.schemas.user_medication import (
    UserMedicationBase,
    UserMedicationCreate,
    UserMedicationUpdate,
    UserMedicationResponse,
)
from app.features.auth.domain.schemas.user_tracking_topic import (
    UserTrackingTopicBase,
    UserTrackingTopicCreate,
    UserTrackingTopicUpdate,
    UserTrackingTopicResponse,
    TrackingTopicUpdate,
    TrackingTopicResponse,
    TrackingTopicListResponse,
)
from app.features.auth.domain.schemas.token import Token, TokenData

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "UserWithOnboardingStatus",
    "EmailValidationRequest",
    "EmailValidationResponse",
    "ResetPasswordLinkRequest",
    "ResetPasswordRequest",
    # User profile schemas
    "UserProfileUpdate",
    "UserProfileResponse",
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
    # User medication schemas
    "UserMedicationBase",
    "UserMedicationCreate",
    "UserMedicationUpdate",
    "UserMedicationResponse",
    # User tracking topic schemas
    "UserTrackingTopicBase",
    "UserTrackingTopicCreate",
    "UserTrackingTopicUpdate",
    "UserTrackingTopicResponse",
    "TrackingTopicUpdate",
    "TrackingTopicResponse",
    "TrackingTopicListResponse",
    # Token schemas
    "Token",
    "TokenData",
]
