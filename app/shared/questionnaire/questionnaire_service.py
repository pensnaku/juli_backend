"""Service for questionnaire operations"""

import copy
from typing import Optional, Dict, Any, List
from datetime import date
from sqlalchemy.orm import Session

from app.core.resource_loader import ResourceLoader
from app.features.auth.domain import User
from app.features.auth.repository import UserRepository, UserMedicationRepository
from app.features.observations.repository import ObservationRepository
from app.shared.questionnaire.repositories import QuestionnaireCompletionRepository
from app.shared.constants import (
    QUESTIONNAIRE_IDS,
    DAILY_QUESTIONNAIRE_MAP,
    DAILY_ROUTINE_STUDENT,
)


class QuestionnaireService:
    """Service for questionnaire operations and eligibility"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.completion_repo = QuestionnaireCompletionRepository(db)
        self.medication_repo = UserMedicationRepository(db)
        self.observation_repo = ObservationRepository(db)
        self.resource_loader = ResourceLoader()

    def get_next_questionnaire(
        self, user_id: int, target_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the next eligible questionnaire for a user with their existing answers.
        Returns None if no questionnaires are available.

        Args:
            user_id: User ID
            target_date: Date for daily questionnaires (defaults to today)

        Returns:
            Questionnaire dict with user's answers merged in, or None
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check onboarding first (priority questionnaire)
        if not self.completion_repo.is_completed(
            user_id, QUESTIONNAIRE_IDS["ONBOARDING"]
        ):
            return self.get_questionnaire_with_answers(
                user_id, QUESTIONNAIRE_IDS["ONBOARDING"]
            )

        # Return daily questionnaires for the specified date
        questionnaire_date = target_date or date.today()
        return self.get_daily_questionnaires(user_id, questionnaire_date)

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
            questionnaire_data = self.resource_loader.load_questionnaire(
                questionnaire_id
            )
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

    def _extract_user_answers(
        self, user: User, questionnaire_id: str
    ) -> Dict[str, Any]:
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
                    answers["daily-routine-or-main-activity"] = (
                        user.settings.daily_routine
                    )
                if user.settings.ethnicity:
                    answers["ethnicity"] = user.settings.ethnicity
                if user.settings.hispanic_latino:
                    answers["ethnicity-hispanic-latino"] = user.settings.hispanic_latino
                if user.settings.allow_medical_support is not None:
                    answers["allow-support-for-other-condition"] = (
                        user.settings.allow_medical_support
                    )

            # Extract from user conditions (ordered by priority)
            if user.conditions:
                from app.shared.condition_utils import order_leading_conditions

                condition_codes = [c.condition_code for c in user.conditions]
                if condition_codes:
                    # Order condition codes by priority
                    answers["conditions"] = order_leading_conditions(condition_codes)

                # Extract condition-specific fields
                for condition in user.conditions:
                    if condition.diagnosed_by_physician is not None:
                        answers["comorbidity-condition-diagnosed-by-physician"] = (
                            condition.diagnosed_by_physician
                        )
                    if condition.duration:
                        answers["comorbidity-condition-experienced-for"] = (
                            condition.duration
                        )
                    if condition.physician_frequency:
                        answers["comorbidity-do-you-see-physician"] = (
                            condition.physician_frequency
                        )

                    # Diabetes-specific
                    if condition.condition_code == "73211009":
                        if condition.diabetes_type:
                            answers["which-type-of-diabetes"] = condition.diabetes_type
                        if condition.therapy_type:
                            answers["what-is-your-diabetes-therapy"] = [
                                condition.therapy_type
                            ]
                        if condition.wants_glucose_reminders is not None:
                            answers["reminder-to-check-blood-glucose"] = (
                                "yes-remind-me"
                                if condition.wants_glucose_reminders
                                else "no-thanks"
                            )

                    # Pain-specific
                    if condition.condition_code == "82423001":
                        if condition.pain_type:
                            answers["how-would-you-describe-your-pain"] = (
                                condition.pain_type
                            )

            # Extract from reminders
            if user.reminders:
                for reminder in user.reminders:
                    if reminder.reminder_type == "daily_check_in":
                        answers["notification-time"] = reminder.time.strftime("%H:%M")
                    elif reminder.reminder_type == "glucose_check":
                        if "glucose-check-reminders" not in answers:
                            answers["glucose-check-reminders"] = []
                        answers["glucose-check-reminders"].append(
                            reminder.time.strftime("%H:%M")
                        )

            # Extract medications (read-only, managed via /medications endpoints)
            medications = self.medication_repo.get_by_user_id(user.id, active_only=True)
            if medications:
                answers["medications-notifications"] = [
                    {
                        "id": med.id,
                        "medication_name": med.medication_name,
                        "dosage": med.dosage,
                        "times_per_day": med.times_per_day,
                        "notes": med.notes,
                        "reminder_enabled": med.reminder_enabled,
                        "notification_times": (
                            [
                                r.time.strftime("%H:%M")
                                for r in med.reminders
                                if r.is_active
                            ]
                            if med.reminders
                            else []
                        ),
                    }
                    for med in medications
                ]

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

    # ========== Daily Questionnaire Methods ==========

    # TEST MODE: Return ALL questionnaires regardless of user conditions
    TEST_MODE_ALL_QUESTIONNAIRES = False

    def get_daily_questionnaires(
        self, user_id: int, target_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Get daily questionnaires for a user.
        Always includes mood questionnaire first, then condition-specific questionnaires.

        Args:
            user_id: User ID
            target_date: The date for the questionnaires

        Returns:
            Dictionary with questionnaires array, or None if no questionnaires available
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        questionnaires = []

        # Always include mood questionnaire first (for all users)
        mood_questionnaire = self._build_mood_questionnaire(user_id, target_date)
        if mood_questionnaire:
            questionnaires.append(mood_questionnaire)

        # Add student wellbeing questionnaire after mood if user is a student
        if user.settings and user.settings.daily_routine == DAILY_ROUTINE_STUDENT:
            student_questionnaire = self._build_daily_questionnaire(
                user_id=user_id,
                condition_key="student_wellbeing",
                target_date=target_date,
            )
            if student_questionnaire:
                questionnaires.append(student_questionnaire)

        # TEST MODE: Return ALL available questionnaires (excluding mood and student_wellbeing already added)
        if self.TEST_MODE_ALL_QUESTIONNAIRES:
            all_condition_keys = [
                "asthma",
                "anxiety",
                "bipolar",
                "chronic_pain",
                "copd",
                "depression",
                "diabetes",
                "dry_eye",
                "headache",
                "hypertension",
                "migraine",
                "wellbeing",
            ]

            for condition_key in all_condition_keys:
                questionnaire = self._build_daily_questionnaire(
                    user_id=user_id,
                    condition_key=condition_key,
                    target_date=target_date,
                )
                if questionnaire:
                    questionnaires.append(questionnaire)
        else:
            # Normal mode: Only user's conditions (ordered by priority)
            # Exclude mood and student_wellbeing as they're already added above
            if user.conditions:
                # Use ordered_conditions to ensure questionnaires appear in priority order
                ordered = (
                    user.ordered_conditions
                    if hasattr(user, "ordered_conditions")
                    else user.conditions
                )
                for condition in ordered:
                    condition_code = condition.condition_code

                    # Get questionnaire filename for this condition
                    condition_key = DAILY_QUESTIONNAIRE_MAP.get(condition_code)
                    if not condition_key:
                        continue

                    # Skip mood, student_wellbeing, and journal as they're already added
                    if condition_key in ["mood", "student_wellbeing", "journal"]:
                        continue

                    questionnaire = self._build_daily_questionnaire(
                        user_id=user_id,
                        condition_key=condition_key,
                        target_date=target_date,
                    )
                    if questionnaire:
                        questionnaires.append(questionnaire)

        # Add journal questionnaire at the end (for all users)
        journal_questionnaire = self._build_daily_questionnaire(
            user_id=user_id,
            condition_key="journal",
            target_date=target_date,
        )
        if journal_questionnaire:
            questionnaires.append(journal_questionnaire)

        # Add individual tracking questionnaire if user has active tracking topics
        tracking_questionnaire = self._build_individual_tracking_questionnaire(
            user_id, target_date
        )
        if tracking_questionnaire:
            questionnaires.append(tracking_questionnaire)

        if not questionnaires:
            return None

        return {
            "title": "Daily Check-in",
            "description": "Your daily health questions",
            "completion_date": target_date.isoformat(),
            "questionnaires": questionnaires,
        }

    def _build_mood_questionnaire(
        self, user_id: int, target_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Build the mood questionnaire (shown to all users daily).

        Args:
            user_id: User ID
            target_date: The date for the questionnaire

        Returns:
            Mood questionnaire dict, or None if file not found
        """
        try:
            questionnaire_data = self.resource_loader.load_daily_questionnaire("mood")
        except FileNotFoundError:
            return None

        questionnaire_id = questionnaire_data.get("questionnaire_id", "daily-mood")

        # Get existing answers for this questionnaire and date
        user_answers = self._extract_daily_answers(
            user_id, questionnaire_id, target_date
        )

        # Merge answers into questions (deep copy to avoid mutating original)
        questions = copy.deepcopy(questionnaire_data.get("questions", []))
        for question in questions:
            question_id = question.get("id")
            question["answer"] = user_answers.get(question_id)

        # Check completion status from database
        is_completed = self.completion_repo.is_condition_completed_for_date(
            user_id, questionnaire_id, target_date
        )

        return {
            "questionnaire_id": questionnaire_id,
            "questions": questions,
            "is_completed": is_completed,
        }

    def _build_individual_tracking_questionnaire(
        self, user_id: int, target_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Build the individual tracking questionnaire from user's active tracking topics.

        Dynamically generates questions based on user's active tracking topics.
        Observations are stored with code='individual-tracking' and variant=topic_code.

        Args:
            user_id: User ID
            target_date: The date for the questionnaire

        Returns:
            Individual tracking questionnaire dict, or None if user has no active topics
        """
        from app.features.auth.repository import UserTrackingTopicRepository

        tracking_repo = UserTrackingTopicRepository(self.db)
        active_topics = tracking_repo.get_by_user_id(user_id, active_only=True)

        if not active_topics:
            return None

        questionnaire_id = "daily-individual-tracking"

        # Get existing answers for this questionnaire and date
        user_answers = self._extract_daily_answers(
            user_id, questionnaire_id, target_date
        )

        # Build questions from active tracking topics
        questions = []
        for topic in active_topics:
            question_data = {
                "id": topic.topic_code,  # e.g., "coffee-consumption" or "water-intake-a3b9f2"
                "text": topic.question,
                "required": False,
            }

            # Add emoji if available
            if topic.emoji:
                question_data["emoji"] = topic.emoji

            # Set question type and relevant fields based on data type
            if topic.data_type == "number":
                # Use 'number' type for numeric inputs (matches daily questionnaires)
                question_data["type"] = "number"
                if topic.unit:
                    question_data["unit"] = topic.unit
                # Add range if min or max values are specified
                if topic.min_value is not None or topic.max_value is not None:
                    question_data["range"] = {}
                    if topic.min_value is not None:
                        question_data["range"]["min"] = topic.min_value
                    if topic.max_value is not None:
                        question_data["range"]["max"] = topic.max_value
            elif topic.data_type == "boolean":
                # Use 'boolean' type for yes/no questions (matches daily questionnaires)
                question_data["type"] = "boolean"
            else:
                # Default to number type
                question_data["type"] = "number"

            # Add existing answer if available
            question_data["answer"] = user_answers.get(topic.topic_code)

            questions.append(question_data)

        # Check completion status
        is_completed = self.completion_repo.is_condition_completed_for_date(
            user_id, questionnaire_id, target_date
        )

        return {
            "questionnaire_id": questionnaire_id,
            "questions": questions,
            "is_completed": is_completed,
        }

    def _build_daily_questionnaire(
        self,
        user_id: int,
        condition_key: str,
        target_date: date,
    ) -> Optional[Dict[str, Any]]:
        """
        Build a single daily questionnaire item.

        Args:
            user_id: User ID
            condition_key: Condition filename key (e.g., 'asthma')
            target_date: The date for the questionnaire

        Returns:
            Questionnaire item dict, or None if questionnaire file not found
        """
        try:
            questionnaire_data = self.resource_loader.load_daily_questionnaire(
                condition_key
            )
        except FileNotFoundError:
            return None

        questionnaire_id = questionnaire_data.get(
            "questionnaire_id", f"daily-{condition_key}"
        )

        # Get existing answers for this questionnaire and date
        user_answers = self._extract_daily_answers(
            user_id, questionnaire_id, target_date
        )

        # Merge answers into questions
        questions = questionnaire_data.get("questions", [])
        for question in questions:
            question_id = question.get("id")
            question["answer"] = user_answers.get(question_id)

        # Check completion status from database
        is_completed = self.completion_repo.is_condition_completed_for_date(
            user_id, questionnaire_id, target_date
        )

        return {
            "questionnaire_id": questionnaire_id,
            "questions": questions,
            "is_completed": is_completed,
        }

    def _extract_daily_answers(
        self, user_id: int, questionnaire_id: str, target_date: date
    ) -> Dict[str, Any]:
        """
        Extract user's daily answers from observations for a specific questionnaire and date.

        Reconstructs multi-value answers (e.g., mood-energy) from multiple observations
        with variants into a single dictionary answer.

        Special handling for individual-tracking questionnaire:
        - Observations are stored with code="individual-tracking" and variant=topic_code
        - Returns dict of topic_code -> answer

        Args:
            user_id: User ID
            questionnaire_id: Questionnaire ID (e.g., "daily-asthma")
            target_date: The date to get answers for

        Returns:
            Dictionary of question_id -> answer
            - Single-value: {"mood": 4}
            - Multi-value: {"mood-energy": {"mood": 4, "energy": 7}}
            - Individual tracking: {"coffee-consumption": 3, "water-intake-a3b9f2": 8}
        """
        from datetime import datetime, timezone
        from collections import defaultdict

        # Create datetime range for the target date (midnight to midnight)
        start_datetime = datetime.combine(
            target_date, datetime.min.time(), tzinfo=timezone.utc
        )
        end_datetime = datetime.combine(
            target_date, datetime.max.time(), tzinfo=timezone.utc
        )

        # Query observations by data_source (questionnaire_id)
        observations, _ = self.observation_repo.get_by_user_paginated(
            user_id=user_id,
            data_source=questionnaire_id,
            start_date=start_datetime,
            end_date=end_datetime,
            page=1,
            page_size=100,
        )

        # Special handling for individual tracking questionnaire
        if questionnaire_id == "daily-individual-tracking":
            # For individual tracking, observations have code="individual-tracking"
            # and variant=topic_code, so we return variant -> value mapping
            answers = {}
            for obs in observations:
                if obs.code == "individual-tracking" and obs.variant:
                    answers[obs.variant] = self._extract_observation_value(obs)
            return answers

        # Group observations by code (question_id)
        observations_by_code = defaultdict(list)
        for obs in observations:
            observations_by_code[obs.code].append(obs)

        answers = {}

        # Reconstruct answers
        for question_id, obs_list in observations_by_code.items():
            if len(obs_list) == 1 and obs_list[0].variant is None:
                # Single-value answer
                obs = obs_list[0]
                answers[question_id] = self._extract_observation_value(obs)
            else:
                # Multi-value answer - reconstruct as dict
                multi_value = {}
                for obs in obs_list:
                    variant = obs.variant or "value"
                    multi_value[variant] = self._extract_observation_value(obs)
                answers[question_id] = multi_value

        return answers

    def _extract_observation_value(self, obs: Any) -> Any:
        """
        Extract the value from an observation based on which value field is populated.

        Args:
            obs: Observation entity

        Returns:
            The observation value (int, float, str, or bool)
        """
        if obs.value_boolean is not None:
            return obs.value_boolean
        elif obs.value_integer is not None:
            return obs.value_integer
        elif obs.value_decimal is not None:
            return float(obs.value_decimal)
        elif obs.value_string is not None:
            return obs.value_string
        return None
