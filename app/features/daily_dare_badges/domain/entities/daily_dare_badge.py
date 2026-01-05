"""DailyDareBadge entity for badge definitions"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DailyDareBadge(Base):
    """
    DailyDareBadge entity for storing badge definitions.

    Badge types:
    - regular: Progression-based badges (Strong Start, Daredevil, Streak, etc.)
    - monthly: Time-limited badges with category-specific criteria
    """
    __tablename__ = "daily_dare_badges"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    pre_text = Column(Text, nullable=True)  # Text shown before earning
    post_text = Column(Text, nullable=True)  # Text shown after earning

    type = Column(String(20), nullable=False, default='regular', index=True)  # 'regular' or 'monthly'
    level = Column(Integer, nullable=True)  # 1-5 for tiered badges
    priority = Column(Integer, nullable=True)  # Display order for regular badges

    can_be_multiple = Column(Boolean, nullable=False, default=False)  # Can be earned multiple times

    # For monthly badges
    month = Column(Integer, nullable=True)  # 1-12
    year = Column(Integer, nullable=True)

    # Badge criteria (flattened from JSON)
    criteria_category = Column(String(50), nullable=True)  # Target category (e.g., 'nutrition', 'sleep')
    criteria_expected_count = Column(Integer, nullable=True)  # Count requirement
    criteria_expected_point_sum = Column(Integer, nullable=True)  # Points total requirement
    criteria_unique_day_count = Column(Integer, nullable=True)  # Unique days requirement

    # Badge images
    image_earned = Column(String(500), nullable=True)
    image_not_earned = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_badges = relationship("UserDailyDareBadge", back_populates="badge")

    def __repr__(self):
        return f"<DailyDareBadge(id={self.id}, slug={self.slug}, type={self.type})>"
