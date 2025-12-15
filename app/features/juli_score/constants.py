"""Juli Score constants and factor configurations"""
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

from app.shared.constants import CONDITION_CODES


# Supported condition codes for Juli Score (reference existing codes)
class JuliScoreConditions:
    """Condition codes supported by Juli Score calculation"""
    DEPRESSION = "35489007"
    ASTHMA = "195967001"
    MIGRAINE = "37796009"


class JuliScoreCodes:
    """Observation codes for juli scores"""
    DEPRESSION = "juli-score-depression"
    ASTHMA = "juli-score-asthma"
    MIGRAINE = "juli-score-migraine"


# Mapping condition codes to score codes
CONDITION_TO_SCORE_CODE = {
    JuliScoreConditions.DEPRESSION: JuliScoreCodes.DEPRESSION,
    JuliScoreConditions.ASTHMA: JuliScoreCodes.ASTHMA,
    JuliScoreConditions.MIGRAINE: JuliScoreCodes.MIGRAINE,
}

# Get condition names from shared constants
def get_condition_name(condition_code: str) -> str:
    """Get human-readable condition name from shared constants"""
    condition = CONDITION_CODES.get(condition_code)
    return condition["label"] if condition else condition_code


# Supported condition codes list
SUPPORTED_CONDITION_CODES = [
    JuliScoreConditions.DEPRESSION,
    JuliScoreConditions.ASTHMA,
    JuliScoreConditions.MIGRAINE,
]


@dataclass
class Step:
    """Step definition for step-based factor calculation"""
    lower_bound: float
    upper_bound: float
    multiplier: float


@dataclass
class FactorConfig:
    """Configuration for a single factor"""
    weight: int
    minimum_score: float
    just_math: bool
    multiplier: Optional[float] = None
    steps: List[Step] = field(default_factory=list)
    observation_code: Optional[str] = None
    time_window_days: int = 0  # 0 = today only


# Mood value mapping
MOOD_VALUES = {
    "very-bad": 1,
    "bad": 2,
    "good": 3,
    "very-good": 4,
    "excellent": 5,
}

# Bi-weekly score transformations by condition
BIWEEKLY_TRANSFORMATIONS: Dict[str, Callable[[float], float]] = {
    JuliScoreConditions.DEPRESSION: lambda raw: 32 - raw,
    JuliScoreConditions.ASTHMA: lambda raw: raw,  # No transformation
    JuliScoreConditions.MIGRAINE: lambda raw: 78 - raw,
}


# Factor configurations by condition
DEPRESSION_FACTORS: Dict[str, FactorConfig] = {
    "air_quality": FactorConfig(
        weight=20,
        minimum_score=0,
        just_math=False,
        observation_code="air-quality",
        time_window_days=0,
        steps=[
            Step(0, 50, 1.0),
            Step(51, 100, 0.5),
            Step(101, float('inf'), 0.0),
        ]
    ),
    "sleep": FactorConfig(
        weight=20,
        minimum_score=-10,  # Can go negative
        just_math=False,
        observation_code="time-asleep",
        time_window_days=0,
        steps=[
            Step(420, float('inf'), 1.0),     # 7+ hours
            Step(360, 419, 0.7),               # 6-7 hours
            Step(300, 359, 0.2),               # 5-6 hours
            Step(0, 299, -0.5),                # <5 hours
        ]
    ),
    "biweekly": FactorConfig(
        weight=64,
        minimum_score=0,
        just_math=True,
        multiplier=2.0,
        observation_code="bi-weekly-depression-questionnaire-score",
        time_window_days=14,
    ),
    "active_energy": FactorConfig(
        weight=50,
        minimum_score=0,
        just_math=True,
        multiplier=0.333,
        observation_code="active-energy-burned",
        time_window_days=10,  # Uses average
    ),
    "medication": FactorConfig(
        weight=30,
        minimum_score=0,
        just_math=True,
        multiplier=30.0,
        observation_code=None,  # Special handling
        time_window_days=0,
    ),
    "mood": FactorConfig(
        weight=25,
        minimum_score=0,
        just_math=True,
        multiplier=5.0,
        observation_code="daily-questionnaire-mood",
        time_window_days=0,
    ),
    "hrv": FactorConfig(
        weight=20,
        minimum_score=0,
        just_math=False,
        observation_code="heart-rate-variability",
        time_window_days=30,
        steps=[
            Step(0, float('inf'), 1.0),           # >= 0: full score (1.0)
            Step(-10, -0.01, 0.5),                # [-10, 0): half score (0.5)
            Step(-15, -10.01, 0.25),              # [-15, -10): quarter score (0.25)
            Step(float('-inf'), -15.01, 0.0),    # < -15: no score (0.0)
        ]
    ),
}

ASTHMA_FACTORS: Dict[str, FactorConfig] = {
    "air_quality": FactorConfig(
        weight=20,
        minimum_score=0,
        just_math=False,
        observation_code="air-quality",
        time_window_days=0,
        steps=[
            Step(0, 50, 1.0),
            Step(51, 100, 0.5),
            Step(101, float('inf'), 0.0),
        ]
    ),
    "sleep": FactorConfig(
        weight=20,
        minimum_score=-10,
        just_math=False,
        observation_code="time-asleep",
        time_window_days=0,
        steps=[
            Step(420, float('inf'), 1.0),
            Step(360, 419, 0.7),
            Step(300, 359, 0.2),
            Step(0, 299, -0.5),
        ]
    ),
    "biweekly": FactorConfig(
        weight=50,
        minimum_score=0,
        just_math=True,
        multiplier=2.0,
        observation_code="bi-weekly-asthma-questionnaire-score",
        time_window_days=14,
    ),
    "active_energy": FactorConfig(
        weight=50,
        minimum_score=0,
        just_math=True,
        multiplier=0.333,
        observation_code="active-energy-burned",
        time_window_days=10,
    ),
    "medication": FactorConfig(
        weight=30,
        minimum_score=0,
        just_math=True,
        multiplier=30.0,
        observation_code=None,
        time_window_days=0,
    ),
    "mood": FactorConfig(
        weight=15,
        minimum_score=0,
        just_math=True,
        multiplier=3.0,
        observation_code="daily-questionnaire-mood",
        time_window_days=0,
    ),
    "hrv": FactorConfig(
        weight=40,
        minimum_score=0,
        just_math=False,
        observation_code="heart-rate-variability",
        time_window_days=30,
        steps=[
            Step(0, float('inf'), 1.0),           # >= 0: full score (1.0)
            Step(-6, -0.01, 0.75),                # [-6, 0): 0.75 score
            Step(-14, -6.01, 0.5),                # [-14, -6): half score (0.5)
            Step(float('-inf'), -14.01, 0.25),   # < -14: quarter score (0.25)
        ]
    ),
    "pollen": FactorConfig(
        weight=30,
        minimum_score=0,
        just_math=False,
        observation_code="air-quality-pollen",
        time_window_days=0,
        steps=[
            Step(0, 50, 1.0),
            Step(51, 85, 0.5),
            Step(86, 100, 0.2),
            Step(101, float('inf'), 0.0),
        ]
    ),
    "inhaler": FactorConfig(
        weight=30,
        minimum_score=0,
        just_math=False,
        observation_code="inhaler-usage-count",
        time_window_days=0,
        steps=[
            Step(0, 0.5, 1.0),  # 0 uses
            Step(0.5, 1.5, 0.5),  # 1 use
            Step(1.5, float('inf'), 0.0),  # 2+ uses
        ]
    ),
}

MIGRAINE_FACTORS: Dict[str, FactorConfig] = {
    "air_quality": FactorConfig(
        weight=30,
        minimum_score=-6,  # Can go negative for AQI > 140
        just_math=False,
        observation_code="air-quality",
        time_window_days=0,
        steps=[
            Step(0, 50, 1.0),       # AQI 0-50: full score (30)
            Step(51, 100, 0.5),     # AQI 51-100: half score (15)
            Step(101, 140, 0.0),    # AQI 101-140: no score (0)
            Step(141, float('inf'), -0.2),  # AQI > 140: negative (-6)
        ]
    ),
    "sleep": FactorConfig(
        weight=20,
        minimum_score=-10,
        just_math=False,
        observation_code="time-asleep",
        time_window_days=0,
        steps=[
            Step(420, float('inf'), 1.0),
            Step(360, 419, 0.7),
            Step(300, 359, 0.2),
            Step(0, 299, -0.5),
        ]
    ),
    "biweekly": FactorConfig(
        weight=42,
        minimum_score=0,
        just_math=True,
        multiplier=1.0,
        observation_code="bi-weekly-migraine-questionnaire-score",
        time_window_days=14,
    ),
    "active_energy": FactorConfig(
        weight=30,
        minimum_score=0,
        just_math=True,
        multiplier=0.333,
        observation_code="active-energy-burned",
        time_window_days=10,
    ),
    "mood": FactorConfig(
        weight=15,
        minimum_score=0,
        just_math=True,
        multiplier=3.0,
        observation_code="daily-questionnaire-mood",
        time_window_days=0,
    ),
    "hrv": FactorConfig(
        weight=60,
        minimum_score=0,
        just_math=False,
        observation_code="heart-rate-variability",
        time_window_days=30,
        steps=[
            Step(0, float('inf'), 1.0),           # >= 0: full score (1.0)
            Step(-10, -0.01, 0.5),                # [-10, 0): half score (0.5)
            Step(-15, -10.01, 0.25),              # [-15, -10): quarter score (0.25)
            Step(float('-inf'), -15.01, 0.0),    # < -15: no score (0.0)
        ]
    ),
}

# Map condition codes to factor configs
CONDITION_FACTORS: Dict[str, Dict[str, FactorConfig]] = {
    JuliScoreConditions.DEPRESSION: DEPRESSION_FACTORS,
    JuliScoreConditions.ASTHMA: ASTHMA_FACTORS,
    JuliScoreConditions.MIGRAINE: MIGRAINE_FACTORS,
}

# Minimum data points required to calculate score
MIN_DATA_POINTS = 3

# Scheduler configuration
SCHEDULER_INTERVAL_MINUTES = 2
ACTIVE_USER_DAYS = 2  # Only process users active in last N days
