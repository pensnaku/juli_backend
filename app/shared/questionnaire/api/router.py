"""Questionnaire API endpoints"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.shared.questionnaire.questionnaire_service import QuestionnaireService

router = APIRouter()


@router.get("/next", response_model=Optional[Dict[str, Any]])
def get_next_questionnaire(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the next eligible questionnaire for the authenticated user.
    Returns the questionnaire with user's existing answers merged in.

    Returns None if no questionnaires are available.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Questionnaire with answers, or null if none available

    Response format:
    ```json
    {
        "id": "onboarding",
        "title": "Welcome! Let's get to know you",
        "description": "...",
        "questions": [
            {
                "id": "name",
                "text": "What should I call you?",
                "type": "text",
                "validation": {"required": true},
                "answer": "John Doe"  // User's existing answer, or null
            },
            ...
        ]
    }
    ```
    """
    try:
        questionnaire_service = QuestionnaireService(db)
        questionnaire = questionnaire_service.get_next_questionnaire(current_user.id)

        if not questionnaire:
            return None

        return questionnaire

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching questionnaire: {str(e)}"
        )


@router.get("/{questionnaire_id}", response_model=Dict[str, Any])
def get_questionnaire_by_id(
    questionnaire_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific questionnaire by ID with user's existing answers.

    Args:
        questionnaire_id: Questionnaire identifier (e.g., 'onboarding', 'daily')
        current_user: Current authenticated user
        db: Database session

    Returns:
        Questionnaire with user's existing answers merged in

    Raises:
        HTTPException: If questionnaire not found
    """
    try:
        questionnaire_service = QuestionnaireService(db)
        questionnaire = questionnaire_service.get_questionnaire_with_answers(
            current_user.id, questionnaire_id
        )
        return questionnaire

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching questionnaire: {str(e)}"
        )