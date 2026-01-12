"""API router for tracking topics feature"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.features.tracking.domain.schemas import (
    IndividualTrackingDataResponse,
    IndividualTrackingTopicData,
    TrackingObservation,
)
from app.features.auth.repository import UserTrackingTopicRepository
from app.features.observations.repository import ObservationRepository
from app.shared.constants import DAILY_ROUTINE_STUDENT


router = APIRouter()


@router.get("", response_model=TrackingTopicListResponse)
def get_tracking_topics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all tracking topics for the current user.
    Default topics are filtered based on user type (student vs non-student),
    followed by any custom user topics with their activation status.
    """
    service = TrackingTopicService(db)
    is_student = (
        current_user.settings
        and current_user.settings.daily_routine == DAILY_ROUTINE_STUDENT
    )
    return service.get_all_topics(current_user.id, is_student=is_student)


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
    - `topic_code`: unique identifier (optional - auto-generated from label with random suffix if not provided)
    - `label`: human-readable name (required)
    - `question`: question to ask users (required)
    - `data_type`: "number" or "boolean" (required)
    - `unit`: unit of measurement (optional, for number types)
    - `emoji`: visual indicator (optional)
    - `min`: minimum value (optional, for number types)
    - `max`: maximum value (optional, for number types)

    Example custom topic request (topic_code will be auto-generated):
    {
        "label": "Water Intake",
        "question": "How many glasses of water did you drink?",
        "data_type": "number",
        "unit": "glasses",
        "emoji": "💧",
        "min": 0,
        "max": 20
    }

    Generated topic_code might be: "water-intake-a3b9f2"
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


@router.get("/data", response_model=IndividualTrackingDataResponse)
def get_individual_tracking_data(
    start_date: datetime = Query(..., description="Start of date range (inclusive)"),
    end_date: datetime = Query(..., description="End of date range (inclusive)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all individual tracking topics with their observations for a date range.

    Returns tracking topic metadata (label, question, unit, etc.) along with
    all observations for each topic in the specified date range.

    Observations are stored with code='individual-tracking' and variant=topic_code.
    """
    tracking_repo = UserTrackingTopicRepository(db)
    obs_repo = ObservationRepository(db)

    # Get all active tracking topics for the user
    topics = tracking_repo.get_by_user_id(current_user.id, active_only=True)

    if not topics:
        return IndividualTrackingDataResponse(topics=[], count=0)

    # Extract topic codes (variants for the observations)
    topic_codes = [topic.topic_code for topic in topics]

    # Query all individual-tracking observations with these variants
    observations = obs_repo.get_by_codes_and_date_range(
        user_id=current_user.id,
        codes=["individual-tracking"],
        start_date=start_date,
        end_date=end_date,
        variants=topic_codes,
        limit_per_code=None,
    )

    # Group observations by variant (topic_code)
    obs_by_topic = {}
    for obs in observations:
        variant = obs.variant
        if variant not in obs_by_topic:
            obs_by_topic[variant] = []
        obs_by_topic[variant].append(
            TrackingObservation(
                id=obs.id,
                code=obs.code,
                variant=obs.variant,
                value_integer=obs.value_integer,
                value_decimal=obs.value_decimal,
                value_string=obs.value_string,
                value_boolean=obs.value_boolean,
                effective_at=obs.effective_at,
                unit=obs.unit,
                data_source=obs.data_source,
            )
        )

    # Build response with topic metadata and observations
    total_count = 0
    topic_responses = []

    for topic in topics:
        topic_obs = obs_by_topic.get(topic.topic_code, [])
        total_count += len(topic_obs)

        topic_responses.append(
            IndividualTrackingTopicData(
                topic_code=topic.topic_code,
                topic_label=topic.topic_label,
                question=topic.question,
                unit=topic.unit,
                emoji=topic.emoji,
                data_type=topic.data_type,
                min_value=topic.min_value,
                max_value=topic.max_value,
                observations=topic_obs,
            )
        )

    return IndividualTrackingDataResponse(
        topics=topic_responses,
        count=total_count,
    )