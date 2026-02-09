"""API router for push notifications feature"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.domain.entities import User
from app.features.notifications.domain.schemas import (
    SubscriptionRequest,
    SubscriptionResponse,
)
from app.features.notifications.repository import PushSubscriptionRepository
from app.features.notifications.service import NotificationService


router = APIRouter()


@router.post("/subscribe", response_model=SubscriptionResponse)
def subscribe(
    request: SubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Register a device for push notifications.

    This endpoint should be called when:
    - User logs in on a new device
    - App starts and has a new/refreshed device token
    - Device token is refreshed by the OS

    If the device token already exists for a different user,
    it will be reassigned to the current user.
    """
    repo = PushSubscriptionRepository(db)

    # Check if token already exists
    existing = repo.get_by_device_token(request.device_token)

    if existing:
        if existing.user_id != current_user.id:
            # Token moved to new user - delete old and create new
            repo.delete(existing.id)
            repo.create(
                current_user.id,
                request.device_token,
                request.device_type
            )
            return SubscriptionResponse(status="subscribed")
        else:
            # Same user, same token - just ensure it's active
            if not existing.is_active:
                existing.is_active = True
                db.commit()
            return SubscriptionResponse(status="updated")

    # Create new subscription
    repo.create(current_user.id, request.device_token, request.device_type)
    return SubscriptionResponse(status="subscribed")


@router.delete("/unsubscribe", response_model=SubscriptionResponse)
def unsubscribe(
    device_token: str = Query(..., description="Device token to unsubscribe"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Unregister a device from push notifications.

    This endpoint should be called when:
    - User logs out of the app
    - User disables notifications in app settings
    """
    repo = PushSubscriptionRepository(db)
    deleted = repo.delete_by_device_token(device_token)

    if deleted:
        return SubscriptionResponse(status="unsubscribed")
    else:
        return SubscriptionResponse(status="not_found")


@router.post("/test", response_model=SubscriptionResponse)
async def test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a test notification to all registered devices for the current user.

    Useful for verifying that push notifications are working correctly.
    """
    service = NotificationService(db)

    notification = NotificationService.create_notification(
        title="Test Notification",
        text="Push notifications are working!",
        data={"type": "test"}
    )

    await service.send_to_user(current_user.id, notification)

    return SubscriptionResponse(status="sent")
