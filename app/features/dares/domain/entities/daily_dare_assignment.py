"""DailyDareAssignment entity - tracks which dares are assigned to users"""
from sqlalchemy import Column, Integer, Boolean, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DailyDareAssignment(Base):
    """Tracks daily dare assignments per user"""
    __tablename__ = "daily_dare_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    dare_id = Column(Integer, ForeignKey("dares.id"), nullable=False, index=True)

    # The user's local date when this dare was assigned
    assigned_date = Column(Date, nullable=False, index=True)

    # Completion tracking
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    points_earned = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="dare_assignments")
    dare = relationship("Dare", back_populates="assignments")

    # Ensure a user can't get the same dare twice on the same day
    __table_args__ = (
        UniqueConstraint('user_id', 'dare_id', 'assigned_date', name='uq_user_dare_date'),
    )

    def __repr__(self):
        return f"<DailyDareAssignment(user_id={self.user_id}, dare_id={self.dare_id}, date={self.assigned_date})>"