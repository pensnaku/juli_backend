"""
Notification trigger functions for use from sync scheduler jobs.

These functions can be called from APScheduler jobs to queue
push notifications for users.

Templates are defined in app/features/notifications/constants.py
"""
import logging

from app.features.notifications.service.notification_service import NotificationService
from app.features.notifications.service.notification_queue import queue_notification_sync
from app.features.notifications.constants import NOTIFICATION_TEMPLATES, NotificationTypes

logger = logging.getLogger(__name__)


def _create_notification_from_template(
    template_key: str,
    text_params: dict = None,
    extra_data: dict = None,
) -> dict:
    """
    Create a notification from a template.

    Args:
        template_key: Key in NOTIFICATION_TEMPLATES
        text_params: Parameters to format the text string
        extra_data: Additional data to merge into the data payload
    """
    template = NOTIFICATION_TEMPLATES[template_key]
    text_params = text_params or {}

    # Format title and text with parameters
    title = template["title"].format(**text_params) if text_params else template["title"]
    text = template["text"].format(**text_params) if text_params else template["text"]

    # Build data payload
    data = dict(template.get("data", {}))
    if extra_data:
        data.update(extra_data)

    return NotificationService.create_notification(
        title=title,
        text=text,
        data=data if data else None,
        aps_data=template.get("aps_data"),
    )


# =============================================================================
# 1. Medication Reminder
# =============================================================================

def trigger_medication_reminder(
    user_id: int,
    medication_id: int,
    medication_name: str,
    time: str,
):
    """
    Queue a medication reminder notification.

    Args:
        user_id: Target user ID
        medication_id: The UserMedication ID
        medication_name: Name of the medication
        time: Reminder time (HH:MM format)
    """
    notification = _create_notification_from_template(
        NotificationTypes.MEDICATION_REMINDER,
        text_params={"medication_name": medication_name},
        extra_data={
            "medicationId": str(medication_id),
            "medicationName": medication_name,
            "time": time,
        },
    )
    queue_notification_sync(user_id, notification)
    logger.info(f"Queued medication reminder for user {user_id}: {medication_name}")


# =============================================================================
# 2. Daily Check-in - Default
# =============================================================================

def trigger_daily_check_default(user_id: int):
    """
    Queue default daily check-in notification (no recent responses).
    """
    notification = _create_notification_from_template(
        NotificationTypes.DAILY_CHECK_DEFAULT,
    )
    queue_notification_sync(user_id, notification)
    logger.info(f"Queued default daily check-in for user {user_id}")


# =============================================================================
# 3. Daily Check-in - 2 Days Since Last Response
# =============================================================================

def trigger_daily_check_2_days(user_id: int, user_name: str):
    """
    Queue daily check-in for user who hasn't responded in 2 days.

    Args:
        user_id: Target user ID
        user_name: User's name (from user.full_name)
    """
    notification = _create_notification_from_template(
        NotificationTypes.DAILY_CHECK_2_DAYS,
        text_params={"user_name": user_name},
    )
    queue_notification_sync(user_id, notification)
    logger.info(f"Queued 2-day daily check-in for user {user_id}")


# =============================================================================
# 4. Daily Check-in - 3 Days Since Last Response
# =============================================================================

def trigger_daily_check_3_days(user_id: int):
    """
    Queue daily check-in for user who hasn't responded in 3 days.
    """
    notification = _create_notification_from_template(
        NotificationTypes.DAILY_CHECK_3_DAYS,
    )
    queue_notification_sync(user_id, notification)
    logger.info(f"Queued 3-day daily check-in for user {user_id}")


# =============================================================================
# 5. Daily Check-in - 4 Days Since Last Response
# =============================================================================

def trigger_daily_check_4_days(user_id: int, condition_name: str):
    """
    Queue daily check-in for user who hasn't responded in 4 days.

    Args:
        user_id: Target user ID
        condition_name: User's leading condition label
    """
    notification = _create_notification_from_template(
        NotificationTypes.DAILY_CHECK_4_DAYS,
        text_params={"condition_name": condition_name},
    )
    queue_notification_sync(user_id, notification)
    logger.info(f"Queued 4-day daily check-in for user {user_id}")


# =============================================================================
# 6. Daily Check-in - 5+ Days Since Last Response (With Score)
# =============================================================================

def trigger_daily_check_5_plus_days(user_id: int, score: int, assessment: str):
    """
    Queue daily check-in for user who hasn't responded in 5+ days.
    Includes their latest juli score.

    Args:
        user_id: Target user ID
        score: User's latest juli score
        assessment: Score assessment (excellent, good, fair, poor)
    """
    notification = _create_notification_from_template(
        NotificationTypes.DAILY_CHECK_5_PLUS_DAYS,
        text_params={"score": score, "assessment": assessment},
    )
    queue_notification_sync(user_id, notification)
    logger.info(f"Queued 5+-day daily check-in with score for user {user_id}")


# =============================================================================
# 7. Admin Broadcast (custom notification)
# =============================================================================

def trigger_broadcast_notification(user_id: int, title: str, text: str):
    """
    Queue a broadcast/admin notification with custom content.
    No template used - fully custom title and text.
    """
    notification = NotificationService.create_notification(
        title=title,
        text=text,
    )
    queue_notification_sync(user_id, notification)
    logger.debug(f"Queued broadcast notification for user {user_id}")


# =============================================================================
# Generic custom notification (for other use cases)
# =============================================================================

def trigger_custom_notification(
    user_id: int,
    title: str,
    text: str,
    notification_type: str,
    extra_data: dict = None,
    aps_data: dict = None,
):
    """
    Queue a custom notification with flexible parameters.
    """
    data = {"type": notification_type}
    if extra_data:
        data.update(extra_data)

    notification = NotificationService.create_notification(
        title=title,
        text=text,
        data=data,
        aps_data=aps_data,
    )
    queue_notification_sync(user_id, notification)
    logger.debug(f"Queued {notification_type} notification for user {user_id}")
