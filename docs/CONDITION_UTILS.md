# Condition Utilities

This document describes utility functions for handling patient conditions, including the priority ordering system for determining the "leading" condition.

---

## Condition Codes

```python
CONDITION_CODES = {
    "DEPRESSION": "35489007",
    "ASTHMA": "195967001",
    "BIPOLAR": "13746004",
    "CHRONIC_PAIN": "82423001",
    "MIGRAINE": "37796009",
    "HEADACHE": "230461009",
    "HYPERTENSION": "38341003",
    "COPD": "13645005",
    "ANXIETY": "197480006",
    "DIABETES": "73211009",
    "DRY_EYE": "162290004",
    "COMORBIDITY_ASTHMA_DEPRESSION": "195967001+35489007",
    "NOVEN_ADHD": "406506008",
}
```

---

## order_leading_conditions()

This function sorts a patient's conditions by clinical priority to determine which condition should be considered the "leading" or primary condition. This is used to decide which daily questionnaire to show first, which insights to prioritize, etc.

### Function Signature

```python
def order_leading_conditions(conditions: list[str]) -> list[str]:
    """
    Sort conditions by clinical priority/impact.

    Args:
        conditions: List of condition codes (SNOMED CT codes as strings)

    Returns:
        List of condition codes sorted by priority (highest priority first)
    """
```

### Default Priority Order

When a patient has multiple conditions, they are sorted by this default priority (lower number = higher priority):

| Priority | Condition | Code |
|----------|-----------|------|
| 0 | ADHD (NOVEN) | 406506008 |
| 1 | Chronic Pain | 82423001 |
| 2 | Bipolar Disorder | 13746004 |
| 3 | COPD | 13645005 |
| 4 | Migraine | 37796009 |
| 5 | Headache | 230461009 |
| 6 | Depression | 35489007 |
| 7 | Asthma | 195967001 |
| 8 | Hypertension | 38341003 |
| 9 | Comorbidity (Asthma+Depression) | 195967001+35489007 |
| 10 | Anxiety | 197480006 |
| 11 | Diabetes | 73211009 |
| 12 | Dry Eye | 162290004 |

### Special Case: Anxiety Present

When a patient has **Anxiety** as one of their conditions, the priority order changes to give Anxiety higher priority:

| Priority | Condition | Code |
|----------|-----------|------|
| 0 | ADHD (NOVEN) | 406506008 |
| 1 | Chronic Pain | 82423001 |
| 2 | Bipolar Disorder | 13746004 |
| 3 | COPD | 13645005 |
| 4 | Asthma | 195967001 |
| 5 | **Anxiety** | 197480006 |
| 6 | Migraine | 37796009 |
| 7 | Headache | 230461009 |
| 8 | Depression | 35489007 |
| 9 | Hypertension | 38341003 |
| 10 | Comorbidity (Asthma+Depression) | 195967001+35489007 |
| 11 | Diabetes | 73211009 |
| 12 | Dry Eye | 162290004 |

### Implementation

```python
DEPRESSION_CODE = "35489007"
ASTHMA_CODE = "195967001"
BIPOLAR_CODE = "13746004"
CHRONIC_PAIN_CODE = "82423001"
MIGRAINE_CODE = "37796009"
HEADACHE_CODE = "230461009"
HYPERTENSION_CODE = "38341003"
COPD_CODE = "13645005"
ANXIETY_CODE = "197480006"
DIABETES_CODE = "73211009"
DRY_EYE_CODE = "162290004"
COMORBIDITY_ASTHMA_DEPRESSION_CODE = "195967001+35489007"
NOVEN_ADHD_CODE = "406506008"


def order_leading_conditions(conditions: list[str]) -> list[str]:
    """
    Sort conditions by clinical priority/impact.

    The leading condition determines:
    - Which daily questionnaire is shown first
    - Which condition's insights are prioritized
    - The primary focus of the user's health journey

    Args:
        conditions: List of condition codes (SNOMED CT codes as strings)

    Returns:
        List of condition codes sorted by priority (highest priority first)
        Only includes conditions that are in the input list.
    """

    # Default priority order (lower number = higher priority)
    condition_priority = {
        NOVEN_ADHD_CODE: 0,           # Always highest priority if present
        CHRONIC_PAIN_CODE: 1,
        BIPOLAR_CODE: 2,
        COPD_CODE: 3,
        MIGRAINE_CODE: 4,
        HEADACHE_CODE: 5,
        DEPRESSION_CODE: 6,
        ASTHMA_CODE: 7,
        HYPERTENSION_CODE: 8,
        COMORBIDITY_ASTHMA_DEPRESSION_CODE: 9,
        ANXIETY_CODE: 10,
        DIABETES_CODE: 11,
        DRY_EYE_CODE: 12,
    }

    # Special case: If patient has Anxiety, adjust priorities
    # This gives Anxiety higher priority and shifts other conditions down
    if ANXIETY_CODE in conditions:
        condition_priority[ASTHMA_CODE] = 4
        condition_priority[ANXIETY_CODE] = 5
        condition_priority[MIGRAINE_CODE] = 6
        condition_priority[HEADACHE_CODE] = 7
        condition_priority[DEPRESSION_CODE] = 8
        condition_priority[HYPERTENSION_CODE] = 9
        condition_priority[COMORBIDITY_ASTHMA_DEPRESSION_CODE] = 10
        condition_priority[DIABETES_CODE] = 11
        condition_priority[DRY_EYE_CODE] = 12

    # Filter to only conditions the patient has, then sort by priority
    patient_conditions = [c for c in condition_priority if c in set(conditions)]

    return sorted(patient_conditions, key=lambda x: condition_priority[x])
```

### Usage Examples

```python
# Example 1: Single condition
conditions = ["73211009"]  # Diabetes
result = order_leading_conditions(conditions)
# Result: ["73211009"]

# Example 2: Multiple conditions (no anxiety)
conditions = ["73211009", "38341003", "37796009"]  # Diabetes, Hypertension, Migraine
result = order_leading_conditions(conditions)
# Result: ["37796009", "38341003", "73211009"]  # Migraine first (priority 4)

# Example 3: Multiple conditions with Anxiety
conditions = ["197480006", "195967001", "35489007"]  # Anxiety, Asthma, Depression
result = order_leading_conditions(conditions)
# Result: ["195967001", "197480006", "35489007"]  # Asthma (4), Anxiety (5), Depression (8)

# Example 4: NOVEN ADHD always first
conditions = ["406506008", "82423001", "197480006"]  # ADHD, Chronic Pain, Anxiety
result = order_leading_conditions(conditions)
# Result: ["406506008", "82423001", "197480006"]  # ADHD always priority 0
```

### Use Cases

1. **Determining Primary Questionnaire**: The first condition in the sorted list determines which daily questionnaire the user sees first.

2. **Insights Prioritization**: Health insights and recommendations are ordered based on the leading condition.

3. **Dashboard Display**: The leading condition may be highlighted on the user's dashboard.

4. **Comorbidity Handling**: When a user has multiple conditions, this ensures the most clinically significant one takes precedence.

---

## Helper Functions

### condition_code()

Extract the condition code from a condition object.

```python
def condition_code(condition) -> str:
    """
    Extract the SNOMED CT code from a condition object.

    Args:
        condition: Condition object with code.coding[0].code

    Returns:
        The condition code as a string
    """
    return condition.code.coding[0].code
```

### condition_display()

Extract the display name from a condition object.

```python
def condition_display(condition) -> str:
    """
    Extract the display name from a condition object.

    Args:
        condition: Condition object with code.coding[0].display

    Returns:
        The human-readable condition name
    """
    return condition.code.coding[0].display
```

### is_comorbidity()

Check if user has multiple conditions.

```python
def is_comorbidity(conditions: list) -> bool:
    """
    Check if patient has multiple conditions (comorbidity).

    Args:
        conditions: List of condition objects or codes

    Returns:
        True if more than one condition, False otherwise
    """
    return len(conditions) > 1
```

### is_diagnosed()

Check if condition was diagnosed by a physician.

```python
def is_diagnosed(condition: dict) -> bool:
    """
    Check if a condition was diagnosed by a physician.

    Args:
        condition: Condition dict with optional diagnosedByPhysician field

    Returns:
        True if diagnosedByPhysician.code == "yes", False otherwise
    """
    return condition.get("diagnosedByPhysician", {}).get("code") == "yes"
```

---

## Database Schema Suggestion

If implementing in a new codebase, you might store conditions like:

```python
# Patient Condition model
class PatientCondition:
    id: str                    # UUID
    patient_id: str            # Foreign key to Patient
    code: str                  # SNOMED CT code (e.g., "197480006")
    display: str               # Human-readable name (e.g., "Anxiety")
    diagnosed_by_physician: bool
    created_at: datetime
    updated_at: datetime
```

Query to get a patient's conditions and determine leading condition:

```python
async def get_leading_condition(patient_id: str) -> str | None:
    """Get the patient's leading (primary) condition code."""
    conditions = await db.query(
        "SELECT code FROM patient_conditions WHERE patient_id = ?",
        patient_id
    )
    condition_codes = [c.code for c in conditions]

    if not condition_codes:
        return None

    ordered = order_leading_conditions(condition_codes)
    return ordered[0] if ordered else None
```
