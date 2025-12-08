"""API router for tracking topics feature"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.domain.entities import User
from app.features.auth.domain.schemas import (
    UserTrackingTopicCreate,
    TrackingTopicUpdate,
    TrackingTopicResponse,
    TrackingTopicListResponse,
)
from app.features.tracking.service import TrackingTopicService


router = APIRouter()


@router.get("", response_model=TrackingTopicListResponse)
def get_tracking_topics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all tracking topics for the current user.
    Default topics are always included first with their activation status.
    """
    service = TrackingTopicService(db)
    return service.get_all_topics(current_user.id)


@router.post("", response_model=TrackingTopicResponse, status_code=status.HTTP_201_CREATED)
def activate_tracking_topic(
    request: UserTrackingTopicCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Activate a tracking topic for the current user.

    For default topics (coffee-consumption, smoking, alcohol-consumption, hours-spent-outside):
    - Only `topic_code` is required

    For custom topics:
    - `topic_code`: unique identifier for the topic
    - `label`: human-readable name (required)
    - `question`: question to ask users (required)
    - `data_type`: "number" or "boolean" (required)
    - `unit`: unit of measurement (optional, for number types)
    - `emoji`: visual indicator (optional)
    - `min`: minimum value (optional, for number types)
    - `max`: maximum value (optional, for number types)
    """
    service = TrackingTopicService(db)
    try:
        return service.activate_topic(current_user.id, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/{topic_code}", response_model=TrackingTopicResponse)
def update_tracking_topic(
    topic_code: str,
    request: TrackingTopicUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a tracking topic for the current user.

    For default topics:
    - Only `is_active` can be changed (activate/deactivate)

    For custom topics:
    - All fields can be updated
    - If changing data_type from boolean to number, min and max are required
    - If changing data_type from number to boolean, min, max, and unit are nullified
    """
    service = TrackingTopicService(db)
    try:
        return service.update_topic(current_user.id, topic_code, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{topic_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tracking_topic(
    topic_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a tracking topic for the current user.

    Note: Default topics cannot be deleted, only deactivated via PATCH.
    Use PATCH with `is_active: false` to deactivate default topics.
    """
    service = TrackingTopicService(db)
    try:
        success = service.delete_topic(current_user.id, topic_code)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracking topic not found",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )