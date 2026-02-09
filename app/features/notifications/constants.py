"""
Push notification templates and constants.

All notification text matches the spec in docs/PUSH_NOTIFICATIONS.md
"""

from typing import Dict, Any


# =============================================================================
# Score Assessment Ranges
# =============================================================================

SCORE_ASSESSMENT_RANGES = {
    (80, 100): "excellent",
    (60, 79): "good",
    (40, 59): "fair",
    (0, 39): "poor",
}


def get_score_assessment(score: int) -> str:
    """Get assessment label for a juli score"""
    for (low, high), label in SCORE_ASSESSMENT_RANGES.items():
        if low <= score <= high:
            return label
    return "fair"


# =============================================================================
# Notification Templates
# =============================================================================

NOTIFICATION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # 1. Medication Reminder
    # -------------------------------------------------------------------------
    "medication_reminder": {
        "title": "Time to talk to juli",
        "text": "Did you take {medication_name} today?",
        "data": {
            "action": "medicationNotification",
            # Dynamic fields added at runtime: medicationId, medicationName, time
        },
        "aps_data": {
            "category": "MEDICATION_CATEGORY",
        },
    },

    # -------------------------------------------------------------------------
    # 2. Daily Check-in - Default (no recent responses)
    # -------------------------------------------------------------------------
    "daily_check_default": {
        "title": "juli's Here to Help",
        "text": "Providing juli with as much information as possible will help us help you. Pop into juli to answer a few daily questions.",
        "data": {
            "action": "openMessenger",
            "tabIndex": 1,
        },
        "aps_data": {
            "badge": 1,
        },
    },

    # -------------------------------------------------------------------------
    # 3. Daily Check-in - 2 Days Since Last Response
    # -------------------------------------------------------------------------
    "daily_check_2_days": {
        "title": "Time to Talk to juli",
        "text": "Hey {user_name}, juli didn't hear from you yesterday. How are you doing?",
        "data": {
            "action": "openMessenger",
            "tabIndex": 1,
        },
        "aps_data": {
            "badge": 1,
        },
    },

    # -------------------------------------------------------------------------
    # 4. Daily Check-in - 3 Days Since Last Response
    # -------------------------------------------------------------------------
    "daily_check_3_days": {
        "title": "Check in with juli",
        "text": "Just checking to see how your past few days have been. juli would love to hear from you!",
        "data": {
            "action": "openMessenger",
            "tabIndex": 1,
        },
        "aps_data": {
            "badge": 1,
        },
    },

    # -------------------------------------------------------------------------
    # 5. Daily Check-in - 4 Days Since Last Response
    # -------------------------------------------------------------------------
    "daily_check_4_days": {
        "title": "Share Your Progress",
        "text": "Did you know that the best way to keep {condition_name} under control is through a daily routine? Share your current progress so juli can better help you.",
        "data": {
            "action": "openMessenger",
            "tabIndex": 1,
        },
        "aps_data": {
            "badge": 1,
        },
    },

    # -------------------------------------------------------------------------
    # 6. Daily Check-in - 5+ Days Since Last Response (With Score)
    # -------------------------------------------------------------------------
    "daily_check_5_plus_days": {
        "title": "What's the Score?",
        "text": "juli misses you. Your latest juli score was {score}. That qualifies as {assessment} for your condition. juli wonders what your score would be now?",
        "data": {
            "action": "openMessenger",
            "tabIndex": 1,
        },
        "aps_data": {
            "badge": 1,
        },
    },
}


# =============================================================================
# Notification Type Keys (for easy reference)
# =============================================================================

class NotificationTypes:
    """Notification type identifiers"""
    MEDICATION_REMINDER = "medication_reminder"
    DAILY_CHECK_DEFAULT = "daily_check_default"
    DAILY_CHECK_2_DAYS = "daily_check_2_days"
    DAILY_CHECK_3_DAYS = "daily_check_3_days"
    DAILY_CHECK_4_DAYS = "daily_check_4_days"
    DAILY_CHECK_5_PLUS_DAYS = "daily_check_5_plus_days"
