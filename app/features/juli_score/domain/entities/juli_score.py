"""JuliScore entity for health wellness scores"""
import uuid
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class JuliScore(Base):
    """
    JuliScore entity for storing calculated health wellness scores.

    Each score is calculated for a specific user and condition, with
    flattened factor inputs and scores for queryability.
    """
    __tablename__ = "juli_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    condition_code = Column(String(20), nullable=False, index=True)  # SNOMED-CT code
    score = Column(Integer, nullable=False)  # Final score 0-100
    effective_at = Column(DateTime(timezone=True), nullable=False)

    # Factor columns: _input = raw observation, _score = calculated contribution
    air_quality_input = Column(Numeric(10, 4), nullable=True)
    air_quality_score = Column(Numeric(10, 4), nullable=True)

    sleep_input = Column(Numeric(10, 4), nullable=True)  # Minutes slept
    sleep_score = Column(Numeric(10, 4), nullable=True)

    biweekly_input = Column(Numeric(10, 4), nullable=True)  # Raw questionnaire score
    biweekly_score = Column(Numeric(10, 4), nullable=True)

    active_energy_input = Column(Numeric(10, 4), nullable=True)  # Avg kcal
    active_energy_score = Column(Numeric(10, 4), nullable=True)

    medication_input = Column(Numeric(10, 4), nullable=True)  # Compliance ratio 0-1
    medication_score = Column(Numeric(10, 4), nullable=True)

    mood_input = Column(Numeric(10, 4), nullable=True)  # Mood value 1-5
    mood_score = Column(Numeric(10, 4), nullable=True)

    hrv_input = Column(Numeric(10, 4), nullable=True)  # HRV diff from average
    hrv_score = Column(Numeric(10, 4), nullable=True)

    pollen_input = Column(Numeric(10, 4), nullable=True)  # Pollen count (Asthma only)
    pollen_score = Column(Numeric(10, 4), nullable=True)

    inhaler_input = Column(Numeric(10, 4), nullable=True)  # Usage count (Asthma only)
    inhaler_score = Column(Numeric(10, 4), nullable=True)

    # Metadata
    data_points_used = Column(Integer, nullable=False)
    total_weight = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="juli_scores")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            'user_id', 'condition_code', 'effective_at',
            name='uq_juli_score_user_condition_time'
        ),
        Index('idx_juli_score_user_condition', 'user_id', 'condition_code'),
    )

    def __repr__(self):
        return f"<JuliScore(id={self.id}, user_id={self.user_id}, condition={self.condition_code}, score={self.score})>"
