"""Repository for questionnaire completion database operations"""
from typing import Optional, List
from datetime import datetime, timezone, date
from sqlalchemy.orm import Session
from app.shared.questionnaire.entities import QuestionnaireCompletion
from app.shared.constants import QUESTIONNAIRE_IDS


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

    # ========== Date-based methods for recurring questionnaires ==========

    def get_by_user_questionnaire_date(
        self, user_id: int, questionnaire_id: str, completion_date: date
    ) -> Optional[QuestionnaireCompletion]:
        """Get completion record for a specific user, questionnaire, and date"""
        return self.db.query(QuestionnaireCompletion).filter(
            QuestionnaireCompletion.user_id == user_id,
            QuestionnaireCompletion.questionnaire_id == questionnaire_id,
            QuestionnaireCompletion.completion_date == completion_date
        ).first()

    def is_daily_completed_for_date(
        self, user_id: int, completion_date: date
    ) -> bool:
        """Check if user has completed daily questionnaire for a specific date"""
        completion = self.get_by_user_questionnaire_date(
            user_id, QUESTIONNAIRE_IDS["DAILY"], completion_date
        )
        return completion is not None and completion.is_completed

    def assign_daily_questionnaire(
        self, user_id: int, completion_date: date
    ) -> QuestionnaireCompletion:
        """
        Assign daily questionnaire to a user for a specific date.
        If already assigned, returns existing record.
        """
        existing = self.get_by_user_questionnaire_date(
            user_id, QUESTIONNAIRE_IDS["DAILY"], completion_date
        )
        if existing:
            return existing

        completion = QuestionnaireCompletion(
            user_id=user_id,
            questionnaire_id=QUESTIONNAIRE_IDS["DAILY"],
            completion_date=completion_date
        )
        self.db.add(completion)
        self.db.commit()
        self.db.refresh(completion)
        return completion

    def mark_daily_completed(
        self, user_id: int, completion_date: date
    ) -> QuestionnaireCompletion:
        """
        Mark daily questionnaire as completed for a specific date.
        If not yet assigned, creates the record and marks it completed.
        """
        completion = self.get_by_user_questionnaire_date(
            user_id, QUESTIONNAIRE_IDS["DAILY"], completion_date
        )

        if not completion:
            completion = QuestionnaireCompletion(
                user_id=user_id,
                questionnaire_id=QUESTIONNAIRE_IDS["DAILY"],
                completion_date=completion_date,
                completed_at=datetime.now(timezone.utc)
            )
            self.db.add(completion)
        else:
            completion.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(completion)
        return completion

    def get_daily_completions_in_range(
        self, user_id: int, start_date: date, end_date: date
    ) -> List[QuestionnaireCompletion]:
        """Get all daily questionnaire completions for a user within a date range"""
        return self.db.query(QuestionnaireCompletion).filter(
            QuestionnaireCompletion.user_id == user_id,
            QuestionnaireCompletion.questionnaire_id == QUESTIONNAIRE_IDS["DAILY"],
            QuestionnaireCompletion.completion_date >= start_date,
            QuestionnaireCompletion.completion_date <= end_date
        ).all()

    # ========== Per-condition completion tracking ==========

    def is_condition_completed_for_date(
        self, user_id: int, questionnaire_id: str, completion_date: date
    ) -> bool:
        """
        Check if a specific condition questionnaire is completed for a date.

        Args:
            user_id: User ID
            questionnaire_id: Questionnaire ID (e.g., 'daily-asthma', 'daily-diabetes')
            completion_date: The date to check

        Returns:
            True if completed, False otherwise
        """
        completion = self.get_by_user_questionnaire_date(
            user_id, questionnaire_id, completion_date
        )
        return completion is not None and completion.is_completed

    def assign_questionnaire_for_date(
        self, user_id: int, questionnaire_id: str, completion_date: date
    ) -> QuestionnaireCompletion:
        """
        Assign a questionnaire to a user for a specific date.
        If already assigned, returns existing record.

        Args:
            user_id: User ID
            questionnaire_id: Questionnaire ID (e.g., 'daily-asthma')
            completion_date: The date for this questionnaire

        Returns:
            The completion record
        """
        existing = self.get_by_user_questionnaire_date(
            user_id, questionnaire_id, completion_date
        )
        if existing:
            return existing

        completion = QuestionnaireCompletion(
            user_id=user_id,
            questionnaire_id=questionnaire_id,
            completion_date=completion_date
        )
        self.db.add(completion)
        self.db.commit()
        self.db.refresh(completion)
        return completion

    def mark_condition_completed(
        self, user_id: int, questionnaire_id: str, completion_date: date
    ) -> QuestionnaireCompletion:
        """
        Mark a condition-specific questionnaire as completed for a date.

        Args:
            user_id: User ID
            questionnaire_id: Questionnaire ID (e.g., 'daily-asthma')
            completion_date: The date for this questionnaire

        Returns:
            The completion record
        """
        completion = self.get_by_user_questionnaire_date(
            user_id, questionnaire_id, completion_date
        )

        if not completion:
            completion = QuestionnaireCompletion(
                user_id=user_id,
                questionnaire_id=questionnaire_id,
                completion_date=completion_date,
                completed_at=datetime.now(timezone.utc)
            )
            self.db.add(completion)
        else:
            completion.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(completion)
        return completion

    def get_all_for_date(
        self, user_id: int, completion_date: date
    ) -> List[QuestionnaireCompletion]:
        """
        Get all questionnaire completions for a user on a specific date.

        Args:
            user_id: User ID
            completion_date: The date to query

        Returns:
            List of completion records for that date
        """
        return self.db.query(QuestionnaireCompletion).filter(
            QuestionnaireCompletion.user_id == user_id,
            QuestionnaireCompletion.completion_date == completion_date
        ).all()

    def delete_all_for_date(self, user_id: int, completion_date: date) -> int:
        """
        Delete all questionnaire completions for a user on a specific date.

        Args:
            user_id: User ID
            completion_date: The date to delete completions for

        Returns:
            Number of records deleted
        """
        count = self.db.query(QuestionnaireCompletion).filter(
            QuestionnaireCompletion.user_id == user_id,
            QuestionnaireCompletion.completion_date == completion_date
        ).delete(synchronize_session=False)
        return count