"""UserReminder entity - user reminders and notifications"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Time, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserReminder(Base):
    """User reminders for various notification types"""
    __tablename__ = "user_reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    medication_id = Column(Integer, ForeignKey("user_medications.id"), nullable=True, index=True)

    # Reminder configuration
    reminder_type = Column(String, nullable=False)  # "daily_check_in", "glucose_check", "medication", etc.
    time = Column(Time, nullable=False)  # Time of day for reminder (e.g., 08:00:00)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="reminders")
    medication = relationship("UserMedication", back_populates="reminders")

    def __repr__(self):
        return f"<UserReminder(user_id={self.user_id}, type={self.reminder_type}, time={self.time})>"