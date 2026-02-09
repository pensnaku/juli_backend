"""FCM (Firebase Cloud Messaging) service for Android notifications"""
import logging
from typing import Optional

from aiohttp import ClientSession, ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

FCM_BASE_URL = "https://fcm.googleapis.com"
FCM_SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]


class FCMService:
    """Handles push notifications for Android devices via FCM"""

    def __init__(self):
        self.credentials = None
        self.project_id: Optional[str] = None
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Lazy initialization of FCM credentials"""
        if self._initialized:
            return self.credentials is not None

        self._initialized = True

        if not settings.FCM_SERVICE_ACCOUNT_FILE:
            logger.warning(
                "FCM service account file not configured - Android notifications disabled"
            )
            return False

        try:
            from google.oauth2 import service_account

            self.credentials = service_account.Credentials.from_service_account_file(
                settings.FCM_SERVICE_ACCOUNT_FILE,
                scopes=FCM_SCOPES
            )
            self.project_id = self.credentials.project_id
            logger.info(f"FCM credentials initialized for project: {self.project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize FCM credentials: {e}")
            return False

    def _get_access_token(self) -> Optional[str]:
        """Get OAuth access token for FCM API"""
        if not self.credentials:
            return None

        try:
            from google.auth.transport.requests import Request

            self.credentials.refresh(Request())
            return self.credentials.token
        except Exception as e:
            logger.error(f"Failed to refresh FCM access token: {e}")
            return None

    async def send(self, device_token: str, notification: dict) -> tuple[bool, Optional[str]]:
        """
        Send notification via FCM.

        Args:
            device_token: Android device token
            notification: Notification payload with 'android' key

        Returns:
            Tuple of (success, error_description)
        """
        if not self._ensure_initialized():
            return False, "FCM not configured"

        token = self._get_access_token()
        if not token:
            return False, "Failed to get FCM access token"

        message = {
            "message": {
                "token": device_token,
                "notification": notification["android"]["notification"],
                "data": {
                    k: str(v) for k, v in notification["android"]["data"].items()
                },
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        url = f"{FCM_BASE_URL}/v1/projects/{self.project_id}/messages:send"

        try:
            async with ClientSession() as session:
                async with session.post(url, headers=headers, json=message) as resp:
                    if resp.status < 400:
                        logger.debug(
                            f"FCM notification sent successfully to {device_token[:20]}..."
                        )
                        return True, None
                    else:
                        error_body = await resp.text()
                        logger.warning(
                            f"FCM notification failed: {resp.status} - {error_body}"
                        )
                        return False, f"HTTP {resp.status}: {error_body}"

        except ClientError as e:
            logger.error(f"FCM client error: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"FCM send error: {e}")
            return False, str(e)
