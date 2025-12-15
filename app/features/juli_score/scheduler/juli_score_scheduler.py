"""Scheduler job for Juli Score calculation"""
import logging
from datetime import date

from app.core.database import SessionLocal
from app.core.scheduler import scheduler
from app.features.juli_score.constants import SCHEDULER_INTERVAL_MINUTES, ACTIVE_USER_DAYS
from app.features.juli_score.service import JuliScoreService
from app.features.juli_score.repository import JuliScoreRepository

logger = logging.getLogger(__name__)


def calculate_all_scores_job():
    """
    Cron job to calculate Juli Scores for all active users.

    Runs every N minutes (configurable via SCHEDULER_INTERVAL_MINUTES).
    Only processes users who have been active in the last N days.
    """
    logger.info("Starting Juli Score calculation job...")

    db = SessionLocal()
    try:
        repo = JuliScoreRepository(db)
        service = JuliScoreService(db)

        # Get active users with supported conditions
        user_condition_pairs = repo.get_active_users_with_conditions(
            active_days=ACTIVE_USER_DAYS
        )

        if not user_condition_pairs:
            logger.info("No active users with supported conditions found")
            return

        logger.info(f"Processing {len(user_condition_pairs)} user-condition pairs")

        success_count = 0
        skip_count = 0
        error_count = 0
        target_date = date.today()

        for user_id, condition_code in user_condition_pairs:
            try:
                result = service.calculate_and_save_score(
                    user_id, condition_code, target_date
                )
                if result:
                    success_count += 1
                else:
                    skip_count += 1  # Insufficient data or unchanged
            except Exception as e:
                error_count += 1
                logger.error(
                    f"Error calculating score for user {user_id}, "
                    f"condition {condition_code}: {e}"
                )

        logger.info(
            f"Juli Score job completed: {success_count} saved, "
            f"{skip_count} skipped, {error_count} errors"
        )

    except Exception as e:
        logger.error(f"Juli Score job failed: {e}")
    finally:
        db.close()


def register_juli_score_job():
    """Register the Juli Score calculation job with the scheduler"""
    scheduler.add_job(
        calculate_all_scores_job,
        'interval',
        minutes=SCHEDULER_INTERVAL_MINUTES,
        id='juli_score_calculation',
        name='Calculate Juli Scores for active users',
        replace_existing=True,
    )
    logger.info(
        f"Registered Juli Score job to run every {SCHEDULER_INTERVAL_MINUTES} minutes"
    )
