"""User entity - authentication and authorization"""
from typing import List
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """User entity for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_legacy_user = Column(Boolean, default=False)

    # Legal compliance fields
    terms_accepted = Column(Boolean, default=False, nullable=False)
    age_confirmed = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    settings = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    conditions = relationship(
        "UserCondition",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    reminders = relationship(
        "UserReminder",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    medications = relationship(
        "UserMedication",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    tracking_topics = relationship(
        "UserTrackingTopic",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    questionnaire_completions = relationship(
        "QuestionnaireCompletion",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    journal_entries = relationship(
        "JournalEntry",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    observations = relationship(
        "Observation",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    juli_scores = relationship(
        "JuliScore",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    @property
    def ordered_conditions(self) -> List:
        """
        Get user conditions ordered by clinical priority.

        Uses the order_leading_conditions utility to sort conditions
        by their clinical priority, with the leading condition first.

        Returns:
            List of UserCondition objects sorted by priority
        """
        if not self.conditions:
            return []

        from app.shared.condition_utils import order_leading_conditions

        # Get condition codes
        condition_codes = [c.condition_code for c in self.conditions]

        # Order them by priority
        ordered_codes = order_leading_conditions(condition_codes)

        # Create a mapping of condition_code -> condition object
        condition_map = {c.condition_code: c for c in self.conditions}

        # Return conditions in priority order
        return [condition_map[code] for code in ordered_codes if code in condition_map]

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
