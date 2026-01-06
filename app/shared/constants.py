"""Shared constants for the application"""

from typing import Dict, Any

# Medical condition codes (SNOMED CT)
CONDITION_CODES: Dict[str, Dict[str, Any]] = {
    "73211009": {
        "label": "Diabetes",
        "system": "snomed",
        "description": "Diabetes mellitus",
    },
    "82423001": {
        "label": "Chronic pain",
        "system": "snomed",
        "description": "Chronic pain disorder",
    },
    "49601007": {
        "label": "Cardiovascular disease",
        "system": "snomed",
        "description": "Disorder of cardiovascular system",
    },
    "13645005": {
        "label": "Chronic obstructive pulmonary disease",
        "system": "snomed",
        "description": "Chronic obstructive lung disease",
    },
    "195967001": {"label": "Asthma", "system": "snomed", "description": "Asthma"},
    "35489007": {
        "label": "Depression",
        "system": "snomed",
        "description": "Depressive disorder",
    },
    "13746004": {
        "label": "Bipolar disorder",
        "system": "snomed",
        "description": "Bipolar disorder",
    },
    "37796009": {"label": "Migraine", "system": "snomed", "description": "Migraine"},
    "197480006": {
        "label": "Anxiety",
        "system": "snomed",
        "description": "Anxiety disorder",
    },
    "162290004": {
        "label": "Dry Eye",
        "system": "snomed",
        "description": "Dry eye syndrome",
    },
    "230461009": {"label": "Headache", "system": "snomed", "description": "Headache"},
    "38341003": {
        "label": "Hypertension",
        "system": "snomed",
        "description": "Essential hypertension",
    },
    "195967001+35489007": {
        "label": "Asthma + Depression Comorbidity",
        "system": "snomed",
        "description": "Comorbidity: Asthma and Depressive disorder",
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

# Daily questionnaire filename mapping (condition_code -> filename)
# Maps SNOMED condition codes to daily questionnaire YAML filenames
DAILY_QUESTIONNAIRE_MAP: Dict[str, str] = {
    "197480006": "anxiety",
    "195967001": "asthma",
    "13746004": "bipolar",
    "82423001": "chronic_pain",
    "13645005": "copd",
    "35489007": "depression",
    "73211009": "diabetes",
    "162290004": "dry_eye",
    "230461009": "headache",
    "38341003": "hypertension",
    "37796009": "migraine",
    "365275006": "wellbeing",
}

# Reverse mapping for lookup (filename -> condition_code)
DAILY_QUESTIONNAIRE_CONDITION_MAP: Dict[str, str] = {
    v: k for k, v in DAILY_QUESTIONNAIRE_MAP.items()
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
