"""Service for questionnaire operations"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.core.resource_loader import ResourceLoader
from app.features.auth.domain import User
from app.features.auth.repository import UserRepository
from app.shared.questionnaire.repositories import QuestionnaireCompletionRepository
from app.shared.constants import QUESTIONNAIRE_IDS


class QuestionnaireService:
    """Service for questionnaire operations and eligibility"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.completion_repo = QuestionnaireCompletionRepository(db)
        self.resource_loader = ResourceLoader()

    def get_next_questionnaire(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the next eligible questionnaire for a user with their existing answers.
        Returns None if no questionnaires are available.

        Args:
            user_id: User ID

        Returns:
            Questionnaire dict with user's answers merged in, or None
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check onboarding first (priority questionnaire)
        if not self.completion_repo.is_completed(user_id, QUESTIONNAIRE_IDS["ONBOARDING"]):
            return self.get_questionnaire_with_answers(user_id, QUESTIONNAIRE_IDS["ONBOARDING"])

        # Future: Add logic for daily, biweekly questionnaires
        # if self._is_daily_due(user_id):
        #     return self.get_questionnaire_with_answers(user_id, QUESTIONNAIRE_IDS["DAILY"])

        return None

    def get_questionnaire_with_answers(
        self, user_id: int, questionnaire_id: str
    ) -> Dict[str, Any]:
        """
        Load a questionnaire and merge with user's existing answers.

        Args:
            user_id: User ID
            questionnaire_id: Questionnaire identifier

        Returns:
            Questionnaire with user answers merged into questions

        Raises:
            ValueError: If questionnaire not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Load questionnaire from YAML
        try:
            questionnaire_data = self.resource_loader.load_questionnaire(questionnaire_id)
        except FileNotFoundError:
            raise ValueError(f"Questionnaire '{questionnaire_id}' not found")

        # Ensure questionnaire is assigned (tracked)
        self.completion_repo.assign_questionnaire(user_id, questionnaire_id)

        # Extract user's existing answers from database
        user_answers = self._extract_user_answers(user, questionnaire_id)

        # Merge answers into questionnaire questions
        questionnaire_with_answers = self._merge_answers_into_questionnaire(
            questionnaire_data, user_answers
        )

        return questionnaire_with_answers

    def _extract_user_answers(self, user: User, questionnaire_id: str) -> Dict[str, Any]:
        """
        Extract user's existing answers from database based on questionnaire type.

        Args:
            user: User entity
            questionnaire_id: Questionnaire identifier

        Returns:
            Dictionary of question_id -> answer
        """
        answers = {}

        if questionnaire_id == QUESTIONNAIRE_IDS["ONBOARDING"]:
            # Extract from user profile
            if user.full_name:
                answers["name"] = user.full_name
            if user.age is not None:
                answers["age"] = user.age
            if user.gender:
                answers["gender"] = user.gender

            # Extract from user settings
            if user.settings:
                if user.settings.daily_routine:
                    answers["daily-routine-or-main-activity"] = user.settings.daily_routine
                if user.settings.ethnicity:
                    answers["ethnicity"] = user.settings.ethnicity
                if user.settings.hispanic_latino:
                    answers["ethnicity-hispanic-latino"] = user.settings.hispanic_latino
                if user.settings.allow_medical_support is not None:
                    answers["allow-support-for-other-condition"] = user.settings.allow_medical_support

            # Extract from user conditions
            if user.conditions:
                condition_codes = [c.condition_code for c in user.conditions]
                if condition_codes:
                    answers["conditions"] = condition_codes

                # Extract condition-specific fields
                for condition in user.conditions:
                    if condition.diagnosed_by_physician is not None:
                        answers["comorbidity-condition-diagnosed-by-physician"] = condition.diagnosed_by_physician
                    if condition.duration:
                        answers["comorbidity-condition-experienced-for"] = condition.duration
                    if condition.physician_frequency:
                        answers["comorbidity-do-you-see-physician"] = condition.physician_frequency

                    # Diabetes-specific
                    if condition.condition_code == "73211009":
                        if condition.diabetes_type:
                            answers["which-type-of-diabetes"] = condition.diabetes_type
                        if condition.therapy_type:
                            answers["what-is-your-diabetes-therapy"] = [condition.therapy_type]
                        if condition.wants_glucose_reminders is not None:
                            answers["reminder-to-check-blood-glucose"] = (
                                "yes-remind-me" if condition.wants_glucose_reminders else "no-thanks"
                            )

                    # Pain-specific
                    if condition.condition_code == "82423001":
                        if condition.pain_type:
                            answers["how-would-you-describe-your-pain"] = condition.pain_type

            # Extract from reminders
            if user.reminders:
                for reminder in user.reminders:
                    if reminder.reminder_type == "daily_check_in":
                        answers["notification-time"] = reminder.time.strftime("%H:%M")
                    elif reminder.reminder_type == "glucose_check":
                        if "glucose-check-reminders" not in answers:
                            answers["glucose-check-reminders"] = []
                        answers["glucose-check-reminders"].append(reminder.time.strftime("%H:%M"))

        return answers

    def _merge_answers_into_questionnaire(
        self, questionnaire_data: Dict[str, Any], user_answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge user answers into questionnaire questions.

        Args:
            questionnaire_data: Raw questionnaire data from YAML
            user_answers: User's existing answers

        Returns:
            Questionnaire with 'answer' field added to each question
        """
        result = questionnaire_data.copy()

        # Add answers to each question
        if "questions" in result:
            for question in result["questions"]:
                question_id = question.get("id")
                if question_id and question_id in user_answers:
                    question["answer"] = user_answers[question_id]
                else:
                    question["answer"] = None

        return result