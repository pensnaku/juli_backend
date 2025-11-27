"""API router for dares feature"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.domain.entities import User
from app.features.dares.service import DareService
from app.features.dares.domain.schemas import (
    DailyDaresResponse,
    UpdateDareCompletionRequest,
    UpdateDareCompletionResponse,
    DareHistoryResponse,
)


router = APIRouter()


@router.get("/daily/{target_date}", response_model=DailyDaresResponse)
def get_dares_for_date(
    target_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dares for a specific date.

    Returns 4 dares (one from each category: Activity, Nutrition, Sleep, Wellness).
    If dares haven't been generated for that date, they will be generated.
    The client should pass the user's local date (e.g., 2025-11-27).
    """
    service = DareService(db)
    return service.get_dares_for_date(current_user.id, target_date)


@router.patch("/{assignment_id}/completion", response_model=UpdateDareCompletionResponse)
def update_dare_completion(
    assignment_id: int,
    request: UpdateDareCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update dare completion status.

    Set completed=true to mark as complete (awards points).
    Set completed=false to mark as incomplete (removes points).
    """
    service = DareService(db)

    try:
        return service.update_dare_completion(current_user.id, assignment_id, request.completed)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/history", response_model=DareHistoryResponse)
def get_dare_history(
    days: int = Query(default=7, ge=1, le=30, description="Number of days of history (max 30)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dare history for the past N days.

    Returns dares for each day with completion status and points earned.
    """
    service = DareService(db)
    return service.get_history(current_user.id, days)