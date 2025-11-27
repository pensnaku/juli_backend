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
    "195967001": {
        "label": "Asthma",
        "system": "snomed",
        "description": "Asthma"
    },
    "35489007": {
        "label": "Depression",
        "system": "snomed",
        "description": "Depressive disorder"
    },
    "13746004": {
        "label": "Bipolar disorder",
        "system": "snomed",
        "description": "Bipolar disorder"
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

# Tracking topic labels
TRACKING_TOPIC_LABELS = {
    "coffee-consumption": "Coffee consumption",
    "alcohol-consumption": "Alcohol consumption",
    "smoking": "Smoking",
    "hours-spent-outside": "Hours spent outside",
}