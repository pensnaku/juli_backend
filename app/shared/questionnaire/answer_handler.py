"""Service to handle questionnaire answers and save to database"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import time as time_type
from sqlalchemy.orm import Session

from app.features.auth.repository import (
    UserRepository,
    UserConditionRepository,
    UserReminderRepository,
)
from app.features.auth.domain import User, UserSettings
from app.features.auth.domain.schemas import (
    UserConditionCreate,
    UserReminderCreate,
)
from app.shared.constants import CONDITION_CODES
from app.shared.questionnaire.repositories import QuestionnaireCompletionRepository


class QuestionnaireAnswerHandler:
    """
    Maps questionnaire answers to domain entities and handles database persistence.
    Each question ID is mapped to the appropriate database table/field.
    """

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.condition_repo = UserConditionRepository(db)
        self.reminder_repo = UserReminderRepository(db)
        self.completion_repo = QuestionnaireCompletionRepository(db)

    def save_answers(
        self, user_id: int, questionnaire_id: str, answers: Dict[str, Any], mark_completed: bool = False
    ) -> Tuple[int, bool]:
        """
        Process and save questionnaire answers for a user.
        Supports partial submissions - only updates provided answers.

        Args:
            user_id: The user ID to save answers for
            questionnaire_id: The questionnaire identifier (e.g., 'onboarding', 'daily')
            answers: Dictionary of question_id -> answer pairs
            mark_completed: If True, mark the questionnaire as completed

        Returns:
            Tuple of (answers_count, is_completed)
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Ensure user has settings
        if not user.settings:
            user.settings = UserSettings(user_id=user_id)
            self.db.add(user.settings)
            self.db.flush()

        # Ensure questionnaire completion tracking exists (assign if not)
        completion = self.completion_repo.get_by_user_and_questionnaire(user_id, questionnaire_id)
        if not completion:
            completion = self.completion_repo.assign_questionnaire(user_id, questionnaire_id)

        # Process each answer based on question ID
        for question_id, answer in answers.items():
            self._process_answer(user, question_id, answer)

        # Mark as completed if requested
        if mark_completed and not completion.is_completed:
            self.completion_repo.mark_completed(user_id, questionnaire_id)

        # Commit all changes
        self.db.commit()

        # Return count of answers processed and completion status
        is_completed = self.completion_repo.is_completed(user_id, questionnaire_id)
        return len(answers), is_completed

    def _process_answer(self, user: User, question_id: str, answer: Any) -> None:
        """Route answer to appropriate handler based on question ID"""

        # User profile fields
        if question_id == "name":
            user.full_name = answer
        elif question_id == "age":
            user.age = int(answer) if answer else None
        elif question_id == "gender":
            user.gender = answer

        # User settings fields
        elif question_id == "daily-routine-or-main-activity":
            user.settings.daily_routine = answer
        elif question_id == "ethnicity":
            user.settings.ethnicity = answer
        elif question_id == "ethnicity-hispanic-latino":
            user.settings.hispanic_latino = answer
        elif question_id == "allow-support-for-other-condition":
            user.settings.allow_medical_support = self._parse_boolean(answer)

        # Conditions (creates/updates condition records)
        elif question_id == "conditions":
            self._handle_conditions(user.id, answer)

        # Common condition fields
        elif question_id == "comorbidity-condition-diagnosed-by-physician":
            self._update_all_conditions(user.id, "diagnosed_by_physician", self._parse_boolean(answer))
        elif question_id == "comorbidity-condition-experienced-for":
            self._update_all_conditions(user.id, "duration", answer)
        elif question_id == "comorbidity-do-you-see-physician":
            self._update_all_conditions(user.id, "physician_frequency", answer)

        # Diabetes-specific fields
        elif question_id == "which-type-of-diabetes":
            self._update_condition_field(user.id, "73211009", "diabetes_type", answer)
        elif question_id == "what-is-your-diabetes-therapy":
            self._handle_diabetes_therapy(user.id, answer)
        elif question_id == "reminder-to-check-blood-glucose":
            wants_reminders = answer == "yes-remind-me"
            self._update_condition_field(user.id, "73211009", "wants_glucose_reminders", wants_reminders)

        # Pain-specific fields
        elif question_id == "how-would-you-describe-your-pain":
            self._update_condition_field(user.id, "82423001", "pain_type", answer)

        # Reminders
        elif question_id == "notification-time":
            self._handle_daily_reminder(user.id, answer)
        elif question_id == "glucose-check-reminders":
            self._handle_glucose_reminders(user.id, answer)

    def _handle_conditions(self, user_id: int, condition_codes: List[str]) -> None:
        """Create or update user conditions from selected condition codes"""
        if not isinstance(condition_codes, list):
            condition_codes = [condition_codes]

        for code in condition_codes:
            if code in CONDITION_CODES:
                condition_info = CONDITION_CODES[code]
                condition_data = UserConditionCreate(
                    condition_code=code,
                    condition_label=condition_info["label"],
                    condition_system=condition_info["system"],
                )
                self.condition_repo.upsert(user_id, condition_data)

    def _update_condition_field(
        self, user_id: int, condition_code: str, field: str, value: Any
    ) -> None:
        """Update a specific field for a specific condition"""
        condition = self.condition_repo.get_by_user_and_condition(user_id, condition_code)
        if condition:
            setattr(condition, field, value)

    def _update_all_conditions(self, user_id: int, field: str, value: Any) -> None:
        """Update a field for all user conditions (common fields)"""
        conditions = self.condition_repo.get_by_user_id(user_id)
        for condition in conditions:
            setattr(condition, field, value)

    def _handle_diabetes_therapy(self, user_id: int, therapy: Any) -> None:
        """Handle diabetes therapy - store first/primary therapy"""
        if isinstance(therapy, list) and therapy:
            primary_therapy = therapy[0]
        else:
            primary_therapy = therapy

        self._update_condition_field(user_id, "73211009", "therapy_type", primary_therapy)

    def _handle_daily_reminder(self, user_id: int, time_str: str) -> None:
        """Create/update daily check-in reminder"""
        if not time_str:
            return

        reminder_time = self._parse_time(time_str)
        if reminder_time:
            # Replace existing daily reminders with new one
            reminder_data = UserReminderCreate(
                reminder_type="daily_check_in",
                time=reminder_time,
                is_active=True,
            )
            self.reminder_repo.replace_reminders_by_type(
                user_id, "daily_check_in", [reminder_data]
            )

    def _handle_glucose_reminders(self, user_id: int, times: List[str]) -> None:
        """Create/update glucose check reminders"""
        if not times or not isinstance(times, list):
            return

        reminder_data_list = []
        for time_str in times:
            reminder_time = self._parse_time(time_str)
            if reminder_time:
                reminder_data_list.append(
                    UserReminderCreate(
                        reminder_type="glucose_check",
                        time=reminder_time,
                        is_active=True,
                    )
                )

        if reminder_data_list:
            # Replace existing glucose reminders with new ones
            self.reminder_repo.replace_reminders_by_type(
                user_id, "glucose_check", reminder_data_list
            )

    @staticmethod
    def _parse_time(time_str: str) -> Optional[time_type]:
        """Parse time string in HH:MM format to time object"""
        if not time_str:
            return None
        try:
            # Handle both "HH:MM" and "HH:MM:SS" formats
            parts = time_str.split(":")
            if len(parts) == 2:
                hour, minute = int(parts[0]), int(parts[1])
                return time_type(hour, minute)
            elif len(parts) == 3:
                hour, minute, second = int(parts[0]), int(parts[1]), int(parts[2])
                return time_type(hour, minute, second)
        except (ValueError, AttributeError):
            return None
        return None

    @staticmethod
    def _parse_boolean(value: Any) -> bool:
        """Parse various boolean representations"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "y")
        return bool(value)