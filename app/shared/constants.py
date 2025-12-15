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
    "37796009": {
        "label": "Migraine",
        "system": "snomed",
        "description": "Migraine"
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

# Tracking topics with metadata
TRACKING_TOPICS: Dict[str, Dict[str, Any]] = {
    "coffee-consumption": {
        "label": "Coffee Consumption",
        "question": "How many cups of coffee did you drink yesterday?",
        "data_type": "number",
        "unit": "cups-of-coffee",
        "emoji": "☕",
        "min": 0,
        "max": 10,
    },
    "smoking": {
        "label": "Smoking",
        "question": "How many cigarettes did you smoke yesterday?",
        "data_type": "number",
        "unit": "number-of-cigarettes",
        "emoji": "🚬",
        "min": 0,
        "max": 20,
    },
    "alcohol-consumption": {
        "label": "Alcohol Consumption",
        "question": "How many glasses of alcohol did you drink yesterday?",
        "data_type": "number",
        "unit": "glasses-of-alcohol",
        "emoji": "🍷",
        "min": 0,
        "max": 5,
    },
    "hours-spent-outside": {
        "label": "Hours Spent Outside",
        "question": "How many hours did you spend outside yesterday?",
        "data_type": "number",
        "unit": "hours-spent-outside",
        "emoji": "☀",
        "min": 0,
        "max": 5,
    },
}

# Backwards compatibility alias
TRACKING_TOPIC_LABELS = {code: info["label"] for code, info in TRACKING_TOPICS.items()}