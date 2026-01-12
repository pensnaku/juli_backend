"""Journal entry entity"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class JournalEntry(Base):
    """User journal entries"""
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    content = Column(Text, nullable=False)

    # Source tracking
    source = Column(String(50), nullable=True)  # e.g., 'questionnaire', 'manual', 'voice'
    questionnaire_completion_id = Column(
        Integer,
        ForeignKey("questionnaire_completions.id"),
        nullable=True,
        index=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="journal_entries")
    questionnaire_completion = relationship("QuestionnaireCompletion", back_populates="journal_entries")

    def __repr__(self):
        return f"<JournalEntry(id={self.id}, user_id={self.user_id})>"