"""UserCondition entity - medical conditions and condition-specific data"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserCondition(Base):
    """
    User medical conditions with condition-specific details.
    Condition-specific fields are nullable and only populated for relevant conditions.
    """
    __tablename__ = "user_conditions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Core condition data (always populated)
    condition_code = Column(String, nullable=False)  # SNOMED: "73211009"
    condition_label = Column(String, nullable=False)  # "Diabetes"
    condition_system = Column(String, default="snomed")  # Coding system

    # Common fields (populated when user answers related questions)
    diagnosed_by_physician = Column(Boolean, nullable=True)
    duration = Column(String, nullable=True)  # "less-than-a-month", etc.
    physician_frequency = Column(String, nullable=True)  # "regularly", etc.

    # Diabetes-specific fields (nullable, only populated for diabetes)
    diabetes_type = Column(String, nullable=True)  # "type-1-diabetes", etc.
    therapy_type = Column(String, nullable=True)  # "pills", "pen-syringe", etc.
    wants_glucose_reminders = Column(Boolean, nullable=True)

    # Chronic pain-specific fields (nullable, only populated for chronic pain)
    pain_type = Column(String, nullable=True)  # "musculoskeletal-pain", etc.

    # Future condition-specific fields can be added here as needed
    # asthma_severity = Column(String, nullable=True)
    # migraine_frequency = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="conditions")

    # Unique constraint: one row per user per condition
    __table_args__ = (
        UniqueConstraint('user_id', 'condition_code', name='uq_user_condition'),
    )

    def __repr__(self):
        return f"<UserCondition(user_id={self.user_id}, condition={self.condition_label})>"