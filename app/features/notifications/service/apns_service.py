"""APNs (Apple Push Notification service) for iOS notifications"""
import logging
from typing import Optional
from uuid import uuid4

from app.core.config import settings

logger = logging.getLogger(__name__)


class APNsService:
    """Handles push notifications for iOS devices via APNs"""

    def __init__(self):
        self.client = None
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Lazy initialization of APNs client"""
        if self._initialized:
            return self.client is not None

        self._initialized = True

        if not settings.APNS_PEM_FILE:
            logger.warning("APNs PEM file not configured - iOS notifications disabled")
            return False

        try:
            from aioapns import APNs

            self.client = APNs(
                client_cert=settings.APNS_PEM_FILE,
                use_sandbox=settings.APNS_USE_SANDBOX,
            )
            logger.info(
                f"APNs client initialized (sandbox={settings.APNS_USE_SANDBOX})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize APNs client: {e}")
            return False

    async def send(self, device_token: str, notification: dict) -> tuple[bool, Optional[str]]:
        """
        Send notification via APNs.

        Args:
            device_token: iOS device token
            notification: Notification payload with 'ios' key

        Returns:
            Tuple of (success, error_description)
        """
        if not self._ensure_initialized():
            return False, "APNs not configured"

        try:
            from aioapns import NotificationRequest

            request = NotificationRequest(
                device_token=device_token,
                message=notification["ios"],
                notification_id=str(uuid4()),
            )

            response = await self.client.send_notification(request)

            if response.is_successful:
                logger.debug(f"APNs notification sent successfully to {device_token[:20]}...")
                return True, None
            else:
                logger.warning(
                    f"APNs notification failed: {response.status} - {response.description}"
                )
                return False, response.description

        except Exception as e:
            logger.error(f"APNs send error: {e}")
            return False, str(e)
