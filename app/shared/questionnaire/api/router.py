"""Questionnaire API endpoints"""
from typing import Optional, Dict, Any
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.shared.questionnaire.questionnaire_service import QuestionnaireService
from app.shared.questionnaire.answer_handler import QuestionnaireAnswerHandler
from app.shared.questionnaire.schemas import (
    DailyAnswerRequest,
    DailyAnswerResponse,
)

router = APIRouter()


@router.get("/next", response_model=Optional[Dict[str, Any]])
def get_next_questionnaire(
    target_date: Optional[str] = Query(
        None,
        alias="date",
        description="Date for daily questionnaires (YYYY-MM-DD). Defaults to today.",
        example="2025-12-23"
    ),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the next eligible questionnaire for the authenticated user.

    - If onboarding is not complete, returns the onboarding questionnaire.
    - If onboarding is complete, returns daily questionnaires for the specified date.
    - Always returns all condition questionnaires, each with `is_completed` flag.

    Args:
        target_date: Optional date (YYYY-MM-DD). Defaults to today if not provided.
        current_user: Current authenticated user
        db: Database session

    Returns:
        Questionnaire with answers, or null if none available

    Response format for onboarding:
    ```json
    {
        "id": "onboarding",
        "title": "Welcome! Let's get to know you",
        "questions": [...]
    }
    ```

    Response format for daily questionnaires:
    ```json
    {
        "title": "Daily Check-in",
        "description": "Your daily health questions",
        "completion_date": "2025-12-23",
        "questionnaires": [
            {
                "condition_key": "asthma",
                "condition_code": "195967001",
                "condition_label": "Asthma",
                "questionnaire_id": "daily-asthma",
                "is_completed": false,
                "questions": [...]
            }
        ]
    }
    ```
    """
    try:
        # Parse target_date if provided, otherwise use today
        parsed_date = date.today()
        if target_date:
            try:
                parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD."
                )

        questionnaire_service = QuestionnaireService(db)
        questionnaire = questionnaire_service.get_next_questionnaire(
            current_user.id, target_date=parsed_date
        )

        if not questionnaire:
            return None

        return questionnaire

    except HTTPException:
        raise
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


@router.post("/daily/answer", response_model=DailyAnswerResponse)
def save_daily_answer(
    request: DailyAnswerRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a single answer for a daily questionnaire.

    Stores the answer as an observation and optionally marks the questionnaire as completed.

    Args:
        request: Daily answer request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Confirmation of saved answer

    Request format:
    ```json
    {
        "completion_date": "2025-12-23",
        "question_id": "how-often-inhaler-or-nebulizer",
        "answer": 2,
        "questionnaire_id": "daily-asthma",
        "completed": false
    }
    ```
    """
    try:
        # Parse completion_date string to date object
        completion_date = datetime.strptime(request.completion_date, "%Y-%m-%d").date()

        answer_handler = QuestionnaireAnswerHandler(db)
        result = answer_handler.save_single_answer(
            user_id=current_user.id,
            completion_date=completion_date,
            question_id=request.question_id,
            answer=request.answer,
            questionnaire_id=request.questionnaire_id,
            mark_completed=request.completed,
        )
        return DailyAnswerResponse(
            message="Answer saved",
            question_id=request.question_id,
            questionnaire_id=request.questionnaire_id,
            completed=result["completed"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving answer: {str(e)}"
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