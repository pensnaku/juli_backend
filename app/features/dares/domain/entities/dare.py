"""Dare entity - master list of all dares/challenges"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Dare(Base):
    """Master list of all dares/challenges"""
    __tablename__ = "dares"

    id = Column(Integer, primary_key=True, index=True)

    # Dare content
    text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)  # Activity, Nutrition, Sleep, Wellness
    subcategory = Column(String(50), nullable=True)  # Meal, Hydration, Alcohol, Vegetables, Fruit
    points = Column(Integer, nullable=False, default=1)

    # Condition filtering - only show to users WITH this condition
    condition = Column(String(50), nullable=True)  # asthma, depress, bipolar, etc.

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    assignments = relationship("DailyDareAssignment", back_populates="dare")

    def __repr__(self):
        return f"<Dare(id={self.id}, category={self.category}, points={self.points})>"
