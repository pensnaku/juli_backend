"""API router for Juli Score feature"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.scheduler import get_scheduler_status
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.domain.entities import User
from app.features.juli_score.service import JuliScoreService
from app.features.juli_score.domain.schemas import (
    JuliScoreResponse,
    JuliScoreListResponse,
    JuliScoreLatestResponse,
)
from app.features.juli_score.constants import (
    SUPPORTED_CONDITION_CODES,
    CONDITION_FACTORS,
    JuliScoreConditions,
)
from app.features.juli_score.repository import JuliScoreRepository
from app.features.juli_score.service.factor_calculators import FactorCalculator


router = APIRouter()


@router.get("/scheduler-status")
def get_scheduler_info():
    """Get the current scheduler status and registered jobs (debug endpoint)."""
    return get_scheduler_status()


@router.get("/debug/{user_id}/{condition_code}")
def debug_user_factors(
    user_id: int,
    condition_code: str,
    db: Session = Depends(get_db),
):
    """
    Debug endpoint to check what data is available for a user's score calculation.
    Shows raw values and calculated scores for each factor.
    """
    if condition_code not in SUPPORTED_CONDITION_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported condition code: {condition_code}",
        )

    repo = JuliScoreRepository(db)
    target_date = date.today()
    factors_config = CONDITION_FACTORS.get(condition_code, {})
    calculator = FactorCalculator(repo, user_id, target_date)

    results = {}
    for factor_name, config in factors_config.items():
        score, raw_input = calculator.calculate_factor(factor_name, config, condition_code)
        results[factor_name] = {
            "raw_input": raw_input,
            "score": score,
            "weight": config.weight,
            "observation_code": config.observation_code,
            "has_data": score is not None,
        }

    data_points = sum(1 for r in results.values() if r["has_data"])

    return {
        "user_id": user_id,
        "condition_code": condition_code,
        "target_date": str(target_date),
        "data_points": data_points,
        "minimum_required": 3,
        "can_calculate": data_points >= 3,
        "factors": results,
    }


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
