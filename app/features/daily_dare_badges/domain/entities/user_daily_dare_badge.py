"""UserDailyDareBadge entity for tracking earned badges"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserDailyDareBadge(Base):
    """
    UserDailyDareBadge entity for tracking which badges users have earned.
    """
    __tablename__ = "user_daily_dare_badges"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_id = Column(Integer, ForeignKey("daily_dare_badges.id", ondelete="CASCADE"), nullable=False, index=True)
    earned_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", backref="daily_dare_badges")
    badge = relationship("DailyDareBadge", back_populates="user_badges")

    def __repr__(self):
        return f"<UserDailyDareBadge(id={self.id}, user_id={self.user_id}, badge_id={self.badge_id})>"
