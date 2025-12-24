"""Service to handle questionnaire answers and save to database"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import time as time_type, date, datetime, timezone
from sqlalchemy.orm import Session

from app.features.auth.repository import (
    UserRepository,
    UserConditionRepository,
    UserReminderRepository,
    UserTrackingTopicRepository,
)
from app.features.auth.domain import User, UserSettings
from app.features.auth.domain.schemas import (
    UserConditionCreate,
    UserReminderCreate,
)
from app.features.observations.repository import ObservationRepository
from app.shared.constants import (
    CONDITION_CODES,
    TRACKING_TOPICS,
    DAILY_QUESTIONNAIRE_CONDITION_MAP,
)
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
        self.tracking_topic_repo = UserTrackingTopicRepository(db)
        self.completion_repo = QuestionnaireCompletionRepository(db)
        self.observation_repo = ObservationRepository(db)

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
        """Route answer to appropriate handler based on question ID.

        When answer is None, the field is cleared/invalidated (for dependent questions).
        """

        # User profile fields
        if question_id == "name":
            user.full_name = answer  # None clears the field
        elif question_id == "age":
            user.age = int(answer) if answer else None
        elif question_id == "gender":
            if answer is None:
                user.gender = None
            elif isinstance(answer, list):
                user.gender = answer[0] if answer else None
            else:
                user.gender = answer

        # User settings fields
        elif question_id == "daily-routine-or-main-activity":
            if answer is None:
                user.settings.daily_routine = None
            elif isinstance(answer, list):
                user.settings.daily_routine = answer[0] if answer else None
            else:
                user.settings.daily_routine = answer
        elif question_id == "ethnicity":
            if answer is None:
                user.settings.ethnicity = None
            elif isinstance(answer, list):
                user.settings.ethnicity = answer[0] if answer else None
            else:
                user.settings.ethnicity = answer
        elif question_id == "ethnicity-hispanic-latino":
            if answer is None:
                user.settings.hispanic_latino = None
            elif isinstance(answer, list):
                user.settings.hispanic_latino = answer[0] if answer else None
            else:
                user.settings.hispanic_latino = answer
        elif question_id == "allow-support-for-other-condition":
            if answer is None:
                user.settings.allow_medical_support = None
            else:
                user.settings.allow_medical_support = self._parse_boolean(answer)

        # Conditions (creates/updates condition records)
        elif question_id == "conditions":
            self._handle_conditions(user.id, answer)

        # Common condition fields
        elif question_id == "comorbidity-condition-diagnosed-by-physician":
            if answer is None:
                self._update_all_conditions(user.id, "diagnosed_by_physician", None)
            else:
                self._update_all_conditions(user.id, "diagnosed_by_physician", self._parse_boolean(answer))
        elif question_id == "comorbidity-condition-experienced-for":
            if answer is None:
                self._update_all_conditions(user.id, "duration", None)
            else:
                value = answer[0] if isinstance(answer, list) and answer else answer
                self._update_all_conditions(user.id, "duration", value)
        elif question_id == "comorbidity-do-you-see-physician":
            if answer is None:
                self._update_all_conditions(user.id, "physician_frequency", None)
            else:
                value = answer[0] if isinstance(answer, list) and answer else answer
                self._update_all_conditions(user.id, "physician_frequency", value)

        # Diabetes-specific fields
        elif question_id == "which-type-of-diabetes":
            if answer is None:
                self._update_condition_field(user.id, "73211009", "diabetes_type", None)
            else:
                value = answer[0] if isinstance(answer, list) and answer else answer
                self._update_condition_field(user.id, "73211009", "diabetes_type", value)
        elif question_id == "what-is-your-diabetes-therapy":
            self._handle_diabetes_therapy(user.id, answer)
        elif question_id == "reminder-to-check-blood-glucose":
            if answer is None:
                self._update_condition_field(user.id, "73211009", "wants_glucose_reminders", None)
            else:
                check_value = answer[0] if isinstance(answer, list) and answer else answer
                wants_reminders = check_value == "yes-remind-me"
                self._update_condition_field(user.id, "73211009", "wants_glucose_reminders", wants_reminders)

        # Pain-specific fields
        elif question_id == "how-would-you-describe-your-pain":
            if answer is None:
                self._update_condition_field(user.id, "82423001", "pain_type", None)
            else:
                value = answer[0] if isinstance(answer, list) and answer else answer
                self._update_condition_field(user.id, "82423001", "pain_type", value)

        # Reminders
        elif question_id == "notification-time":
            self._handle_daily_reminder(user.id, answer)
        elif question_id == "glucose-check-reminders":
            self._handle_glucose_reminders(user.id, answer)

        # Medication questions
        elif question_id == "do-you-take-medication":
            if answer is None:
                user.settings.takes_medication = None
            else:
                value = answer[0] if isinstance(answer, list) and answer else answer
                user.settings.takes_medication = self._parse_boolean(value)
        elif question_id == "medication-reminder":
            if answer is None:
                user.settings.wants_medication_reminders = None
            else:
                value = answer[0] if isinstance(answer, list) and answer else answer
                user.settings.wants_medication_reminders = self._parse_boolean(value)
        elif question_id == "medications-notifications":
            # Medications are managed via /medications endpoints, not here
            # This is read-only in the questionnaire - skip processing
            pass

        # Tracking questions
        elif question_id == "track-additional-topics":
            if answer is None:
                user.settings.wants_additional_tracking = None
            else:
                value = answer[0] if isinstance(answer, list) and answer else answer
                user.settings.wants_additional_tracking = self._parse_boolean(value)
        elif question_id == "tracking-symptoms":
            self._handle_tracking_topics(user.id, answer)

    def _handle_conditions(self, user_id: int, condition_codes: List[str]) -> None:
        """Create or update user conditions from selected condition codes.

        If condition_codes is None or empty, deletes all user conditions.
        """
        if condition_codes is None or (isinstance(condition_codes, list) and len(condition_codes) == 0):
            # Clear all conditions
            self.condition_repo.delete_all_by_user_id(user_id)
            return

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
        """Handle diabetes therapy - store first/primary therapy.

        If therapy is None, clears the therapy_type field.
        """
        if therapy is None:
            self._update_condition_field(user_id, "73211009", "therapy_type", None)
            return

        if isinstance(therapy, list) and therapy:
            primary_therapy = therapy[0]
        else:
            primary_therapy = therapy

        self._update_condition_field(user_id, "73211009", "therapy_type", primary_therapy)

    def _handle_daily_reminder(self, user_id: int, time_str: str) -> None:
        """Create/update daily check-in reminder.

        If time_str is None, deletes all daily check-in reminders.
        """
        if time_str is None:
            # Clear all daily check-in reminders
            self.reminder_repo.replace_reminders_by_type(user_id, "daily_check_in", [])
            return

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
        """Create/update glucose check reminders.

        If times is None, deletes all glucose check reminders.
        """
        if times is None:
            # Clear all glucose check reminders
            self.reminder_repo.replace_reminders_by_type(user_id, "glucose_check", [])
            return

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

    def _handle_tracking_topics(self, user_id: int, topic_codes: List[str]) -> None:
        """Create/update user tracking topics.

        If topic_codes is None, deactivates all tracking topics.
        """
        if topic_codes is None:
            # Clear/deactivate all tracking topics
            existing_topics = self.tracking_topic_repo.get_by_user_id(user_id, active_only=False)
            for topic in existing_topics:
                topic.is_active = False
            return

        if not topic_codes or not isinstance(topic_codes, list):
            return

        # Filter out the "nothing-from-the-list" option
        topic_codes = [code for code in topic_codes if code != "nothing-from-the-list"]

        if not topic_codes:
            # User selected "nothing from the list" - deactivate all topics
            existing_topics = self.tracking_topic_repo.get_by_user_id(user_id, active_only=False)
            for topic in existing_topics:
                topic.is_active = False
            return

        # Build list of (topic_code, topic_label) tuples
        topics = []
        for code in topic_codes:
            topic_info = TRACKING_TOPICS.get(code)
            label = topic_info["label"] if topic_info else code.replace("-", " ").title()
            topics.append((code, label))

        # Replace all topics for user
        self.tracking_topic_repo.replace_all(user_id, topics)

    @staticmethod
    def _parse_boolean(value: Any) -> bool:
        """Parse various boolean representations"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "y")
        return bool(value)

    # ========== Daily Questionnaire Answer Methods ==========

    def save_single_answer(
        self,
        user_id: int,
        completion_date: date,
        question_id: str,
        answer: Any,
        questionnaire_id: str,
        mark_completed: bool = False,
    ) -> Dict[str, Any]:
        """
        Save a single daily questionnaire answer.

        Args:
            user_id: The user ID
            completion_date: The date for this questionnaire
            question_id: The question being answered
            answer: The answer value (number, boolean, string)
            questionnaire_id: Which questionnaire this belongs to (e.g., 'daily-asthma')
            mark_completed: If True, mark the questionnaire as completed

        Returns:
            Dict with question_id, questionnaire_id, and completed status
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get or create questionnaire completion record
        completion = self.completion_repo.get_by_user_questionnaire_date(
            user_id, questionnaire_id, completion_date
        )
        if not completion:
            completion = self.completion_repo.assign_questionnaire_for_date(
                user_id, questionnaire_id, completion_date
            )

        # Create effective datetime for observations (midnight of completion date)
        effective_datetime = datetime.combine(
            completion_date,
            datetime.min.time(),
            tzinfo=timezone.utc
        )

        # Determine value type
        value_integer = None
        value_decimal = None
        value_string = None
        value_boolean = None

        if isinstance(answer, bool):
            value_boolean = answer
        elif isinstance(answer, int):
            value_integer = answer
        elif isinstance(answer, float):
            value_decimal = answer
        elif isinstance(answer, str):
            # Try to parse string booleans
            if answer.lower() in ('yes', 'true'):
                value_boolean = True
            elif answer.lower() in ('no', 'false'):
                value_boolean = False
            else:
                value_string = answer

        # Check if observation already exists (upsert logic)
        existing = self.observation_repo.get_by_code_and_time(
            user_id=user_id,
            code=question_id,
            variant=None,
            effective_at=effective_datetime,
        )

        if existing:
            # Update existing observation
            existing.value_integer = value_integer
            existing.value_decimal = value_decimal
            existing.value_string = value_string
            existing.value_boolean = value_boolean
            existing.questionnaire_completion_id = completion.id
            self.observation_repo.update(existing)
        else:
            # Create new observation
            self.observation_repo.create(
                user_id=user_id,
                code=question_id,
                value_integer=value_integer,
                value_decimal=value_decimal,
                value_string=value_string,
                value_boolean=value_boolean,
                effective_at=effective_datetime,
                category="questionnaire",
                data_source=questionnaire_id,
                questionnaire_completion_id=completion.id,
            )

        # Mark questionnaire as completed if requested
        if mark_completed:
            self.completion_repo.mark_condition_completed(
                user_id, questionnaire_id, completion_date
            )

        self.db.commit()

        is_completed = self.completion_repo.is_condition_completed_for_date(
            user_id, questionnaire_id, completion_date
        )

        return {
            "question_id": question_id,
            "questionnaire_id": questionnaire_id,
            "completed": is_completed
        }