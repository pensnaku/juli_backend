# Questionnaire Question to Database Mapping

Maps each onboarding question to proper database tables (normalized, no JSON storage).

## User Profile → `users` table

| Question ID | Field | Type |
|-------------|-------|------|
| `name` | `full_name` | string |
| `age` | `age` | integer |
| `gender` | `gender` | string |

## User Settings → `user_settings` table

| Question ID | Field | Type |
|-------------|-------|------|
| `daily-routine-or-main-activity` | `daily_routine` | string |
| `ethnicity` | `ethnicity` | string (nullable) |
| `ethnicity-hispanic-latino` | `hispanic_latino` | string (nullable) |
| `allow-support-for-other-condition` | `allow_medical_support` | boolean |

## User Reminders → `user_reminders` table (NEW)

| Question ID | Mapping |
|-------------|---------|
| `notification-time` | Creates reminder with type="daily_check_in" |
| `glucose-check-reminders` | Creates multiple reminders with type="glucose_check" |

### `user_reminders` Table:
```python
class UserReminder(Base):
    id: int
    user_id: int (FK)
    reminder_type: str  # "daily_check_in", "glucose_check", etc.
    time: time  # "08:00:00"
    is_active: bool
    created_at: datetime
```

## Medical Conditions → `user_conditions` table (NEW)

| Question ID | Field |
|-------------|-------|
| `conditions` | Creates rows (one per condition) |
| `comorbidity-condition-diagnosed-by-physician` | `diagnosed_by_physician` |
| `comorbidity-condition-experienced-for` | `duration` |
| `comorbidity-do-you-see-physician` | `physician_frequency` |
| **Diabetes-specific:** |
| `which-type-of-diabetes` | `diabetes_type` (nullable) |
| `reminder-to-check-blood-glucose` | `wants_glucose_reminders` (nullable) |
| **Pain-specific:** |
| `how-would-you-describe-your-pain` | `pain_type` (nullable) |

### `user_conditions` Table:
```python
class UserCondition(Base):
    id: int
    user_id: int (FK)

    # Core fields
    condition_code: str  # "73211009"
    condition_label: str  # "Diabetes"

    # Common fields (for all conditions)
    diagnosed_by_physician: bool (nullable)
    duration: str (nullable)
    physician_frequency: str (nullable)

    # Diabetes-specific (nullable, only populated for diabetes)
    diabetes_type: str (nullable)  # "type-2-diabetes"
    therapy_type: str (nullable)  # "pills" or store first therapy
    wants_glucose_reminders: bool (nullable)

    # Pain-specific (nullable, only populated for chronic pain)
    pain_type: str (nullable)  # "musculoskeletal-pain"

    # Future condition-specific fields can be added as needed
```

## Diabetes Therapy → `user_conditions` table

| Question ID | Field |
|-------------|-------|
| `what-is-your-diabetes-therapy` | `therapy_type` (nullable, comma-separated or single value) |

Since users can select multiple therapies, we'll store the primary one in `therapy_type` field. If you need to track multiple therapies separately, we can create a junction table later.

---

## Database Schema Summary

### New Tables:

1. **`user_conditions`** - One row per condition per user (includes therapy)
2. **`user_reminders`** - All types of reminders (normalized)

### Updates to Existing Tables:

**`users`:**
- `age: integer`
- `gender: string`

**`user_settings`:**
- `daily_routine: string`
- `ethnicity: string (nullable)`
- `hispanic_latino: string (nullable)`
- `allow_medical_support: boolean`

---

## Example Data Flow

When user submits:
```json
{
  "name": "John",
  "age": 30,
  "conditions": ["73211009"],
  "which-type-of-diabetes": "type-2-diabetes",
  "what-is-your-diabetes-therapy": ["pills", "pen-syringe"],
  "reminder-to-check-blood-glucose": "yes-remind-me",
  "glucose-check-reminders": ["08:00", "12:00", "20:00"],
  "notification-time": "19:00"
}
```

### Results in:

**`users` table:**
```
full_name: "John"
age: 30
```

**`user_conditions` table:**
```
condition_code: "73211009"
condition_label: "Diabetes"
diabetes_type: "type-2-diabetes"
therapy_type: "pills"  # Store primary/first therapy
wants_glucose_reminders: true
```

**`user_reminders` table:**
```
Row 1: type="daily_check_in", time="19:00"
Row 2: type="glucose_check", time="08:00"
Row 3: type="glucose_check", time="12:00"
Row 4: type="glucose_check", time="20:00"
```

---

## Benefits:

✅ **Fully normalized** - No JSON storage
✅ **Queryable** - Easy to filter/search therapies and reminders
✅ **Flexible** - Can add reminder types without schema changes
✅ **Proper relationships** - Foreign keys maintain integrity
✅ **Scalable** - Can handle unlimited therapies/reminders per user

Should I proceed with creating these database models?
