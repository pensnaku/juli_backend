"""QuestionnaireCompletion entity - tracks questionnaire assignment and completion"""
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class QuestionnaireCompletion(Base):
    """
    Tracks when questionnaires are assigned to users and when they're completed.
    This allows tracking of onboarding, daily, biweekly, and other questionnaire types.

    For recurring questionnaires (daily), completion_date tracks which day the
    questionnaire is for. For one-time questionnaires (onboarding), completion_date is NULL.
    """
    __tablename__ = "questionnaire_completions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    questionnaire_id = Column(String, nullable=False, index=True)  # "onboarding", "daily", "biweekly"

    # Date for recurring questionnaires (NULL for one-time questionnaires like onboarding)
    completion_date = Column(Date, nullable=True, index=True)

    # Tracking timestamps
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())  # When questionnaire was sent/assigned
    completed_at = Column(DateTime(timezone=True), nullable=True)  # When user completed it (null = not completed)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="questionnaire_completions")
    observations = relationship("Observation", back_populates="questionnaire_completion")
    journal_entries = relationship("JournalEntry", back_populates="questionnaire_completion")

    # Unique constraint includes completion_date to allow recurring questionnaires
    # For onboarding (completion_date=NULL), only one record per user
    # For daily (completion_date=specific date), one record per user per date
    __table_args__ = (
        UniqueConstraint('user_id', 'questionnaire_id', 'completion_date',
                        name='uq_user_questionnaire_date'),
    )

    @property
    def is_completed(self) -> bool:
        """Check if questionnaire is completed"""
        return self.completed_at is not None

    def __repr__(self):
        status = "completed" if self.is_completed else "pending"
        return f"<QuestionnaireCompletion(user_id={self.user_id}, questionnaire={self.questionnaire_id}, status={status})>"