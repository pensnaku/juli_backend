"""Service for managing condition assessment questionnaires (periodic assessments)"""
from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
import logging

from app.core.resource_loader import get_resource_loader
from app.features.auth.repository import UserConditionRepository
from app.features.observations.repository import ObservationRepository
from app.shared.constants import (
    CONDITION_ASSESSMENT_MAP,
    CONDITION_ASSESSMENT_OBSERVATION_CODES,
)

logger = logging.getLogger(__name__)


class ConditionAssessmentService:
    """
    Service to manage condition assessment questionnaire scheduling.

    Condition assessments are shown based on interval_days from each YAML file:
    - Every 14 days for most conditions
    - Every 30 days for diabetes

    Special cases:
    - Bipolar users without Depression condition get both bipolar AND depression assessments
    """

    def __init__(self, db: Session):
        self.db = db
        self.condition_repo = UserConditionRepository(db)
        self.observation_repo = ObservationRepository(db)
        self.resource_loader = get_resource_loader()
        self._config_cache: Dict[str, Dict[str, Any]] = {}

    def _get_questionnaire_config(self, questionnaire_key: str) -> Dict[str, Any]:
        """
        Load and cache questionnaire config from YAML.

        Args:
            questionnaire_key: The questionnaire key (e.g., "depression")

        Returns:
            Questionnaire configuration dictionary
        """
        if questionnaire_key not in self._config_cache:
            try:
                self._config_cache[questionnaire_key] = (
                    self.resource_loader.load_condition_assessment(questionnaire_key)
                )
            except FileNotFoundError:
                logger.warning(f"Condition assessment config not found: {questionnaire_key}")
                return {}
        return self._config_cache.get(questionnaire_key, {})

    def get_interval_days(self, questionnaire_key: str) -> int:
        """
        Get the interval in days for a questionnaire from its YAML config.

        Args:
            questionnaire_key: The questionnaire key (e.g., "diabetes", "depression")

        Returns:
            Number of days between assessments (from YAML interval_days, defaults to 14)
        """
        config = self._get_questionnaire_config(questionnaire_key)
        return config.get("interval_days", 14)

    def get_questionnaire_id(self, questionnaire_key: str) -> str:
        """
        Convert questionnaire key to full questionnaire ID.

        Args:
            questionnaire_key: The questionnaire key (e.g., "depression")

        Returns:
            Full questionnaire ID (e.g., "condition-assessment-depression")
        """
        return f"condition-assessment-{questionnaire_key.replace('_', '-')}"

    def get_observation_code(self, questionnaire_id: str) -> Optional[str]:
        """
        Get the observation code for a questionnaire's total score.

        Args:
            questionnaire_id: The full questionnaire ID (e.g., "condition-assessment-depression")

        Returns:
            Observation code for the score (e.g., "condition-assessment-depression-score")
        """
        return CONDITION_ASSESSMENT_OBSERVATION_CODES.get(questionnaire_id)

    def get_last_response_date(
        self, user_id: int, questionnaire_id: str
    ) -> Optional[date]:
        """
        Get the date of the user's last response to a condition assessment.

        Args:
            user_id: The user ID
            questionnaire_id: The full questionnaire ID

        Returns:
            Date of last response, or None if never completed
        """
        observation_code = self.get_observation_code(questionnaire_id)
        if not observation_code:
            return None

        latest = self.observation_repo.get_latest_by_code(user_id, observation_code)
        if latest and latest.effective_at:
            return latest.effective_at.date()
        return None

    def is_questionnaire_due(
        self, user_id: int, questionnaire_key: str, target_date: date
    ) -> bool:
        """
        Check if a questionnaire is due for a user on a given date.

        A questionnaire is due if:
        - User has never completed it, OR
        - It's been >= interval_days since last completion

        Args:
            user_id: The user ID
            questionnaire_key: The questionnaire key (e.g., "depression")
            target_date: The date to check

        Returns:
            True if the questionnaire is due
        """
        questionnaire_id = self.get_questionnaire_id(questionnaire_key)
        last_response_date = self.get_last_response_date(user_id, questionnaire_id)

        if last_response_date is None:
            # Never completed - it's due
            return True

        interval_days = self.get_interval_days(questionnaire_key)
        days_since_last = (target_date - last_response_date).days

        return days_since_last >= interval_days

    def get_questionnaire_keys_for_condition(self, condition_code: str) -> List[str]:
        """
        Get all questionnaire keys for a given condition code.

        Args:
            condition_code: SNOMED condition code

        Returns:
            List of questionnaire keys (e.g., ["chronic_pain", "chronic_pain_interference"])
        """
        return CONDITION_ASSESSMENT_MAP.get(condition_code, [])

    def get_due_questionnaires_for_user(
        self, user_id: int, target_date: date
    ) -> List[str]:
        """
        Get all condition assessment questionnaires that are due for a user.

        Args:
            user_id: The user ID
            target_date: The date to check

        Returns:
            List of questionnaire IDs that are due (e.g., ["condition-assessment-depression"])
        """
        due_questionnaires: List[str] = []
        seen_keys: set = set()

        # Get user's conditions
        conditions = self.condition_repo.get_by_user_id(user_id)
        condition_codes = {c.condition_code for c in conditions}

        # Special case: Bipolar users without Depression get both assessments
        has_bipolar = "13746004" in condition_codes
        has_depression = "35489007" in condition_codes

        for condition in conditions:
            questionnaire_keys = self.get_questionnaire_keys_for_condition(
                condition.condition_code
            )

            for key in questionnaire_keys:
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                if self.is_questionnaire_due(user_id, key, target_date):
                    questionnaire_id = self.get_questionnaire_id(key)
                    due_questionnaires.append(questionnaire_id)

        # Special case: Bipolar without Depression - add depression assessment
        if has_bipolar and not has_depression:
            key = "depression"
            if key not in seen_keys and self.is_questionnaire_due(
                user_id, key, target_date
            ):
                questionnaire_id = self.get_questionnaire_id(key)
                due_questionnaires.append(questionnaire_id)

        return due_questionnaires

    def get_all_condition_assessment_keys(self) -> List[str]:
        """
        Get all available condition assessment questionnaire keys.

        Returns:
            List of all questionnaire keys
        """
        all_keys = set()
        for keys in CONDITION_ASSESSMENT_MAP.values():
            all_keys.update(keys)
        return list(all_keys)
