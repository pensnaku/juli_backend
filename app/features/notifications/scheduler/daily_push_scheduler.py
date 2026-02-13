"""Scheduler job for daily check-in push notifications.

Sends engagement-based notifications depending on how many days since
the user last completed a daily questionnaire.
"""

import logging
from datetime import datetime, timezone, timedelta, date
from zoneinfo import ZoneInfo

from app.core.database import SessionLocal
from app.core.scheduler import scheduler
from app.features.auth.domain.entities import UserReminder, UserSettings, User
from app.shared.questionnaire.repositories import QuestionnaireCompletionRepository
from app.features.juli_score.repository import JuliScoreRepository
from app.features.notifications.constants import get_score_assessment
from app.features.notifications.repository import PushSubscriptionRepository
from app.features.notifications.scheduler.notification_triggers import (
    trigger_daily_check_default,
    trigger_daily_check_2_days,
    trigger_daily_check_3_days,
    trigger_daily_check_4_days,
    trigger_daily_check_5_plus_days,
)

logger = logging.getLogger(__name__)

# Scheduler runs every minute to check for daily check-in reminders
SCHEDULER_INTERVAL_MINUTES = 1

# Default timezone for users without timezone setting
DEFAULT_TIMEZONE = "UTC"


def get_days_since_last_completion(db, user_id: int, today: date) -> int:
    """
    Calculate days since user's last daily questionnaire completion.

    Args:
        db: Database session
        user_id: User ID
        today: Today's date in user's local timezone

    Returns:
        Number of days since last completion (0 if completed today, max 30)
    """
    repo = QuestionnaireCompletionRepository(db)

    # Check last 30 days
    start_date = today - timedelta(days=30)
    completions = repo.get_daily_completions_in_range(user_id, start_date, today)

    # Find completed ones (completed_at is not None)
    completed = [c for c in completions if c.completed_at is not None]

    if not completed:
        return 30  # No completions in 30 days

    # Find most recent completion date
    most_recent = max(c.completion_date for c in completed)
    return (today - most_recent).days


def get_leading_condition_name(user: User) -> str:
    """
    Get the user's leading (highest priority) condition name.

    Args:
        user: User entity with conditions relationship

    Returns:
        Condition label from the leading condition
    """
    ordered = user.ordered_conditions
    return ordered[0].condition_label


def get_latest_score_with_assessment(db, user: User) -> tuple | None:
    """
    Get user's latest juli score and assessment label.

    Args:
        db: Database session
        user: User entity with conditions relationship

    Returns:
        Tuple of (score: int, assessment: str) or None if no score available
    """
    ordered_conditions = user.ordered_conditions
    if not ordered_conditions:
        return None

    repo = JuliScoreRepository(db)

    # Try to get score for leading condition first, then others
    for condition in ordered_conditions:
        score_record = repo.get_latest_juli_score(user.id, condition.condition_code)
        if score_record:
            assessment = get_score_assessment(score_record.score)
            return (score_record.score, assessment)

    return None


def _send_daily_notification(db, user: User, days_since: int):
    """
    Send the appropriate daily notification based on engagement level.

    Args:
        db: Database session
        user: User entity
        days_since: Days since last questionnaire completion
    """
    if days_since <= 1:
        # Default message for users with recent or no engagement data
        trigger_daily_check_default(user.id)

    elif days_since == 2:
        # 2 days - personalized with name
        user_name = user.full_name or "there"
        trigger_daily_check_2_days(user.id, user_name)

    elif days_since == 3:
        # 3 days - encouragement message
        trigger_daily_check_3_days(user.id)

    elif days_since == 4:
        # 4 days - condition-specific message
        condition_name = get_leading_condition_name(user)
        trigger_daily_check_4_days(user.id, condition_name)

    else:
        # 5+ days - include juli score if available
        score_data = get_latest_score_with_assessment(db, user)
        if score_data:
            score, assessment = score_data
            trigger_daily_check_5_plus_days(user.id, score, assessment)
        else:
            # No score available - fall back to 4-day message
            condition_name = get_leading_condition_name(user)
            trigger_daily_check_4_days(user.id, condition_name)


def process_daily_push_job():
    """
    Process daily check-in push notifications.

    Runs every minute. For each user with an active daily_check_in reminder:
    1. Check if reminder time matches current time in user's timezone
    2. Check if not already triggered today
    3. Calculate days since last questionnaire completion
    4. Send appropriate notification based on engagement level
    """
    logger.info("Daily push notification job running...")

    db = SessionLocal()
    try:
        utc_now = datetime.now(timezone.utc)

        # Query daily_check_in reminders with user data
        reminders_with_data = (
            db.query(UserReminder, UserSettings.timezone, User)
            .join(User, UserReminder.user_id == User.id)
            .outerjoin(UserSettings, UserReminder.user_id == UserSettings.user_id)
            .filter(
                UserReminder.is_active == True,
                UserReminder.reminder_type == "daily_check_in",
            )
            .all()
        )

        if not reminders_with_data:
            logger.debug("No active daily_check_in reminders found")
            return

        processed_count = 0
        skipped_count = 0

        for reminder, user_timezone, user in reminders_with_data:
            try:
                # Use default timezone if user hasn't set one
                tz_name = user_timezone or DEFAULT_TIMEZONE
                user_tz = ZoneInfo(tz_name)
                local_now = utc_now.astimezone(user_tz)

                # Check if reminder time matches current local time (exact minute)
                if (
                    reminder.time.hour != local_now.hour
                    or reminder.time.minute != local_now.minute
                ):
                    continue

                # Check if already triggered today (in user's local timezone)
                if reminder.last_triggered_at:
                    last_triggered_local = reminder.last_triggered_at.astimezone(
                        user_tz
                    )
                    if last_triggered_local.date() == local_now.date():
                        skipped_count += 1
                        continue

                # Skip if user has no push subscriptions (don't update last_triggered_at)
                sub_repo = PushSubscriptionRepository(db)
                if not sub_repo.get_by_user_id(user.id):
                    logger.info(f"No push subscriptions for user {user.id}, skipping")
                    continue

                # Calculate days since last questionnaire completion
                days_since = get_days_since_last_completion(
                    db, user.id, local_now.date()
                )

                # Send appropriate notification
                _send_daily_notification(db, user, days_since)

                # Update last_triggered_at only after notification is queued
                reminder.last_triggered_at = utc_now
                processed_count += 1

            except Exception as e:
                logger.error(
                    f"Error processing daily push for user {reminder.user_id}: {e}"
                )

        db.commit()

        if processed_count > 0 or skipped_count > 0:
            logger.info(
                f"Daily push job completed: {processed_count} sent, "
                f"{skipped_count} skipped (already triggered)"
            )

    except Exception as e:
        logger.error(f"Daily push job failed: {e}")
        db.rollback()
    finally:
        db.close()


def register_daily_push_job():
    """Register the daily push notification job with the scheduler."""
    scheduler.add_job(
        process_daily_push_job,
        "cron",
        second=0,  # Run at second 0 of every minute
        id="daily_push_notifications",
        name="Process daily check-in push notifications",
        replace_existing=True,
    )
    logger.info("Registered daily push job to run at the start of every minute")
    print("[Daily Push] Registered job to run at the start of every minute")
