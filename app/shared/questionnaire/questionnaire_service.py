"""Service for questionnaire operations"""

import copy
from typing import Optional, Dict, Any, List
from datetime import date, time as dt_time
from sqlalchemy.orm import Session

from app.core.resource_loader import ResourceLoader
from app.features.auth.domain import User
from app.features.auth.repository import UserRepository, UserMedicationRepository
from app.features.observations.repository import ObservationRepository
from app.features.medication.repository import MedicationAdherenceRepository
from app.shared.questionnaire.repositories import QuestionnaireCompletionRepository
from app.shared.constants import (
    QUESTIONNAIRE_IDS,
    DAILY_QUESTIONNAIRE_MAP,
    DAILY_ROUTINE_STUDENT,
    CONDITION_ASSESSMENT_MAP,
    DAILY_QUESTIONNAIRE_MOOD,
    DAILY_QUESTIONNAIRE_JOURNAL,
)
from app.shared.questionnaire.condition_assessment_service import (
    ConditionAssessmentService,
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

        # Add individual tracking questionnaire if user has active tracking topics
        tracking_questionnaire = self._build_individual_tracking_questionnaire(
            user_id, target_date
        )
        if tracking_questionnaire:
            questionnaires.append(tracking_questionnaire)

        # Add medication questionnaire after individual tracking
        medication_questionnaire = self._build_medication_questionnaire(
            user_id, target_date
        )
        if medication_questionnaire:
            questionnaires.append(medication_questionnaire)

        # Add condition assessment questionnaires if due (second to last, ordered by leading conditions)
        assessment_service = ConditionAssessmentService(self.db)
        due_assessments = assessment_service.get_due_questionnaires_for_user(
            user_id, target_date
        )

        # Sort assessments by leading condition order
        if due_assessments and user.conditions:
            from app.shared.condition_utils import order_leading_conditions

            condition_codes = [c.condition_code for c in user.conditions]
            ordered_conditions = order_leading_conditions(condition_codes)

            # Build reverse mapping: questionnaire_key -> condition_code
            questionnaire_to_condition = {}
            for code, keys in CONDITION_ASSESSMENT_MAP.items():
                for key in keys:
                    questionnaire_to_condition[key] = code

            def get_assessment_priority(questionnaire_id: str) -> int:
                key = questionnaire_id.replace("condition-assessment-", "").replace("-", "_")
                condition_code = questionnaire_to_condition.get(key)
                if condition_code in ordered_conditions:
                    return ordered_conditions.index(condition_code)
                return 999  # Unknown conditions go last

            due_assessments = sorted(due_assessments, key=get_assessment_priority)

        for questionnaire_id in due_assessments:
            # questionnaire_id is already in correct format: "condition-assessment-{condition}"
            # Extract the condition key for loading the YAML file (e.g., "depression" from "condition-assessment-depression")
            condition_key = questionnaire_id.replace("condition-assessment-", "").replace("-", "_")
            assessment_q = self._build_condition_assessment(
                user_id, condition_key, questionnaire_id, target_date
            )
            if assessment_q:
                questionnaires.append(assessment_q)

        # Add journal questionnaire at the end (always last for all users)
        journal_questionnaire = self._build_journal_questionnaire(user_id, target_date)
        if journal_questionnaire:
            questionnaires.append(journal_questionnaire)

        if not questionnaires:
            return None

        result = {
            "title": "Daily Check-in",
            "description": "Your daily health questions",
            "completion_date": target_date.isoformat(),
            "questionnaires": questionnaires,
        }

        # Include condition assessment scores completed today
        assessment_scores = self._get_condition_assessment_scores_for_date(
            user_id, target_date
        )
        if assessment_scores:
            result["condition_assessment_scores"] = assessment_scores

        return result

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
            questionnaire_data = self.resource_loader.load_daily_questionnaire(
                DAILY_QUESTIONNAIRE_MOOD
            )
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

    def _build_journal_questionnaire(
        self, user_id: int, target_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Build the journal questionnaire (shown to all users daily, always last).

        Args:
            user_id: User ID
            target_date: The date for the questionnaire

        Returns:
            Journal questionnaire dict, or None if file not found
        """
        try:
            questionnaire_data = self.resource_loader.load_daily_questionnaire(
                DAILY_QUESTIONNAIRE_JOURNAL
            )
        except FileNotFoundError:
            return None

        questionnaire_id = questionnaire_data.get("questionnaire_id", "daily-journal")

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

    def _build_medication_questionnaire(
        self, user_id: int, target_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Build medication adherence questionnaire for user's active medications.

        Loads base question structure from YAML, then generates sub-questions
        for each medication with pending adherence records from yesterday and today.

        Returns None if:
        - User has no active medications
        - No adherence records exist
        - All adherence records have been answered (no not_set status)
        - Questionnaire already completed for target_date

        Args:
            user_id: User ID
            target_date: The date for the questionnaire

        Returns:
            Medication questionnaire dict, or None if no medications to track
        """
        from datetime import timedelta
        from app.features.auth.repository import UserReminderRepository

        # Load base questionnaire from YAML
        questionnaire_data = self.resource_loader.load_questionnaire(
            "daily/medication"
        )
        if not questionnaire_data:
            return None

        base_question = questionnaire_data.get("questions", [{}])[0]
        questionnaire_id = questionnaire_data.get("id", "daily-medication")

        # Check if already completed for today
        if self.completion_repo.is_condition_completed_for_date(
            user_id, questionnaire_id, target_date
        ):
            return None

        # Get user's active medications
        medications = self.medication_repo.get_by_user_id(user_id, active_only=True)
        if not medications:
            return None

        # Create medication lookup map
        medication_map = {med.id: med for med in medications}

        # Get adherence records for yesterday and today
        adherence_repo = MedicationAdherenceRepository(self.db)
        yesterday = target_date - timedelta(days=1)
        adherence_records = adherence_repo.get_by_user_date_range(
            user_id, yesterday, target_date
        )

        if not adherence_records:
            return None

        # Get reminder times for all medications
        reminder_repo = UserReminderRepository(self.db)
        user_reminders = reminder_repo.get_by_user_and_type(user_id, "medication_reminder")
        # Map medication_id -> reminder time (use first reminder if multiple)
        reminder_time_map = {}
        for reminder in user_reminders:
            if reminder.medication_id and reminder.medication_id not in reminder_time_map:
                reminder_time_map[reminder.medication_id] = reminder.time

        # Build medication entries with adherence info
        medication_entries = []
        has_unanswered = False

        for adherence in adherence_records:
            med = medication_map.get(adherence.medication_id)
            if not med:
                continue

            # Get current status - prefill if already answered
            current_value = None
            if adherence.status and adherence.status != "not_set":
                current_value = adherence.status
            else:
                has_unanswered = True

            # Get reminder time for this medication
            reminder_time = reminder_time_map.get(med.id)

            medication_entries.append(
                {
                    "medication_id": med.id,
                    "medication_name": med.medication_name,
                    "dosage": med.dosage,
                    "date": adherence.date.isoformat(),
                    "reminder_time": reminder_time.strftime("%H:%M") if reminder_time else None,
                    "answer": current_value,
                    "_sort_key": (adherence.date, reminder_time or dt_time.min),
                }
            )

        # Only return questionnaire if at least one medication is unanswered
        if not has_unanswered:
            return None

        # Sort by date (older first), then by reminder time
        medication_entries.sort(key=lambda x: x["_sort_key"])

        # Remove sort key from output
        for entry in medication_entries:
            del entry["_sort_key"]

        # Build the single question with medications as sub-questions
        question = {
            "id": base_question.get("id", "medications-notifications"),
            "text": base_question.get("text", "Did you take your medication?"),
            "type": base_question.get("type", "single_choice"),
            "required": base_question.get("required", False),
            "medications": medication_entries,
        }

        return {
            "questionnaire_id": questionnaire_id,
            "questions": [question],
            "is_completed": False,  # Always false since we only return if there's unanswered
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

    # ========== Condition Assessment Methods ==========

    def _build_condition_assessment(
        self,
        user_id: int,
        condition_key: str,
        questionnaire_id: str,
        target_date: date,
    ) -> Optional[Dict[str, Any]]:
        """
        Build a condition assessment questionnaire item.

        Args:
            user_id: User ID
            condition_key: Condition filename key (e.g., 'depression', 'chronic_pain')
            questionnaire_id: Full questionnaire ID (e.g., 'condition-assessment-depression')
            target_date: The date for the questionnaire

        Returns:
            Questionnaire item dict, or None if questionnaire file not found
        """
        try:
            questionnaire_data = self.resource_loader.load_condition_assessment(
                condition_key
            )
        except FileNotFoundError:
            return None

        # Get existing answers for this questionnaire and date
        user_answers = self._extract_condition_assessment_answers(
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

        result = {
            "questionnaire_id": questionnaire_id,
            "title": questionnaire_data.get("title"),
            "description": questionnaire_data.get("description"),
            "questions": questions,
            "is_completed": is_completed,
        }

        # Include score_range if present in YAML
        if "score_range" in questionnaire_data:
            result["score_range"] = questionnaire_data["score_range"]

        return result

    def _extract_condition_assessment_answers(
        self, user_id: int, questionnaire_id: str, target_date: date
    ) -> Dict[str, Any]:
        """
        Extract user's condition assessment answers from observations.

        Condition assessment answers are stored with:
        - code: questionnaire_id (e.g., "condition-assessment-depression")
        - variant: question_id (e.g., "bothered-little-interest")
        - value_string: selected option value (e.g., "several-days")
        - questionnaire_completion_id: links to the completion record

        Args:
            user_id: User ID
            questionnaire_id: Questionnaire ID (e.g., "condition-assessment-depression")
            target_date: The date to get answers for

        Returns:
            Dictionary of question_id -> answer value
        """
        # Get questionnaire completion record for this user/questionnaire/date
        completion = self.completion_repo.get_by_user_questionnaire_date(
            user_id, questionnaire_id, target_date
        )

        if not completion:
            return {}

        # Query observations by questionnaire_completion_id
        observations = self.observation_repo.get_by_questionnaire_completion_id(
            completion.id
        )

        # Build answers dict: variant (question_id) -> value_string (selected option)
        answers = {}
        for obs in observations:
            if obs.variant:
                # Return the string value (option value like "several-days")
                answers[obs.variant] = obs.value_string

        return answers

    def _get_condition_assessment_scores_for_date(
        self, user_id: int, target_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get condition assessment scores completed on a specific date for user's active conditions.
        Results are ordered by leading condition priority.

        Args:
            user_id: User ID
            target_date: The date to check for completed assessments

        Returns:
            List of score dictionaries with questionnaire_id, score, and condition
        """
        from datetime import datetime, timezone
        from app.shared.condition_utils import order_leading_conditions
        from app.shared.constants import CONDITION_ASSESSMENT_OBSERVATION_CODES

        # Get user's active conditions
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.conditions:
            return []

        # Build set of relevant questionnaire keys based on user's conditions
        relevant_keys: set = set()
        condition_codes = [c.condition_code for c in user.conditions]

        for condition_code in condition_codes:
            questionnaire_keys = CONDITION_ASSESSMENT_MAP.get(condition_code, [])
            relevant_keys.update(questionnaire_keys)

        # Special case: Bipolar users without Depression get depression assessment too
        has_bipolar = "13746004" in set(condition_codes)
        has_depression = "35489007" in set(condition_codes)
        if has_bipolar and not has_depression:
            relevant_keys.add("depression")

        if not relevant_keys:
            return []

        # Get ordered conditions for sorting
        ordered_conditions = order_leading_conditions(condition_codes)

        # Build reverse mapping: questionnaire_key -> condition_code
        questionnaire_to_condition = {}
        for code, keys in CONDITION_ASSESSMENT_MAP.items():
            for key in keys:
                questionnaire_to_condition[key] = code

        scores = []

        # Create datetime range for the target date
        start_datetime = datetime.combine(
            target_date, datetime.min.time(), tzinfo=timezone.utc
        )
        end_datetime = datetime.combine(
            target_date, datetime.max.time(), tzinfo=timezone.utc
        )

        # Only check observation codes for user's relevant conditions
        for questionnaire_id, observation_code in CONDITION_ASSESSMENT_OBSERVATION_CODES.items():
            # Extract key from questionnaire_id (e.g., "chronic_pain" from "condition-assessment-chronic-pain")
            key = questionnaire_id.replace("condition-assessment-", "").replace("-", "_")
            if key not in relevant_keys:
                continue

            # Query for score observation on this date
            observations, _ = self.observation_repo.get_by_user_paginated(
                user_id=user_id,
                code=observation_code,
                start_date=start_datetime,
                end_date=end_datetime,
                page=1,
                page_size=1,
            )

            if observations:
                obs = observations[0]
                score_value = obs.value_integer
                if score_value is not None:
                    # Extract condition from questionnaire_id (e.g., "depression" from "condition-assessment-depression")
                    condition = questionnaire_id.replace("condition-assessment-", "")
                    scores.append({
                        "questionnaire_id": questionnaire_id,
                        "condition": condition,
                        "score": score_value,
                    })

        # Sort scores by leading condition order
        def get_score_priority(score_item: Dict[str, Any]) -> int:
            key = score_item["condition"].replace("-", "_")
            condition_code = questionnaire_to_condition.get(key)
            if condition_code in ordered_conditions:
                return ordered_conditions.index(condition_code)
            return 999  # Unknown conditions go last

        scores.sort(key=get_score_priority)

        return scores
