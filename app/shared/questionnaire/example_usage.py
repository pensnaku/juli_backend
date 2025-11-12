"""
Example usage of questionnaire service

This file demonstrates how to use the questionnaire service in your application.
You can integrate this into your actual API endpoints.
"""

from app.shared.questionnaire import QuestionnaireService


# ===== Example 1: Load and serve questionnaire =====
def get_onboarding_questionnaire():
    """Load the onboarding questionnaire"""
    service = QuestionnaireService()
    questionnaire = service.load_questionnaire("onboarding")

    # Convert to frontend format
    return service.to_frontend_format(questionnaire)


# ===== Example 2: Get specific question =====
def get_question(question_id: str):
    """Get a specific question by ID"""
    service = QuestionnaireService()
    questionnaire = service.load_questionnaire("onboarding")
    question = service.get_question_by_id(questionnaire, question_id)

    if question:
        return question.model_dump()
    return None


# ===== Example 3: Filter questions based on user context =====
def get_visible_questions(user_settings: dict, user_answers: dict):
    """
    Get questions that should be visible based on settings and previous answers

    Args:
        user_settings: Dict like {"ask_ethnicity": True}
        user_answers: Dict like {"daily-routine-or-main-activity": "student", "conditions": ["73211009"]}
    """
    service = QuestionnaireService()
    questionnaire = service.load_questionnaire("onboarding")

    # Merge settings and answers into context
    context = {**user_answers}

    # Get filtered questions
    visible_questions = service.get_questions_for_context(
        questionnaire,
        context
    )

    return [q.model_dump() for q in visible_questions]


# ===== Example 4: FastAPI endpoint (copy this to your router) =====
"""
from fastapi import APIRouter
from app.shared.questionnaire import QuestionnaireService

router = APIRouter(prefix="/questionnaires", tags=["questionnaires"])

@router.get("/{questionnaire_name}")
def get_questionnaire(questionnaire_name: str):
    '''Get a questionnaire by name'''
    service = QuestionnaireService()
    questionnaire = service.load_questionnaire(questionnaire_name)
    return service.to_frontend_format(questionnaire)

@router.post("/{questionnaire_name}/filter")
def filter_questions(questionnaire_name: str, context: dict):
    '''Get visible questions based on context'''
    service = QuestionnaireService()
    questionnaire = service.load_questionnaire(questionnaire_name)
    visible = service.get_questions_for_context(questionnaire, context)
    return {"questions": [q.model_dump() for q in visible]}
"""


if __name__ == "__main__":
    # Test loading
    print("=== Loading questionnaire ===")
    result = get_onboarding_questionnaire()
    print(f"Loaded: {result['title']}")
    print(f"Total questions: {len(result['questions'])}")

    # Test specific question
    print("\n=== Get specific question ===")
    question = get_question("gender")
    if question:
        print(f"Question: {question['text']}")
        print(f"Options: {len(question.get('options', []))}")

    # Test filtering
    print("\n=== Filter questions (diabetes user) ===")
    visible = get_visible_questions(
        user_settings={"ask_ethnicity": False},
        user_answers={"conditions": ["73211009"]}  # Diabetes
    )
    diabetes_questions = [q['id'] for q in visible if 'diabetes' in q['id'] or 'glucose' in q['id']]
    print(f"Diabetes-specific questions shown: {diabetes_questions}")