"""Observation entity for health data tracking"""
import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Observation(Base):
    """
    Observation entity for storing health data collected from users.

    This can include mood data, health metrics, questionnaire responses,
    sleep data, workout data, heart rate, etc.
    """
    __tablename__ = "observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Observation type identification
    code = Column(String(100), nullable=False)  # e.g., 'sleep', 'workout', 'heart-rate', 'mood'
    variant = Column(String(100), nullable=True)  # e.g., 'deep', 'running', 'resting', NULL

    # Flexible value storage - only one should be populated per observation
    value_integer = Column(Integer, nullable=True)
    value_decimal = Column(Numeric(10, 4), nullable=True)
    value_string = Column(String(500), nullable=True)
    value_boolean = Column(Boolean, nullable=True)

    # Timing
    effective_at = Column(DateTime(timezone=True), nullable=False)  # When the observation occurred
    period_start = Column(DateTime(timezone=True), nullable=True)  # For observations spanning a period
    period_end = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    category = Column(String(50), nullable=True)  # e.g., 'vital-signs', 'activity', 'mental-health'
    data_source = Column(String(50), nullable=True)  # e.g., 'manual', 'apple-health', 'questionnaire'
    unit = Column(String(20), nullable=True)  # e.g., 'minutes', 'bpm', 'steps'

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # External reference for deduplication
    source_id = Column(String(255), nullable=True)  # External ID from data source

    # Relationships
    user = relationship("User", back_populates="observations")

    # Unique constraint to prevent duplicate observations
    __table_args__ = (
        UniqueConstraint(
            'user_id', 'code', 'variant', 'effective_at', 'source_id',
            name='uq_observation_user_code_variant_time_source'
        ),
    )

    def __repr__(self):
        return f"<Observation(id={self.id}, user_id={self.user_id}, code={self.code}, variant={self.variant})>"
