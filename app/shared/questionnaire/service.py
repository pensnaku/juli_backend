"""Service for loading and working with questionnaires"""

from typing import Dict, Any, Optional, List
from app.core.resource_loader import get_resource_loader
from app.shared.questionnaire.models import Questionnaire, Question


class QuestionnaireService:
    """Service for questionnaire operations"""

    def __init__(self):
        self.loader = get_resource_loader()

    def load_questionnaire(self, name: str) -> Questionnaire:
        """
        Load and validate a questionnaire by name

        Args:
            name: Questionnaire filename (without .yml)

        Returns:
            Validated Questionnaire object

        Raises:
            FileNotFoundError: If questionnaire doesn't exist
            ValidationError: If questionnaire structure is invalid
        """
        raw_data = self.loader.load_yaml(f"questionnaires/{name}.yml")
        return Questionnaire(**raw_data)

    def get_question_by_id(
        self, questionnaire: Questionnaire, question_id: str
    ) -> Optional[Question]:
        """
        Get a specific question by ID

        Args:
            questionnaire: Questionnaire object
            question_id: Question ID to find

        Returns:
            Question object or None if not found
        """
        for question in questionnaire.questions:
            if question.id == question_id:
                return question
        return None

    def get_questions_for_context(
        self, questionnaire: Questionnaire, context: Dict[str, Any]
    ) -> List[Question]:
        """
        Get questions that should be shown based on context/answers

        Args:
            questionnaire: Questionnaire object
            context: Dict with settings and answer values

        Returns:
            List of questions that should be displayed
        """
        visible_questions = []

        for question in questionnaire.questions:
            if self._should_show_question(question, context, questionnaire.settings):
                visible_questions.append(question)

        return visible_questions

    def _should_show_question(
        self, question: Question, context: Dict[str, Any], settings: Any
    ) -> bool:
        """
        Check if a question should be shown based on show_if conditions

        Args:
            question: Question to check
            context: Current answers/values
            settings: Global settings

        Returns:
            True if question should be shown
        """
        if not question.show_if:
            return True  # No conditions, always show

        condition = question.show_if

        # Check setting-based conditions
        if condition.setting:
            setting_value = getattr(settings, condition.setting, None)
            if condition.equals is not None:
                return setting_value == condition.equals
            return bool(setting_value)

        # Check field-based conditions
        if condition.field:
            field_value = context.get(condition.field)

            if condition.not_empty is not None:
                return bool(field_value) == condition.not_empty

            if condition.equals is not None:
                return field_value == condition.equals

            if condition.contains is not None:
                if isinstance(field_value, list):
                    return condition.contains in field_value
                return condition.contains == field_value

        return True

    def to_frontend_format(self, questionnaire: Questionnaire) -> Dict[str, Any]:
        """
        Convert questionnaire to frontend-friendly format

        Args:
            questionnaire: Questionnaire object

        Returns:
            Dictionary optimized for frontend consumption
        """
        return {
            "id": questionnaire.questionnaire_id,
            "version": questionnaire.version,
            "title": questionnaire.title,
            "description": questionnaire.description,
            "settings": questionnaire.settings.model_dump(),
            "questions": [
                {
                    "id": q.id,
                    "text": q.text,
                    "type": q.type,
                    "helpText": q.help_text,
                    "placeholder": q.placeholder,
                    "validation": q.validation.model_dump() if q.validation else {},
                    "showIf": q.show_if.model_dump() if q.show_if else None,
                    "options": (
                        [opt.model_dump() for opt in q.options] if q.options else None
                    ),
                    "allowNone": q.allow_none,
                    "noneOption": q.none_option.model_dump() if q.none_option else None,
                }
                for q in questionnaire.questions
            ],
        }
