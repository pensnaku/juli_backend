"""API endpoints for daily dare badges"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.features.daily_dare_badges.service.badge_service import DailyDareBadgeService

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
def get_user_badges(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all badges earned by the current user.

    Returns a list of badges with earning details including:
    - Badge info (name, slug, level, etc.)
    - When it was first/last earned
    - How many times it has been earned
    """
    try:
        badge_service = DailyDareBadgeService(db)
        badges = badge_service.get_user_badges(current_user.id)

        return {
            "badges": badges
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching badges: {str(e)}"
        )


@router.get("/dashboard", response_model=Dict[str, Any])
def get_badge_dashboard(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get badge dashboard overview for the current user.

    Returns:
    - last_earned_regular: Most recently earned regular badge
    - last_earned_monthly: Most recently earned monthly badge
    - next_regular: Next regular badge to earn (by priority)
    - next_monthly: Current month's challenge badge (if not yet earned)
    """
    try:
        badge_service = DailyDareBadgeService(db)
        dashboard = badge_service.get_dashboard_overview(current_user.id)

        return dashboard

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard: {str(e)}"
        )


@router.get("/all", response_model=Dict[str, Any])
def get_all_badges_with_status(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all available badges with user's achievement status.

    Returns all regular and monthly badges, each with:
    - Badge info
    - is_earned: Whether the user has earned this badge
    - times_earned: How many times they've earned it (for repeatable badges)
    """
    try:
        badge_service = DailyDareBadgeService(db)
        all_badges = badge_service.get_all_badges_with_status(current_user.id)

        return all_badges

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching badges: {str(e)}"
        )
