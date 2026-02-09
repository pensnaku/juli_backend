"""Main notification service for push notifications"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.features.notifications.repository import PushSubscriptionRepository
from app.features.notifications.service.apns_service import APNsService
from app.features.notifications.service.fcm_service import FCMService

logger = logging.getLogger(__name__)


class NotificationService:
    """Main service for creating and sending push notifications"""

    # Singleton services for APNs and FCM (shared across instances)
    _apns_service: Optional[APNsService] = None
    _fcm_service: Optional[FCMService] = None

    def __init__(self, db: Session):
        self.db = db
        self.subscription_repo = PushSubscriptionRepository(db)

        # Initialize singleton services if not already done
        if NotificationService._apns_service is None:
            NotificationService._apns_service = APNsService()
        if NotificationService._fcm_service is None:
            NotificationService._fcm_service = FCMService()

    @staticmethod
    def create_notification(
        title: str,
        text: str,
        data: Optional[dict] = None,
        aps_data: Optional[dict] = None
    ) -> dict:
        """
        Create a platform-specific notification payload.

        Args:
            title: Notification title
            text: Notification body text
            data: Custom data payload (sent to both platforms)
            aps_data: Additional APNs-specific data (iOS only)

        Returns:
            Dictionary with 'ios' and 'android' keys containing
            platform-specific notification formats
        """
        data = data or {}
        aps_data = aps_data or {}

        # Add timestamp to data
        data["createdAt"] = datetime.utcnow().isoformat()

        return {
            "ios": {
                "aps": {
                    "alert": {"title": title, "body": text},
                    "badge": 0,
                    "sound": "default",
                    **aps_data,
                },
                "data": data,
            },
            "android": {
                "data": data,
                "notification": {"title": title, "body": text}
            },
        }

    async def send_to_user(self, user_id: int, notification: dict):
        """
        Send notification to all devices registered for a user.

        Invalid device tokens are automatically cleaned up.

        Args:
            user_id: Target user ID
            notification: Notification payload (from create_notification)
        """
        subscriptions = self.subscription_repo.get_by_user_id(user_id)

        if not subscriptions:
            logger.info(f"No push subscriptions for user {user_id}")
            return

        logger.info(f"Sending notification to {len(subscriptions)} device(s) for user {user_id}")

        for sub in subscriptions:
            try:
                if sub.device_type == "ios":
                    logger.info(f"Sending iOS notification to subscription {sub.id}")
                    success, error = await self._apns_service.send(
                        sub.device_token, notification
                    )
                elif sub.device_type == "android":
                    logger.info(f"Sending Android notification to subscription {sub.id}")
                    success, error = await self._fcm_service.send(
                        sub.device_token, notification
                    )
                else:
                    logger.warning(f"Unknown device type: {sub.device_type}")
                    continue

                if success:
                    logger.info(f"Notification sent successfully to subscription {sub.id}")
                else:
                    logger.warning(
                        f"Notification failed for subscription {sub.id}: {error}"
                    )
                    # Delete invalid subscription to prevent future failures
                    self.subscription_repo.delete(sub.id)
                    logger.info(f"Deleted invalid subscription {sub.id}")

            except Exception as e:
                logger.error(
                    f"Error sending notification to subscription {sub.id}: {e}"
                )
                # Delete problematic subscription
                self.subscription_repo.delete(sub.id)

    async def send_direct(self, user_id: int, notification: dict):
        """
        Send notification directly (bypassing the queue).

        Use this for immediate delivery without debouncing.

        Args:
            user_id: Target user ID
            notification: Notification payload (from create_notification)
        """
        await self.send_to_user(user_id, notification)

    async def queue_notification(self, user_id: int, notification: dict):
        """
        Queue a notification for debounced delivery.

        Args:
            user_id: Target user ID
            notification: Notification payload (from create_notification)
        """
        from app.features.notifications.service.notification_queue import queue_notification
        await queue_notification(user_id, notification)
