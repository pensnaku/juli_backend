"""Scheduler job for processing user reminders"""
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.core.database import SessionLocal
from app.core.scheduler import scheduler
from app.features.auth.domain import UserReminder, UserSettings
from app.features.medication.domain.entities import MedicationAdherence, AdherenceStatus
from app.features.medication.repository import MedicationAdherenceRepository

logger = logging.getLogger(__name__)

# Run every minute to check for reminders
SCHEDULER_INTERVAL_MINUTES = 1

# Default timezone for users without timezone setting
DEFAULT_TIMEZONE = "UTC"


def process_reminders_job():
    """
    Cron job to process user reminders.

    Runs every minute. For each active reminder:
    1. Converts current UTC time to user's local timezone
    2. Checks if reminder time matches current local time (hour + minute)
    3. If match and not already triggered today, processes the reminder
    4. Updates last_triggered_at to prevent duplicate processing

    Currently handles:
    - medication_reminder: Creates adherence record with NOT_SET status
    """
    logger.debug("Starting reminder processing job...")

    db = SessionLocal()
    try:
        utc_now = datetime.now(timezone.utc)

        # Query active reminders with user timezone (LEFT JOIN to include users without settings)
        reminders_with_tz = (
            db.query(UserReminder, UserSettings.timezone)
            .outerjoin(UserSettings, UserReminder.user_id == UserSettings.user_id)
            .filter(UserReminder.is_active == True)
            .all()
        )

        if not reminders_with_tz:
            logger.debug("No active reminders with timezone found")
            return

        processed_count = 0
        skipped_count = 0

        for reminder, user_timezone in reminders_with_tz:
            try:
                # Use default timezone if user hasn't set one
                tz_name = user_timezone or DEFAULT_TIMEZONE
                user_tz = ZoneInfo(tz_name)
                local_now = utc_now.astimezone(user_tz)

                # Check if reminder time matches current local time (hour and minute)
                if (reminder.time.hour != local_now.hour or
                        reminder.time.minute != local_now.minute):
                    continue

                # Check if already triggered today (in user's local timezone)
                if reminder.last_triggered_at:
                    last_triggered_local = reminder.last_triggered_at.astimezone(user_tz)
                    if last_triggered_local.date() == local_now.date():
                        skipped_count += 1
                        continue

                # Process the reminder based on type
                _process_reminder(db, reminder, local_now.date())

                # Update last_triggered_at
                reminder.last_triggered_at = utc_now
                processed_count += 1

            except Exception as e:
                logger.error(
                    f"Error processing reminder {reminder.id} for user {reminder.user_id}: {e}"
                )

        db.commit()

        if processed_count > 0 or skipped_count > 0:
            logger.info(
                f"Reminder job completed: {processed_count} processed, {skipped_count} skipped (already triggered)"
            )

    except Exception as e:
        logger.error(f"Reminder job failed: {e}")
        db.rollback()
    finally:
        db.close()


def _process_reminder(db, reminder: UserReminder, target_date):
    """Process a single reminder based on its type."""
    if reminder.reminder_type == "medication_reminder":
        _process_medication_reminder(db, reminder, target_date)
    # Add other reminder types here as needed
    # elif reminder.reminder_type == "daily_check_in":
    #     _process_daily_check_in(db, reminder, target_date)


def _process_medication_reminder(db, reminder: UserReminder, target_date):
    """
    Process a medication reminder by creating an adherence record.

    Creates a medication adherence record with NOT_SET status if one
    doesn't already exist for this medication on this date.
    """
    if not reminder.medication_id:
        logger.warning(
            f"Medication reminder {reminder.id} has no medication_id, skipping"
        )
        return

    repo = MedicationAdherenceRepository(db)

    # Check if adherence record already exists for this date
    existing = repo.get_by_user_medication_date(
        user_id=reminder.user_id,
        medication_id=reminder.medication_id,
        target_date=target_date,
    )

    if existing:
        logger.debug(
            f"Adherence record already exists for user {reminder.user_id}, "
            f"medication {reminder.medication_id}, date {target_date}"
        )
        return

    # Create new adherence record with NOT_SET status
    adherence = MedicationAdherence(
        user_id=reminder.user_id,
        medication_id=reminder.medication_id,
        date=target_date,
        status=AdherenceStatus.NOT_SET,
    )
    db.add(adherence)
    db.flush()

    logger.info(
        f"Created adherence record for user {reminder.user_id}, "
        f"medication {reminder.medication_id}, date {target_date}"
    )


def register_reminder_job():
    """Register the reminder processing job with the scheduler."""
    scheduler.add_job(
        process_reminders_job,
        'interval',
        minutes=SCHEDULER_INTERVAL_MINUTES,
        id='reminder_processing',
        name='Process user reminders',
        replace_existing=True,
    )
    logger.info(
        f"Registered reminder job to run every {SCHEDULER_INTERVAL_MINUTES} minute(s)"
    )
