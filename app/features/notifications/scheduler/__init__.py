"""Notification scheduler integration"""
from app.features.notifications.scheduler.notification_triggers import (
    trigger_medication_reminder,
    trigger_daily_check_default,
    trigger_daily_check_2_days,
    trigger_daily_check_3_days,
    trigger_daily_check_4_days,
    trigger_daily_check_5_plus_days,
    trigger_broadcast_notification,
    trigger_custom_notification,
)
from app.features.notifications.scheduler.daily_push_scheduler import (
    register_daily_push_job,
    process_daily_push_job,
)

__all__ = [
    "trigger_medication_reminder",
    "trigger_daily_check_default",
    "trigger_daily_check_2_days",
    "trigger_daily_check_3_days",
    "trigger_daily_check_4_days",
    "trigger_daily_check_5_plus_days",
    "trigger_broadcast_notification",
    "trigger_custom_notification",
    "register_daily_push_job",
    "process_daily_push_job",
]
