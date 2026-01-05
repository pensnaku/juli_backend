"""Utility functions for handling patient conditions"""
from typing import List, Optional

# Condition code constants (for readability and consistency)
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


def order_leading_conditions(conditions: List[str]) -> List[str]:
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

    Example:
        >>> order_leading_conditions(["73211009", "37796009"])
        ["37796009", "73211009"]  # Migraine before Diabetes
    """
    # Default priority order (lower number = higher priority)
    condition_priority = {
        CHRONIC_PAIN_CODE: 0,
        BIPOLAR_CODE: 1,
        COPD_CODE: 2,
        MIGRAINE_CODE: 3,
        HEADACHE_CODE: 4,
        DEPRESSION_CODE: 5,
        ASTHMA_CODE: 6,
        HYPERTENSION_CODE: 7,
        COMORBIDITY_ASTHMA_DEPRESSION_CODE: 8,
        ANXIETY_CODE: 9,
        DIABETES_CODE: 10,
        DRY_EYE_CODE: 11,
    }

    # Special case: If patient has Anxiety, adjust priorities
    if ANXIETY_CODE in conditions:
        condition_priority[ASTHMA_CODE] = 3
        condition_priority[ANXIETY_CODE] = 4
        condition_priority[MIGRAINE_CODE] = 5
        condition_priority[HEADACHE_CODE] = 6
        condition_priority[DEPRESSION_CODE] = 7
        condition_priority[HYPERTENSION_CODE] = 8
        condition_priority[COMORBIDITY_ASTHMA_DEPRESSION_CODE] = 9
        condition_priority[DIABETES_CODE] = 10
        condition_priority[DRY_EYE_CODE] = 11

    # Filter to only conditions the patient has, then sort by priority
    patient_conditions = [c for c in condition_priority if c in set(conditions)]

    return sorted(patient_conditions, key=lambda x: condition_priority[x])


def is_comorbidity(conditions: List[str]) -> bool:
    """
    Check if patient has multiple conditions (comorbidity).

    Args:
        conditions: List of condition codes

    Returns:
        True if more than one condition, False otherwise
    """
    return len(conditions) > 1


def get_leading_condition(conditions: List[str]) -> Optional[str]:
    """
    Get the patient's leading (primary) condition code.

    Args:
        conditions: List of condition codes

    Returns:
        The highest priority condition code, or None if no conditions
    """
    ordered = order_leading_conditions(conditions)
    return ordered[0] if ordered else None
