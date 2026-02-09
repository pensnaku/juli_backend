"""Admin endpoints for notifications (broadcast functionality)"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_superuser
from app.features.auth.domain.entities import User
from app.features.notifications.repository import PushSubscriptionRepository
from app.features.notifications.service import NotificationService

router = APIRouter()


class BroadcastRequest(BaseModel):
    """Request schema for broadcast notification"""
    title: str
    text: str
    platform: str  # "ios", "android", or "all"
    confirmation_code: str


class BroadcastResponse(BaseModel):
    """Response schema for broadcast notification"""
    status: str
    users_notified: int


@router.post("/broadcast", response_model=BroadcastResponse)
async def broadcast_notification(
    request: BroadcastRequest,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """
    Send a broadcast notification to all users on a platform.

    Requires superuser privileges and a confirmation code for safety.

    The confirmation code format: BROADCAST-{PLATFORM}-{YYYYMMDD}
    Example: BROADCAST-IOS-20260129
    """
    # Validate platform
    valid_platforms = ["ios", "android", "all"]
    if request.platform.lower() not in valid_platforms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform. Must be one of: {', '.join(valid_platforms)}"
        )

    # Validate confirmation code
    expected_code = f"BROADCAST-{request.platform.upper()}-{date.today().strftime('%Y%m%d')}"

    if request.confirmation_code != expected_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid confirmation code. Expected format: BROADCAST-PLATFORM-YYYYMMDD"
        )

    service = NotificationService(db)
    repo = PushSubscriptionRepository(db)

    # Get subscriptions by platform
    platform = request.platform.lower()
    if platform == "all":
        subscriptions = repo.get_all_active()
    else:
        subscriptions = repo.get_by_device_type(platform)

    if not subscriptions:
        return BroadcastResponse(status="no_subscriptions", users_notified=0)

    # Create notification
    notification = NotificationService.create_notification(
        title=request.title,
        text=request.text,
    )

    # Send to each unique user (deduplicate by user_id)
    user_ids_notified = set()
    for sub in subscriptions:
        if sub.user_id not in user_ids_notified:
            await service.send_to_user(sub.user_id, notification)
            user_ids_notified.add(sub.user_id)

    return BroadcastResponse(
        status="sent",
        users_notified=len(user_ids_notified)
    )
