"""QuestionnaireCompletion entity - tracks questionnaire assignment and completion"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class QuestionnaireCompletion(Base):
    """
    Tracks when questionnaires are assigned to users and when they're completed.
    This allows tracking of onboarding, daily, biweekly, and other questionnaire types.
    """
    __tablename__ = "questionnaire_completions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    questionnaire_id = Column(String, nullable=False, index=True)  # "onboarding", "daily", "biweekly"

    # Tracking timestamps
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())  # When questionnaire was sent/assigned
    completed_at = Column(DateTime(timezone=True), nullable=True)  # When user completed it (null = not completed)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship back to user
    user = relationship("User", back_populates="questionnaire_completions")

    # Ensure one record per user per questionnaire type
    # For recurring questionnaires (daily), you might want to remove this constraint
    # and add a date field to track daily completions
    __table_args__ = (
        UniqueConstraint('user_id', 'questionnaire_id', name='uq_user_questionnaire'),
    )

    @property
    def is_completed(self) -> bool:
        """Check if questionnaire is completed"""
        return self.completed_at is not None

    def __repr__(self):
        status = "completed" if self.is_completed else "pending"
        return f"<QuestionnaireCompletion(user_id={self.user_id}, questionnaire={self.questionnaire_id}, status={status})>"