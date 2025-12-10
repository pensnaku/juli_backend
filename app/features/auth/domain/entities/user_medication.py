"""UserMedication entity - user medications"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserMedication(Base):
    """User medications"""
    __tablename__ = "user_medications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Medication details
    medication_name = Column(String, nullable=False)
    dosage = Column(String, nullable=True)
    times_per_day = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="medications")
    reminders = relationship("UserReminder", back_populates="medication", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserMedication(id={self.id}, user_id={self.user_id}, name={self.medication_name})>"