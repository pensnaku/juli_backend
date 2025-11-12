"""Repository for questionnaire completion database operations"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.shared.questionnaire.entities import QuestionnaireCompletion


class QuestionnaireCompletionRepository:
    """Handles all database operations for questionnaire completions"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, completion_id: int) -> Optional[QuestionnaireCompletion]:
        """Get questionnaire completion by ID"""
        return self.db.query(QuestionnaireCompletion).filter(
            QuestionnaireCompletion.id == completion_id
        ).first()

    def get_by_user_and_questionnaire(
        self, user_id: int, questionnaire_id: str
    ) -> Optional[QuestionnaireCompletion]:
        """Get completion record for a specific user and questionnaire"""
        return self.db.query(QuestionnaireCompletion).filter(
            QuestionnaireCompletion.user_id == user_id,
            QuestionnaireCompletion.questionnaire_id == questionnaire_id
        ).first()

    def get_all_by_user(self, user_id: int) -> List[QuestionnaireCompletion]:
        """Get all questionnaire completions for a user"""
        return self.db.query(QuestionnaireCompletion).filter(
            QuestionnaireCompletion.user_id == user_id
        ).all()

    def get_completed_by_user(self, user_id: int) -> List[QuestionnaireCompletion]:
        """Get all completed questionnaires for a user"""
        return self.db.query(QuestionnaireCompletion).filter(
            QuestionnaireCompletion.user_id == user_id,
            QuestionnaireCompletion.completed_at.isnot(None)
        ).all()

    def get_pending_by_user(self, user_id: int) -> List[QuestionnaireCompletion]:
        """Get all pending (not completed) questionnaires for a user"""
        return self.db.query(QuestionnaireCompletion).filter(
            QuestionnaireCompletion.user_id == user_id,
            QuestionnaireCompletion.completed_at.is_(None)
        ).all()

    def assign_questionnaire(
        self, user_id: int, questionnaire_id: str
    ) -> QuestionnaireCompletion:
        """
        Assign a questionnaire to a user (create a tracking record).
        If already assigned, returns existing record.
        """
        existing = self.get_by_user_and_questionnaire(user_id, questionnaire_id)
        if existing:
            return existing

        completion = QuestionnaireCompletion(
            user_id=user_id,
            questionnaire_id=questionnaire_id
        )
        self.db.add(completion)
        self.db.commit()
        self.db.refresh(completion)
        return completion

    def mark_completed(
        self, user_id: int, questionnaire_id: str
    ) -> QuestionnaireCompletion:
        """
        Mark a questionnaire as completed.
        If not yet assigned, creates the record and marks it completed.
        """
        completion = self.get_by_user_and_questionnaire(user_id, questionnaire_id)

        if not completion:
            # Create new completion record
            completion = QuestionnaireCompletion(
                user_id=user_id,
                questionnaire_id=questionnaire_id,
                completed_at=datetime.now(timezone.utc)
            )
            self.db.add(completion)
        else:
            # Update existing record
            completion.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(completion)
        return completion

    def is_completed(self, user_id: int, questionnaire_id: str) -> bool:
        """Check if a user has completed a specific questionnaire"""
        completion = self.get_by_user_and_questionnaire(user_id, questionnaire_id)
        return completion is not None and completion.is_completed

    def delete(self, completion: QuestionnaireCompletion) -> None:
        """Delete a questionnaire completion record"""
        self.db.delete(completion)
        self.db.commit()