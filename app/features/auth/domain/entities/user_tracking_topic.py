"""UserTrackingTopic entity - topics users want to track"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserTrackingTopic(Base):
    """Topics that users want to track (e.g., coffee consumption, alcohol, etc.)"""
    __tablename__ = "user_tracking_topics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Topic details
    topic_code = Column(String, nullable=False)  # e.g., "coffee-consumption"
    topic_label = Column(String, nullable=False)  # e.g., "Coffee consumption"
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="tracking_topics")

    # Ensure one topic per user
    __table_args__ = (
        UniqueConstraint('user_id', 'topic_code', name='uq_user_topic'),
    )

    def __repr__(self):
        return f"<UserTrackingTopic(user_id={self.user_id}, topic={self.topic_code})>"