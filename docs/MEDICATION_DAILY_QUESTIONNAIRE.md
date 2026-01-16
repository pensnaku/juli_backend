# Medication in Daily Check-in Questionnaire

This document explains how medication tracking works within the daily check-in flow.

---

## Implementation Plan

### Overview

Add medication adherence tracking to the daily questionnaire flow. Users with active medications will see a medication section where they can mark each medication as taken/not taken.

### Current State (What Already Exists)

| Component | Location | Status |
|-----------|----------|--------|
| `UserMedication` entity | `app/features/auth/domain/entities/user_medication.py` | ✅ Exists |
| `MedicationAdherence` entity | `app/features/medication/domain/entities/medication_adherence.py` | ✅ Exists |
| Adherence API endpoints | `app/features/medication/api/router.py` | ✅ Exists |
| `AdherenceStatus` enum | `medication_adherence.py` | ✅ Exists (NOT_SET, TAKEN, NOT_TAKEN, PARTLY_TAKEN) |

### What Needs to Be Built

| Step | Task | Files to Modify |
|------|------|-----------------|
| 1 | Add medication questionnaire builder | `questionnaire_service.py` |
| 2 | Add medication answer handler | `answer_handler.py` |
| 3 | Add repository helper methods | `medication_adherence_repository.py` |
| 4 | Insert medication section into daily flow | `questionnaire_service.py` |

---

## Step 1: Add Medication Questionnaire Builder

**File:** `app/shared/questionnaire/questionnaire_service.py`

Add method to build the medication questionnaire dynamically based on user's active medications:

```python
def _build_medication_questionnaire(
    self, user_id: int, target_date: date
) -> Optional[Dict[str, Any]]:
    """
    Build medication adherence questionnaire for user's active medications.

    Returns None if user has no active medications.
    """
    # Get user's active medications
    medications = self.medication_repo.get_active_by_user_id(user_id)
    if not medications:
        return None

    # Get existing adherence records for today
    adherence_repo = MedicationAdherenceRepository(self.db)
    existing_adherence = adherence_repo.get_daily_adherence_map(user_id, target_date)

    questions = []
    for med in medications:
        # Get current status if already answered today
        current_status = existing_adherence.get(med.id)
        current_value = None
        if current_status:
            current_value = current_status.status.value if current_status.status != AdherenceStatus.NOT_SET else None

        questions.append({
            "id": f"medication-{med.id}",
            "text": f"Did you take {med.medication_name}?",
            "help_text": med.dosage if med.dosage else None,
            "type": "single_choice",
            "options": [
                {"value": "taken", "label": "Yes, I took it"},
                {"value": "not_taken", "label": "No, I didn't take it"},
                {"value": "partly_taken", "label": "I took some of it"},
            ],
            "validation": {"required": False},
            "prefilled_value": current_value,
            "metadata": {
                "medication_id": med.id,
                "medication_name": med.medication_name,
            }
        })

    return {
        "id": "medication",
        "title": "Medication",
        "description": "Did you take your medications today?",
        "questions": questions,
    }
```

**Dependencies to add:**
```python
from app.features.medication.repository import MedicationAdherenceRepository
from app.features.medication.domain.entities import AdherenceStatus
```

---

## Step 2: Add Medication Answer Handler

**File:** `app/shared/questionnaire/answer_handler.py`

Add handler for medication answers in `_process_answer`:

```python
# In _process_answer method, add:
elif question_id.startswith("medication-"):
    # Extract medication_id from question_id (format: "medication-{id}")
    try:
        medication_id = int(question_id.split("-")[1])
        self._handle_medication_adherence(user.id, medication_id, answer)
    except (ValueError, IndexError):
        logger.warning(f"Invalid medication question ID: {question_id}")
```

Add the handler method:

```python
def _handle_medication_adherence(
    self, user_id: int, medication_id: int, status_value: str
) -> None:
    """
    Create or update medication adherence record for today.

    Args:
        user_id: User ID
        medication_id: Medication ID
        status_value: One of "taken", "not_taken", "partly_taken"
    """
    from app.features.medication.repository import MedicationAdherenceRepository
    from app.features.medication.domain.entities import AdherenceStatus
    from datetime import date

    adherence_repo = MedicationAdherenceRepository(self.db)

    # Map string value to enum
    status_map = {
        "taken": AdherenceStatus.TAKEN,
        "not_taken": AdherenceStatus.NOT_TAKEN,
        "partly_taken": AdherenceStatus.PARTLY_TAKEN,
    }
    status = status_map.get(status_value, AdherenceStatus.NOT_SET)

    # Upsert adherence record for today
    adherence_repo.upsert_adherence(
        user_id=user_id,
        medication_id=medication_id,
        target_date=date.today(),
        status=status,
    )
```

---

## Step 3: Add Repository Methods

**File:** `app/features/medication/repository/medication_adherence_repository.py`

Add these methods:

```python
def upsert_adherence(
    self,
    user_id: int,
    medication_id: int,
    target_date: date,
    status: AdherenceStatus,
    notes: Optional[str] = None,
) -> MedicationAdherence:
    """
    Create or update adherence record for a specific medication and date.
    """
    existing = self.db.query(MedicationAdherence).filter(
        MedicationAdherence.user_id == user_id,
        MedicationAdherence.medication_id == medication_id,
        MedicationAdherence.date == target_date,
    ).first()

    if existing:
        existing.status = status
        if notes is not None:
            existing.notes = notes
        self.db.flush()
        return existing

    adherence = MedicationAdherence(
        user_id=user_id,
        medication_id=medication_id,
        date=target_date,
        status=status,
        notes=notes,
    )
    self.db.add(adherence)
    self.db.flush()
    return adherence


def get_daily_adherence_map(
    self, user_id: int, target_date: date
) -> Dict[int, MedicationAdherence]:
    """
    Get all adherence records for a user on a specific date.
    Returns dict mapping medication_id -> adherence record.
    """
    records = self.db.query(MedicationAdherence).filter(
        MedicationAdherence.user_id == user_id,
        MedicationAdherence.date == target_date,
    ).all()

    return {r.medication_id: r for r in records}
```

---

## Step 4: Insert Medication Section into Daily Flow

**File:** `app/shared/questionnaire/questionnaire_service.py`

In `get_daily_questionnaires` method, add medication section after mood and before condition-specific questionnaires:

```python
def get_daily_questionnaires(
    self, user_id: int, target_date: date
) -> Optional[Dict[str, Any]]:
    # ... existing code ...

    questionnaires = []

    # Always include mood questionnaire first (for all users)
    mood_questionnaire = self._build_mood_questionnaire(user_id, target_date)
    if mood_questionnaire:
        questionnaires.append(mood_questionnaire)

    # Add medication questionnaire if user has active medications
    medication_questionnaire = self._build_medication_questionnaire(user_id, target_date)
    if medication_questionnaire:
        questionnaires.append(medication_questionnaire)

    # Add student wellbeing questionnaire after mood if user is a student
    # ... rest of existing code ...
```

---

## Questionnaire Order

After implementation, the daily questionnaire order will be:

1. **Mood** - Always first
2. **Medication** - If user has active medications
3. **Student Wellbeing** - If user is a student
4. **Condition-specific** - Based on user's conditions (in priority order)
5. **Individual Tracking** - If user has active tracking topics
6. **Journal** - Always last

---

## Data Model Mapping

### Existing Entities → Documentation Mapping

| Documentation Term | Codebase Entity | Table |
|--------------------|-----------------|-------|
| Schedule | `UserMedication` | `user_medications` |
| Adherence | `MedicationAdherence` | `medication_adherence` |
| Notification Times | `UserReminder` (type="medication_reminder") | `user_reminders` |

### UserMedication (Schedule)

```
user_medications
├── id (PK)
├── user_id (FK → users)
├── medication_name
├── dosage
├── times_per_day
├── notes
├── is_active
├── reminder_enabled
├── created_at
└── updated_at
```

### MedicationAdherence

```
medication_adherence
├── id (PK)
├── user_id (FK → users)
├── medication_id (FK → user_medications)
├── date
├── status (NOT_SET | TAKEN | NOT_TAKEN | PARTLY_TAKEN)
├── notes
├── created_at
└── updated_at
└── UNIQUE(user_id, medication_id, date)
```

---

## API Response Format

### Daily Questionnaire with Medication Section

```json
{
  "title": "Daily Check-in",
  "description": "Your daily health questions",
  "completion_date": "2024-01-15",
  "questionnaires": [
    {
      "id": "mood",
      "title": "Mood",
      "questions": [...]
    },
    {
      "id": "medication",
      "title": "Medication",
      "description": "Did you take your medications today?",
      "questions": [
        {
          "id": "medication-123",
          "text": "Did you take Aspirin 100mg?",
          "help_text": "100mg daily",
          "type": "single_choice",
          "options": [
            {"value": "taken", "label": "Yes, I took it"},
            {"value": "not_taken", "label": "No, I didn't take it"},
            {"value": "partly_taken", "label": "I took some of it"}
          ],
          "validation": {"required": false},
          "prefilled_value": "taken",
          "metadata": {
            "medication_id": 123,
            "medication_name": "Aspirin 100mg"
          }
        }
      ]
    },
    {
      "id": "journal",
      "title": "Journal",
      "questions": [...]
    }
  ]
}
```

---

## Testing Checklist

- [ ] User with no medications → medication section not shown
- [ ] User with active medications → medication section appears after mood
- [ ] User with inactive medications only → medication section not shown
- [ ] Prefilled values load correctly for already-answered medications
- [ ] Submitting answers creates/updates adherence records
- [ ] Adherence status values map correctly (taken/not_taken/partly_taken)
- [ ] Medication section respects questionnaire order (after mood, before conditions)

---

## Files to Modify Summary

| File | Changes |
|------|---------|
| `app/shared/questionnaire/questionnaire_service.py` | Add `_build_medication_questionnaire()`, add to `get_daily_questionnaires()` |
| `app/shared/questionnaire/answer_handler.py` | Add medication-* question handler |
| `app/features/medication/repository/medication_adherence_repository.py` | Add `upsert_adherence()`, `get_daily_adherence_map()` |

---

## Auto-Creation of Adherence Records via Reminder Scheduler

### Overview

A scheduler job runs every minute to:
1. Find medication reminders that are due (based on user's local time)
2. Create adherence records with `NOT_SET` status
3. (Future) Trigger push notifications

### Why Reminder Scheduler?

| Entity | Purpose |
|--------|---------|
| `UserMedication` | The medication itself (Aspirin, dosage, etc.) |
| `UserReminder` | The notification times for a medication (08:00, 20:00) |
| `MedicationAdherence` | Daily record of whether medication was taken |

The scheduler processes **reminders** (not medications) because:
- Reminders have the exact `time` to match against
- Reminders link to specific medications via `medication_id`
- One medication can have multiple reminder times

### Flow

```
Every Minute:
┌─────────────────────────────────────────────────────────────┐
│ 1. Get all active medication reminders                      │
│    JOIN with user_settings to get timezone                  │
│                                                             │
│ 2. For each reminder:                                       │
│    - Convert current UTC → user's local time                │
│    - Check if local time matches reminder time (HH:MM)      │
│                                                             │
│ 3. If match and no adherence record exists for today:       │
│    - Create adherence record with status = NOT_SET          │
│    - (Future) Send push notification                        │
└─────────────────────────────────────────────────────────────┘
```

### Timezone Handling (Compute On-the-Fly)

Instead of storing UTC times, we compute timezone conversion at runtime:

```python
# Reminder stored as local time: 08:00
# User timezone: "America/New_York" (UTC-5)
# Current UTC: 13:00

# Convert UTC to user's local time:
# 13:00 UTC → 08:00 America/New_York

# Match: 08:00 == 08:00 ✓ → Create adherence record
```

**Why on-the-fly?**
- User timezone can change (travel, DST, correction)
- No stale data to maintain
- No extra columns needed

### Implementation

**New File:** `app/features/medication/scheduler/medication_reminder_scheduler.py`

```python
"""Scheduler job for processing medication reminders and creating adherence records"""
import logging
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import SessionLocal
from app.core.scheduler import scheduler
from app.features.auth.domain.entities import UserReminder, UserSettings
from app.features.medication.domain.entities import MedicationAdherence, AdherenceStatus
from app.features.medication.repository import MedicationAdherenceRepository

logger = logging.getLogger(__name__)


def process_medication_reminders_job():
    """
    Process medication reminders that are due now.
    Creates adherence records with NOT_SET status.

    Runs every minute via APScheduler.
    """
    print("🔄 [MedicationReminder] Processing due reminders...")

    db = SessionLocal()
    try:
        created_count = 0
        utc_now = datetime.now(timezone.utc)
        today = date.today()

        # Get all active medication reminders with user timezone
        reminders_with_tz = (
            db.query(UserReminder, UserSettings.timezone)
            .join(UserSettings, UserReminder.user_id == UserSettings.user_id)
            .filter(
                UserReminder.reminder_type == "medication_reminder",
                UserReminder.is_active == True,
                UserReminder.medication_id.isnot(None),
                UserSettings.timezone.isnot(None),
            )
            .all()
        )

        adherence_repo = MedicationAdherenceRepository(db)

        for reminder, user_timezone in reminders_with_tz:
            try:
                # Convert current UTC to user's local time
                user_tz = ZoneInfo(user_timezone)
                local_now = utc_now.astimezone(user_tz)
                local_time = local_now.time()

                # Check if reminder time matches current local time (to minute precision)
                if (reminder.time.hour == local_time.hour and
                    reminder.time.minute == local_time.minute):

                    # Check if adherence record already exists for today
                    existing = adherence_repo.get_by_user_medication_date(
                        user_id=reminder.user_id,
                        medication_id=reminder.medication_id,
                        target_date=today,
                    )

                    if not existing:
                        # Create adherence record with NOT_SET status
                        adherence_repo.create(
                            user_id=reminder.user_id,
                            medication_id=reminder.medication_id,
                            target_date=today,
                            status=AdherenceStatus.NOT_SET,
                        )
                        created_count += 1
                        logger.info(
                            f"Created adherence record: user={reminder.user_id}, "
                            f"medication={reminder.medication_id}"
                        )

                        # TODO: Send push notification here

            except Exception as e:
                logger.warning(
                    f"Error processing reminder {reminder.id}: {e}"
                )
                continue

        db.commit()

        if created_count > 0:
            print(f"✅ [MedicationReminder] Created {created_count} adherence records")
            logger.info(f"Created {created_count} medication adherence records")

    except Exception as e:
        print(f"❌ [MedicationReminder] Job failed: {e}")
        logger.error(f"Medication reminder job failed: {e}")
    finally:
        db.close()


def register_medication_reminder_job():
    """Register the medication reminder job with the scheduler"""
    scheduler.add_job(
        process_medication_reminders_job,
        'cron',
        minute='*',  # Run every minute
        id='medication_reminder_processor',
        name='Process medication reminders and create adherence records',
        replace_existing=True,
    )
    print("📅 [MedicationReminder] Registered job to run every minute")
    logger.info("Registered medication reminder job to run every minute")
```

### Register in App Startup

**File:** `app/main.py` (add to startup)

```python
from app.features.medication.scheduler.medication_reminder_scheduler import (
    register_medication_reminder_job
)

@app.on_event("startup")
async def startup_event():
    # ... existing startup code ...
    register_medication_reminder_job()
```

### Tracking Processed Reminders

To prevent re-processing reminders that have already been triggered today, add `last_triggered_at` column to `user_reminders`.

**Schema Change:**

```sql
ALTER TABLE user_reminders ADD COLUMN last_triggered_at TIMESTAMP WITH TIME ZONE;
```

**Migration File:** `alembic/versions/YYYY_MM_DD_HHMM-add_last_triggered_at_to_reminders.py`

```python
"""Add last_triggered_at to user_reminders

Revision ID: xxxx
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column(
        'user_reminders',
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True)
    )

def downgrade():
    op.drop_column('user_reminders', 'last_triggered_at')
```

**Entity Update:** `app/features/auth/domain/entities/user_reminder.py`

```python
class UserReminder(Base):
    # ... existing fields ...
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
```

**Scheduler Logic Update:**

```python
for reminder, user_timezone in reminders_with_tz:
    try:
        user_tz = ZoneInfo(user_timezone)
        local_now = utc_now.astimezone(user_tz)
        local_time = local_now.time()

        # Check if reminder time matches current local time
        if (reminder.time.hour == local_time.hour and
            reminder.time.minute == local_time.minute):

            # Check if already triggered today (in user's local timezone)
            if reminder.last_triggered_at:
                last_triggered_local = reminder.last_triggered_at.astimezone(user_tz)
                if last_triggered_local.date() == local_now.date():
                    continue  # Already triggered today, skip

            # Process reminder (create adherence, send notification, etc.)
            # ...

            # Update last_triggered_at
            reminder.last_triggered_at = utc_now
```

### Edge Cases Handled

| Case | Handling |
|------|----------|
| User has no timezone set | Skipped (filtered in query) |
| Invalid timezone string | Caught in try/except, skipped |
| Adherence already exists | Checked before creating |
| Medication reminder inactive | Filtered in query |
| Multiple reminders same time | Each creates separate check |
| Reminder already triggered today | Skipped via `last_triggered_at` check |

### Testing Checklist

- [ ] Reminder at 08:00 in user's timezone triggers at correct UTC time
- [ ] Adherence record created with `NOT_SET` status
- [ ] No duplicate records created if job runs multiple times
- [ ] Users without timezone are skipped gracefully
- [ ] Invalid timezone strings don't crash the job
- [ ] Job logs creation count
- [ ] `last_triggered_at` updated after processing
- [ ] Reminder not re-triggered if `last_triggered_at` is today
