"""UserSettings entity - user preferences and configuration"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserSettings(Base):
    """User settings and preferences (separate from authentication)"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Location and regional settings from mobile app
    store_country = Column(String, nullable=True)
    store_region = Column(String, nullable=True)
    timezone = Column(String, nullable=True)  # e.g., "America/New_York", "Africa/Lagos"

    # Questionnaire-related settings
    daily_routine = Column(String, nullable=True)  # "student", "working", etc.
    ethnicity = Column(String, nullable=True)
    hispanic_latino = Column(String, nullable=True)
    allow_medical_support = Column(Boolean, default=False)

    # Additional settings (optional, for future use)
    phone_number = Column(String, nullable=True)
    language_preference = Column(String, default="en")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship back to user
    user = relationship("User", back_populates="settings")

    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, routine={self.daily_routine})>"
