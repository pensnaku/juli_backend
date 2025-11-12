"""Shared constants for the application"""
from typing import Dict, Any

# Medical condition codes (SNOMED CT)
CONDITION_CODES: Dict[str, Dict[str, Any]] = {
    "73211009": {
        "label": "Diabetes",
        "system": "snomed",
        "description": "Diabetes mellitus"
    },
    "82423001": {
        "label": "Chronic pain",
        "system": "snomed",
        "description": "Chronic pain disorder"
    },
    "49601007": {
        "label": "Cardiovascular disease",
        "system": "snomed",
        "description": "Disorder of cardiovascular system"
    },
    "13645005": {
        "label": "Chronic obstructive pulmonary disease",
        "system": "snomed",
        "description": "Chronic obstructive lung disease"
    },
}

# Reminder types
REMINDER_TYPES = {
    "daily_check_in": "Daily check-in reminder",
    "glucose_check": "Blood glucose check reminder",
    "medication": "Medication reminder",
    "appointment": "Medical appointment reminder",
}

# Questionnaire IDs
QUESTIONNAIRE_IDS = {
    "ONBOARDING": "onboarding",
    "DAILY": "daily",
    "BIWEEKLY": "biweekly",
}