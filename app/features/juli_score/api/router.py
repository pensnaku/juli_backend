"""API router for Juli Score feature"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.domain.entities import User
from app.features.juli_score.service import JuliScoreService
from app.features.juli_score.domain.schemas import (
    JuliScoreResponse,
    JuliScoreListResponse,
    JuliScoreLatestResponse,
)
from app.features.juli_score.constants import SUPPORTED_CONDITION_CODES


router = APIRouter()


@router.get("/latest", response_model=JuliScoreLatestResponse)
def get_latest_scores(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the most recent Juli Scores for all user conditions.

    Returns stored scores only (does not recalculate).
    """
    service = JuliScoreService(db)
    return service.get_latest_scores_for_user(current_user.id)


@router.get("/latest/{condition_code}", response_model=JuliScoreResponse)
def get_latest_score_for_condition(
    condition_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the most recent Juli Score for a specific condition."""
    if condition_code not in SUPPORTED_CONDITION_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported condition code: {condition_code}. "
                   f"Supported: {SUPPORTED_CONDITION_CODES}",
        )

    service = JuliScoreService(db)
    score = service.get_latest_score(current_user.id, condition_code)

    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No score found for condition: {condition_code}",
        )

    return score


@router.get("/history/{condition_code}", response_model=JuliScoreListResponse)
def get_score_history(
    condition_code: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get paginated Juli Score history for a specific condition."""
    if condition_code not in SUPPORTED_CONDITION_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported condition code: {condition_code}. "
                   f"Supported: {SUPPORTED_CONDITION_CODES}",
        )

    service = JuliScoreService(db)
    return service.get_score_history(
        current_user.id, condition_code, page, page_size
    )
