# Daily Dares Feature - Implementation Plan

## Overview
Daily Dares is a gamification feature that provides **exactly 4 daily challenges** to users - **one from each category** (Activity, Nutrition, Sleep, Wellness). Users fetch dares via API and can complete dares from previous days.

---

## Key Requirements
- **4 dares per day** - exactly one from each category
- **Condition filtering** - dares with conditions (asthma, depress, bipolar) are only shown to users WITH those conditions
- **On-demand delivery** - users fetch dares when they request via API (no push notifications)
- **Retroactive completion** - users can complete dares from previous days
- **Timezone aware** - use user's timezone to determine "today"
- **No repetition** - avoid assigning same dares within recent days

---

## Database Schema

### 1. `dares` table (Master list of all dares)

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | Primary key |
| text | TEXT NOT NULL | The dare text |
| category | VARCHAR(50) NOT NULL | Activity, Nutrition, Sleep, Wellness |
| subcategory | VARCHAR(50) NULL | Meal, Hydration, Alcohol, Vegetables, Fruit |
| points | INT NOT NULL | 1-5 points |
| condition | VARCHAR(50) NULL | Only show to users WITH this condition |
| is_active | BOOLEAN DEFAULT TRUE | Soft delete flag |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

**Index**: `category` (for filtering by category)

### 2. `daily_dare_assignments` table (User's assigned dares)

| Column | Type | Description |
|--------|------|-------------|
| id | INT PK | Primary key |
| user_id | INT FK | Foreign key to users |
| dare_id | INT FK | Foreign key to dares |
| assigned_date | DATE NOT NULL | User's local date (YYYY-MM-DD) |
| is_completed | BOOLEAN DEFAULT FALSE | Completion status |
| completed_at | TIMESTAMP NULL | When completed |
| points_earned | INT DEFAULT 0 | Points awarded on completion |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

**Constraints**:
- UNIQUE(user_id, dare_id, assigned_date) - prevent duplicate assignments
- INDEX(user_id, assigned_date) - fast lookup for user's daily dares

---

## Feature Structure

```
app/features/dares/
├── __init__.py
├── api/
│   ├── __init__.py
│   └── router.py
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── dare.py
│   │   └── daily_dare_assignment.py
│   └── schemas/
│       ├── __init__.py
│       ├── dare.py
│       └── daily_dare_assignment.py
├── repository/
│   ├── __init__.py
│   ├── dare_repository.py
│   └── daily_dare_assignment_repository.py
└── service/
    ├── __init__.py
    └── dare_service.py
```

---

## API Endpoints

### 1. GET `/api/v1/dares/daily`
Get today's 4 dares for the authenticated user.

**Logic:**
1. Get user's timezone from user_settings
2. Calculate user's local date
3. Check if 4 dares exist for that date
4. If not, generate them (one per category)
5. Return dares with completion status

**Response:**
```json
{
  "date": "2025-11-27",
  "dares": [
    {
      "assignment_id": 123,
      "dare_id": 45,
      "text": "Walk at least 1 mile (1.6 km).",
      "category": "Activity",
      "subcategory": null,
      "points": 3,
      "is_completed": false,
      "completed_at": null
    },
    {
      "assignment_id": 124,
      "dare_id": 89,
      "text": "Drink 64 ounces (2L) of water.",
      "category": "Nutrition",
      "subcategory": "Hydration",
      "points": 3,
      "is_completed": false,
      "completed_at": null
    },
    {
      "assignment_id": 125,
      "dare_id": 102,
      "text": "Be in bed by 10 PM",
      "category": "Sleep",
      "subcategory": null,
      "points": 2,
      "is_completed": true,
      "completed_at": "2025-11-27T22:05:00Z"
    },
    {
      "assignment_id": 126,
      "dare_id": 150,
      "text": "Give a compliment to someone.",
      "category": "Wellness",
      "subcategory": null,
      "points": 2,
      "is_completed": false,
      "completed_at": null
    }
  ],
  "summary": {
    "total_points_possible": 10,
    "points_earned": 2,
    "completed_count": 1
  }
}
```

### 2. GET `/api/v1/dares/daily/{date}`
Get dares for a specific date (for viewing/completing past dares).

**Path Parameter:** `date` - ISO format date (YYYY-MM-DD)

**Response:** Same as above

### 3. POST `/api/v1/dares/{assignment_id}/complete`
Mark a dare as completed.

**Validation:**
- Assignment must belong to authenticated user
- Assignment must not already be completed

**Response:**
```json
{
  "success": true,
  "assignment_id": 123,
  "points_earned": 3,
  "completed_at": "2025-11-27T14:30:00Z"
}
```

### 4. GET `/api/v1/dares/history?days=7`
Get dare history for past N days.

**Query Parameter:** `days` - number of days (default: 7, max: 30)

**Response:**
```json
{
  "history": [
    {
      "date": "2025-11-27",
      "dares": [...],
      "completed_count": 3,
      "points_earned": 8
    },
    {
      "date": "2025-11-26",
      "dares": [...],
      "completed_count": 4,
      "points_earned": 12
    }
  ],
  "total_points": 20,
  "total_completed": 7
}
```

---

## Dare Selection Algorithm

```python
def generate_daily_dares(user_id: int, user_date: date) -> List[DailyDareAssignment]:
    """Generate exactly 4 dares (one per category) for a user's date."""

    # 1. Check if already generated for this date
    existing = get_assignments_for_date(user_id, user_date)
    if len(existing) == 4:
        return existing

    # 2. Get user's condition codes (from user_conditions table)
    user_condition_codes = get_user_condition_codes(user_id)

    # 3. Get recently assigned dare IDs to avoid repetition
    recent_dare_ids = get_recent_dare_ids(user_id, days=7)

    # 4. Select one dare per category
    categories = ["Activity", "Nutrition", "Sleep", "Wellness"]
    assignments = []

    for category in categories:
        dare = select_random_dare(
            category=category,
            exclude_ids=recent_dare_ids,
            user_conditions=user_condition_codes
        )
        if dare:
            assignment = create_assignment(user_id, dare.id, user_date)
            assignments.append(assignment)
            recent_dare_ids.add(dare.id)

    return assignments


def select_random_dare(category: str, exclude_ids: Set[int], user_conditions: List[str]) -> Dare:
    """
    Select a random dare from category.

    Rules:
    - Must match category
    - Must not be in exclude_ids (recently assigned)
    - If dare has a condition, user must have that condition
    - If dare has no condition, any user can get it
    """
    query = (
        db.query(Dare)
        .filter(Dare.category == category)
        .filter(Dare.is_active == True)
        .filter(~Dare.id.in_(exclude_ids))
        .filter(
            or_(
                Dare.condition.is_(None),  # No condition required
                Dare.condition.in_(user_conditions)  # User has the condition
            )
        )
    )

    # Get all matching dares and pick one randomly
    dares = query.all()
    if dares:
        return random.choice(dares)

    # Fallback: if no dares available (all recently used), allow repetition
    return db.query(Dare).filter(
        Dare.category == category,
        Dare.is_active == True
    ).order_by(func.random()).first()
```

---

## Timezone Handling

```python
from zoneinfo import ZoneInfo  # Python 3.9+ built-in
from datetime import datetime, date

def get_user_local_date(timezone_str: str) -> date:
    """Get the current date in user's timezone."""
    if not timezone_str:
        timezone_str = "UTC"

    try:
        tz = ZoneInfo(timezone_str)
        return datetime.now(tz).date()
    except Exception:
        return datetime.now(ZoneInfo("UTC")).date()
```

---

## Implementation Steps

### Phase 1: Database & Entities
1. Create `Dare` entity
2. Create `DailyDareAssignment` entity
3. Generate and run Alembic migration
4. Create Pydantic schemas for both entities

### Phase 2: Repositories
1. Create `DareRepository`:
   - `get_all()` - list all dares
   - `get_by_category(category)` - filter by category
   - `get_random_for_user(category, exclude_ids, user_conditions)` - selection logic
2. Create `DailyDareAssignmentRepository`:
   - `get_by_user_and_date(user_id, date)` - get user's dares for a date
   - `get_recent_dare_ids(user_id, days)` - for avoiding repetition
   - `create(user_id, dare_id, date)` - create assignment
   - `mark_completed(assignment_id)` - complete a dare

### Phase 3: Service Layer
1. Create `DareService`:
   - `get_daily_dares(user_id)` - main method to get/generate daily dares
   - `get_dares_for_date(user_id, date)` - get dares for specific date
   - `complete_dare(user_id, assignment_id)` - mark dare complete
   - `get_history(user_id, days)` - get past dares

### Phase 4: API Router
1. Create router with all endpoints
2. Register router in main app

### Phase 5: Data Import
1. Create script to import dares from CSV
2. Run import to populate `dares` table

---

## CSV Data Notes

From the provided CSV:
- **~180 total dares**
- **Activity**: ~40 dares
- **Nutrition**: ~45 dares (subcategories: Meal, Hydration, Alcohol, Vegetables, Fruit)
- **Sleep**: ~20 dares
- **Wellness**: ~75 dares
- **Conditions used**: asthma, depress, bipolar (only on a few dares)

The condition values in CSV need to be mapped to SNOMED codes used in `user_conditions` table, or we use simple string matching.

---

## Ready to Implement?

This plan covers:
- ✅ Database schema for dares and assignments
- ✅ Feature structure following existing patterns
- ✅ API endpoints for fetching and completing dares
- ✅ Dare selection algorithm with condition filtering
- ✅ Timezone handling
- ✅ Retroactive completion support
- ✅ Implementation phases

Let me know if you want to proceed with implementation!