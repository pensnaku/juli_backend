"""Domain entities for authentication feature"""
from app.features.auth.domain.entities.user import User
from app.features.auth.domain.entities.user_settings import UserSettings

__all__ = ["User", "UserSettings"]
