"""Observation code constants for health data tracking"""


class ObservationCodes:
    """All supported observation codes organized by category"""

    # Sleep & Rest
    TIME_ASLEEP = "time-asleep"
    TIME_IN_BED = "time-in-bed"
    TIME_LIGHT_SLEEP = "time-light-sleep"
    TIME_REM_SLEEP = "time-rem-sleep"
    TIME_DEEP_SLEEP = "time-deep-sleep"

    # Activity & Exercise
    STEPS_COUNT = "steps-count"
    WORKOUT = "workout"
    BASAL_ENERGY_BURNED = "basal-energy-burned"
    ACTIVE_ENERGY_BURNED = "active-energy-burned"
    FLIGHTS_CLIMBED = "flights-climbed"

    # Environment (unified code with variants)
    ENVIRONMENT = "environment"

    # Body Measurements
    WEIGHT = "weight"
    HEIGHT = "height"
    BMI = "bmi"
    BODY_FAT_PERCENTAGE = "body-fat-percentage"
    BODY_TEMPERATURE = "body-temperature"

    # Vital Signs
    RESTING_HEART_RATE = "resting-heart-rate"
    HEART_RATE = "heart-rate"
    HEART_RATE_VARIABILITY = "heart-rate-variability"
    OXYGEN_SATURATION = "oxygen-saturation"
    BLOOD_PRESSURE = "blood-pressure"

    # Respiratory
    PEAK_EXPIRATORY_FLOW = "peak-expiratory-flow"
    INHALER_USAGE_COUNT = "inhaler-usage-count"

    # Demographics & Personal Info
    BIOLOGICAL_SEX = "biological-sex"
    BIRTHDATE = "birthdate"

    # Menstrual Health
    LAST_MENSTRUATION_DATE = "last-menstruation-date"
    MENSTRUAL_FLOW = "menstrual-flow"

    # Bi-Weekly Questionnaire Scores
    BIWEEKLY_ANXIETY_SCORE = "bi-weekly-anxiety-questionnaire-score"
    BIWEEKLY_ASTHMA_SCORE = "bi-weekly-asthma-questionnaire-score"
    BIWEEKLY_DEPRESSION_SCORE = "bi-weekly-depression-questionnaire-score"
    BIWEEKLY_BIPOLAR_SCORE = "bi-weekly-bipolar-questionnaire-score"
    BIWEEKLY_CHRONIC_PAIN_INTERFERENCE_SCORE = "bi-weekly-chronic-pain-interference-questionnaire-score"
    BIWEEKLY_CHRONIC_PAIN_SCORE = "bi-weekly-chronic-pain-questionnaire-score"
    BIWEEKLY_COPD_SCORE = "bi-weekly-copd-questionnaire-score"
    BIWEEKLY_HEADACHE_SCORE = "bi-weekly-headache-questionnaire-score"
    BIWEEKLY_HYPERTENSION_SCORE = "bi-weekly-hypertension-questionnaire-score"
    BIWEEKLY_MIGRAINE_SCORE = "bi-weekly-migraine-questionnaire-score"
    BIWEEKLY_COMORBIDITY_ASTHMA_DEPRESSION_ASTHMA_SCORE = "bi-weekly-comorbidity-asthma-depression-part-asthma-questionnaire-score"
    BIWEEKLY_COMORBIDITY_ASTHMA_DEPRESSION_DEPRESSION_SCORE = "bi-weekly-comorbidity-asthma-depression-part-depression-questionnaire-score"

    # Daily Questionnaire - Mood & Energy
    DAILY_MOOD = "daily-questionnaire-mood"
    DAILY_MOOD_ENERGY = "daily-questionnaire-mood-energy"
    DAILY_MOOD_ENERGY_MOOD = "daily-questionnaire-mood-energy-mood"

    # Daily Questionnaire - Respiratory
    DAILY_SHORTNESS_OF_BREATH = "daily-questionnaire-shortness-of-breath"
    DAILY_COUGH_UP_MUCUS = "daily-cough-up-mucus-observation-extract"
    DAILY_WAKE_UP_AT_NIGHT = "daily-questionnaire-wake-up-at-night"

    # Daily Questionnaire - Pain
    DAILY_ACTIVITY_PAIN_INTERFERENCE = "daily-questionnaire-activity-pain-interference"
    DAILY_RELIEF_FROM_PAIN_MEDICATION = "daily-questionnaire-relief-from-pain-medication"
    DAILY_ACTIVITY_PAIN = "daily-questionnaire-activity-pain"

    # Daily Questionnaire - Mental Health
    DAILY_ANXIETY_MANAGEMENT = "daily-anxiety-management"
    DAILY_ANXIETY_RATING = "daily-anxiety-rating"

    # Daily Questionnaire - Other
    DAILY_BLOOD_PRESSURE = "daily-questionnaire-blood-pressure"
    DAILY_HEADACHE_TODAY = "daily-questionnaire-headache-today"
    DAILY_MIGRAINE_TODAY = "daily-questionnaire-migraine-today"


class ObservationCategories:
    """Categories for grouping observations"""

    SLEEP = "sleep"
    ACTIVITY = "activity"
    ENVIRONMENT = "environment"
    BODY_MEASUREMENTS = "body-measurements"
    VITAL_SIGNS = "vital-signs"
    RESPIRATORY = "respiratory"
    DEMOGRAPHICS = "demographics"
    MENSTRUAL_HEALTH = "menstrual-health"
    QUESTIONNAIRE_BIWEEKLY = "questionnaire-biweekly"
    QUESTIONNAIRE_DAILY = "questionnaire-daily"


class ObservationDataSources:
    """Data sources for observations"""

    MANUAL = "manual"
    APPLE_HEALTH = "apple-health"
    GOOGLE_FIT = "google-fit"
    QUESTIONNAIRE = "questionnaire"
    DEVICE = "device"
    CALCULATED = "calculated"
    AMBEE = "ambee"
    OPENWEATHERMAP = "openweathermap"


class EnvironmentVariants:
    """Variants for environment observations"""

    # Air Quality
    AIR_QUALITY_INDEX = "air-quality-index"
    AIR_QUALITY_POLLUTANT = "air-quality-pollutant"

    # Pollen
    POLLEN_GRASS = "pollen-grass"
    POLLEN_TREE = "pollen-tree"
    POLLEN_WEED = "pollen-weed"
    POLLEN_TOTAL = "pollen-total"

    # Pollen Risk
    POLLEN_RISK_GRASS = "pollen-risk-grass"
    POLLEN_RISK_TREE = "pollen-risk-tree"
    POLLEN_RISK_WEED = "pollen-risk-weed"

    # Weather
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    AIR_PRESSURE = "air-pressure"
    WIND_SPEED = "wind-speed"
    WIND_DIRECTION = "wind-direction"
    SUNRISE = "sunrise"
    SUNSET = "sunset"


# Mapping of codes to their default categories
OBSERVATION_CODE_CATEGORIES = {
    # Sleep
    ObservationCodes.TIME_ASLEEP: ObservationCategories.SLEEP,
    ObservationCodes.TIME_IN_BED: ObservationCategories.SLEEP,
    ObservationCodes.TIME_LIGHT_SLEEP: ObservationCategories.SLEEP,
    ObservationCodes.TIME_REM_SLEEP: ObservationCategories.SLEEP,
    ObservationCodes.TIME_DEEP_SLEEP: ObservationCategories.SLEEP,

    # Activity
    ObservationCodes.STEPS_COUNT: ObservationCategories.ACTIVITY,
    ObservationCodes.WORKOUT: ObservationCategories.ACTIVITY,
    ObservationCodes.BASAL_ENERGY_BURNED: ObservationCategories.ACTIVITY,
    ObservationCodes.ACTIVE_ENERGY_BURNED: ObservationCategories.ACTIVITY,
    ObservationCodes.FLIGHTS_CLIMBED: ObservationCategories.ACTIVITY,

    # Environment
    ObservationCodes.ENVIRONMENT: ObservationCategories.ENVIRONMENT,

    # Body Measurements
    ObservationCodes.WEIGHT: ObservationCategories.BODY_MEASUREMENTS,
    ObservationCodes.HEIGHT: ObservationCategories.BODY_MEASUREMENTS,
    ObservationCodes.BMI: ObservationCategories.BODY_MEASUREMENTS,
    ObservationCodes.BODY_FAT_PERCENTAGE: ObservationCategories.BODY_MEASUREMENTS,
    ObservationCodes.BODY_TEMPERATURE: ObservationCategories.BODY_MEASUREMENTS,

    # Vital Signs
    ObservationCodes.RESTING_HEART_RATE: ObservationCategories.VITAL_SIGNS,
    ObservationCodes.HEART_RATE: ObservationCategories.VITAL_SIGNS,
    ObservationCodes.HEART_RATE_VARIABILITY: ObservationCategories.VITAL_SIGNS,
    ObservationCodes.OXYGEN_SATURATION: ObservationCategories.VITAL_SIGNS,
    ObservationCodes.BLOOD_PRESSURE: ObservationCategories.VITAL_SIGNS,

    # Respiratory
    ObservationCodes.PEAK_EXPIRATORY_FLOW: ObservationCategories.RESPIRATORY,
    ObservationCodes.INHALER_USAGE_COUNT: ObservationCategories.RESPIRATORY,

    # Demographics
    ObservationCodes.BIOLOGICAL_SEX: ObservationCategories.DEMOGRAPHICS,
    ObservationCodes.BIRTHDATE: ObservationCategories.DEMOGRAPHICS,

    # Menstrual Health
    ObservationCodes.LAST_MENSTRUATION_DATE: ObservationCategories.MENSTRUAL_HEALTH,
    ObservationCodes.MENSTRUAL_FLOW: ObservationCategories.MENSTRUAL_HEALTH,

    # Bi-Weekly Questionnaires
    ObservationCodes.BIWEEKLY_ANXIETY_SCORE: ObservationCategories.QUESTIONNAIRE_BIWEEKLY,
    ObservationCodes.BIWEEKLY_ASTHMA_SCORE: ObservationCategories.QUESTIONNAIRE_BIWEEKLY,
    ObservationCodes.BIWEEKLY_DEPRESSION_SCORE: ObservationCategories.QUESTIONNAIRE_BIWEEKLY,
    ObservationCodes.BIWEEKLY_BIPOLAR_SCORE: ObservationCategories.QUESTIONNAIRE_BIWEEKLY,
    ObservationCodes.BIWEEKLY_CHRONIC_PAIN_INTERFERENCE_SCORE: ObservationCategories.QUESTIONNAIRE_BIWEEKLY,
    ObservationCodes.BIWEEKLY_CHRONIC_PAIN_SCORE: ObservationCategories.QUESTIONNAIRE_BIWEEKLY,
    ObservationCodes.BIWEEKLY_COPD_SCORE: ObservationCategories.QUESTIONNAIRE_BIWEEKLY,
    ObservationCodes.BIWEEKLY_HEADACHE_SCORE: ObservationCategories.QUESTIONNAIRE_BIWEEKLY,
    ObservationCodes.BIWEEKLY_HYPERTENSION_SCORE: ObservationCategories.QUESTIONNAIRE_BIWEEKLY,
    ObservationCodes.BIWEEKLY_MIGRAINE_SCORE: ObservationCategories.QUESTIONNAIRE_BIWEEKLY,
    ObservationCodes.BIWEEKLY_COMORBIDITY_ASTHMA_DEPRESSION_ASTHMA_SCORE: ObservationCategories.QUESTIONNAIRE_BIWEEKLY,
    ObservationCodes.BIWEEKLY_COMORBIDITY_ASTHMA_DEPRESSION_DEPRESSION_SCORE: ObservationCategories.QUESTIONNAIRE_BIWEEKLY,

    # Daily Questionnaires
    ObservationCodes.DAILY_MOOD: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_MOOD_ENERGY: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_MOOD_ENERGY_MOOD: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_SHORTNESS_OF_BREATH: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_COUGH_UP_MUCUS: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_WAKE_UP_AT_NIGHT: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_ACTIVITY_PAIN_INTERFERENCE: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_RELIEF_FROM_PAIN_MEDICATION: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_ACTIVITY_PAIN: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_ANXIETY_MANAGEMENT: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_ANXIETY_RATING: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_BLOOD_PRESSURE: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_HEADACHE_TODAY: ObservationCategories.QUESTIONNAIRE_DAILY,
    ObservationCodes.DAILY_MIGRAINE_TODAY: ObservationCategories.QUESTIONNAIRE_DAILY,
}


# List of all valid observation codes for validation
ALL_OBSERVATION_CODES = [
    getattr(ObservationCodes, attr)
    for attr in dir(ObservationCodes)
    if not attr.startswith('_')
]
