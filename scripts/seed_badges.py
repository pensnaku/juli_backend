"""
Seed script for Daily Dare Badges

Run this script to populate the badges table with all badge definitions.

Usage:
    docker exec juli_api python scripts/seed_badges.py
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal

# Import all models to resolve relationship dependencies
# These imports ensure SQLAlchemy can resolve all string references in relationships
from app.features.auth.domain.entities.user import User
from app.features.auth.domain.entities.user_settings import UserSettings
from app.features.auth.domain.entities.user_condition import UserCondition
from app.features.auth.domain.entities.user_reminder import UserReminder
from app.features.auth.domain.entities.user_medication import UserMedication
from app.features.auth.domain.entities.user_tracking_topic import UserTrackingTopic
from app.shared.questionnaire.entities.questionnaire_completion import QuestionnaireCompletion
from app.features.journal.domain.entities.journal_entry import JournalEntry
from app.features.observations.domain.entities.observation import Observation
from app.features.juli_score.domain.entities.juli_score import JuliScore
from app.features.daily_dare_badges.domain.entities.daily_dare_badge import DailyDareBadge
from app.features.daily_dare_badges.domain.entities.user_daily_dare_badge import UserDailyDareBadge


# ==================== Regular Badges ====================

REGULAR_BADGES = [
    # Strong Start badges (consecutive days with ANY dare completed)
    {
        'name': 'Strong Start',
        'slug': 'strong-start1',
        'description': '2 consecutive active days',
        'pre_text': 'Complete any dare for 2 days in a row',
        'post_text': 'You completed dares for 2 days in a row!',
        'type': 'regular',
        'level': 1,
        'priority': 1,
        'can_be_multiple': True,
    },
    {
        'name': 'Strong Start',
        'slug': 'strong-start2',
        'description': '5 consecutive active days',
        'pre_text': 'Complete any dare for 5 days in a row',
        'post_text': 'You completed dares for 5 days in a row!',
        'type': 'regular',
        'level': 2,
        'priority': 4,
        'can_be_multiple': True,
    },
    {
        'name': 'Strong Start',
        'slug': 'strong-start3',
        'description': '10 consecutive active days',
        'pre_text': 'Complete any dare for 10 days in a row',
        'post_text': 'You completed dares for 10 days in a row!',
        'type': 'regular',
        'level': 3,
        'priority': 5,
        'can_be_multiple': True,
    },
    {
        'name': 'Strong Start',
        'slug': 'strong-start4',
        'description': '15 consecutive active days',
        'pre_text': 'Complete any dare for 15 days in a row',
        'post_text': 'You completed dares for 15 days in a row!',
        'type': 'regular',
        'level': 4,
        'priority': 6,
        'can_be_multiple': True,
    },

    # Daredevil badges (consecutive days with ALL 4 dares completed)
    {
        'name': 'Daredevil',
        'slug': 'daredevil1',
        'description': 'Complete all 4 dares in a day',
        'pre_text': 'Complete all 4 daily dares',
        'post_text': 'You completed all 4 dares!',
        'type': 'regular',
        'level': 1,
        'priority': 2,
        'can_be_multiple': True,
    },
    {
        'name': 'Daredevil',
        'slug': 'daredevil2',
        'description': 'Complete all 4 dares for 7 days in a row',
        'pre_text': 'Complete all 4 dares for 7 consecutive days',
        'post_text': 'You completed all 4 dares for a whole week!',
        'type': 'regular',
        'level': 2,
        'priority': 10,
        'can_be_multiple': True,
    },
    {
        'name': 'Daredevil',
        'slug': 'daredevil3',
        'description': 'Complete all 4 dares for 14 days in a row',
        'pre_text': 'Complete all 4 dares for 14 consecutive days',
        'post_text': 'You completed all 4 dares for 2 weeks!',
        'type': 'regular',
        'level': 3,
        'priority': 12,
        'can_be_multiple': True,
    },
    {
        'name': 'Daredevil',
        'slug': 'daredevil4',
        'description': 'Complete all 4 dares for 30 days in a row',
        'pre_text': 'Complete all 4 dares for 30 consecutive days',
        'post_text': 'You completed all 4 dares for a whole month!',
        'type': 'regular',
        'level': 4,
        'priority': 13,
        'can_be_multiple': True,
    },
    {
        'name': 'Daredevil',
        'slug': 'daredevil5',
        'description': 'Complete all 4 dares for 60 days in a row',
        'pre_text': 'Complete all 4 dares for 60 consecutive days',
        'post_text': 'You completed all 4 dares for 2 months!',
        'type': 'regular',
        'level': 5,
        'priority': 17,
        'can_be_multiple': True,
    },

    # Streak badges (long consecutive periods with ANY dare)
    {
        'name': 'Streak',
        'slug': 'streak1',
        'description': '20 consecutive active days',
        'pre_text': 'Complete any dare for 20 days in a row',
        'post_text': 'You have a 20-day streak!',
        'type': 'regular',
        'level': 1,
        'priority': 7,
        'can_be_multiple': True,
    },
    {
        'name': 'Streak',
        'slug': 'streak2',
        'description': '50 consecutive active days',
        'pre_text': 'Complete any dare for 50 days in a row',
        'post_text': 'You have a 50-day streak!',
        'type': 'regular',
        'level': 2,
        'priority': 9,
        'can_be_multiple': True,
    },
    {
        'name': 'Streak',
        'slug': 'streak3',
        'description': '100 consecutive active days',
        'pre_text': 'Complete any dare for 100 days in a row',
        'post_text': 'You have a 100-day streak!',
        'type': 'regular',
        'level': 3,
        'priority': 11,
        'can_be_multiple': True,
    },
    {
        'name': 'Streak',
        'slug': 'streak4',
        'description': '180 consecutive active days',
        'pre_text': 'Complete any dare for 180 days in a row',
        'post_text': 'You have a 6-month streak!',
        'type': 'regular',
        'level': 4,
        'priority': 14,
        'can_be_multiple': True,
    },
    {
        'name': 'Streak',
        'slug': 'streak5',
        'description': '365 consecutive active days',
        'pre_text': 'Complete any dare for 365 days in a row',
        'post_text': 'You have a 1-year streak!',
        'type': 'regular',
        'level': 5,
        'priority': 16,
        'can_be_multiple': True,
    },

    # Points badges
    {
        'name': 'Decade',
        'slug': 'decade',
        'description': 'Earn 10 total points',
        'pre_text': 'Earn 10 points from completing dares',
        'post_text': 'You earned your first 10 points!',
        'type': 'regular',
        'level': None,
        'priority': 3,
        'can_be_multiple': False,
    },
    {
        'name': 'Century',
        'slug': 'century',
        'description': 'Earn 100 total points',
        'pre_text': 'Earn 100 points from completing dares',
        'post_text': 'You earned 100 points!',
        'type': 'regular',
        'level': None,
        'priority': 8,
        'can_be_multiple': False,
    },
    {
        'name': 'Millenium',
        'slug': 'millenium',
        'description': 'Earn 1000 total points',
        'pre_text': 'Earn 1000 points from completing dares',
        'post_text': 'You earned 1000 points!',
        'type': 'regular',
        'level': None,
        'priority': 15,
        'can_be_multiple': True,
    },

    # The Warrior badge (first access)
    {
        'name': 'The Warrior',
        'slug': 'the-warrior',
        'description': 'Welcome to the app!',
        'pre_text': 'Join the app',
        'post_text': 'Welcome, Warrior! Your journey begins now.',
        'type': 'regular',
        'level': None,
        'priority': 0,
        'can_be_multiple': False,
    },
]


# ==================== Sample Monthly Badges ====================

MONTHLY_BADGES = [
    {
        'name': 'January Challenge',
        'slug': 'january-2025',
        'description': 'Complete 50 dares in January 2025',
        'pre_text': 'Complete 50 dares this month!',
        'post_text': 'You completed the January Challenge!',
        'type': 'monthly',
        'month': 1,
        'year': 2025,
        'can_be_multiple': False,
        'criteria_category': None,
        'criteria_expected_count': 50,
    },
    {
        'name': 'Sleep Month',
        'slug': 'sleep-month-feb-2025',
        'description': 'Complete 10 Sleep dares in February 2025',
        'pre_text': 'Complete 10 Sleep dares this month!',
        'post_text': 'You mastered your sleep this month!',
        'type': 'monthly',
        'month': 2,
        'year': 2025,
        'can_be_multiple': False,
        'criteria_category': 'sleep',
        'criteria_expected_count': 10,
    },
]


def seed_badges():
    """Seed all badges into the database."""
    db = SessionLocal()

    try:
        # Check if badges already exist
        existing = db.query(DailyDareBadge).count()
        if existing > 0:
            print(f"Found {existing} existing badges. Skipping seed.")
            print("To re-seed, delete existing badges first.")
            return

        # Insert regular badges
        print("Seeding regular badges...")
        for badge_data in REGULAR_BADGES:
            badge = DailyDareBadge(**badge_data)
            db.add(badge)
            print(f"  Added: {badge_data['slug']}")

        # Insert monthly badges
        print("Seeding monthly badges...")
        for badge_data in MONTHLY_BADGES:
            badge = DailyDareBadge(**badge_data)
            db.add(badge)
            print(f"  Added: {badge_data['slug']}")

        db.commit()
        print(f"\nSuccessfully seeded {len(REGULAR_BADGES)} regular badges and {len(MONTHLY_BADGES)} monthly badges.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding badges: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    seed_badges()
