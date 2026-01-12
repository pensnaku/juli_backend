"""Factor calculation logic for Juli Score"""

from typing import Optional, Tuple, Dict
from decimal import Decimal
from datetime import date, timedelta

from app.features.juli_score.constants import (
    FactorConfig,
    MOOD_VALUES,
    BIWEEKLY_TRANSFORMATIONS,
)
from app.features.juli_score.repository import JuliScoreRepository


class FactorCalculator:
    """Calculates individual factor values for Juli Score"""

    def __init__(self, repo: JuliScoreRepository, user_id: int, target_date: date):
        self.repo = repo
        self.user_id = user_id
        self.target_date = target_date

    def calculate_factor(
        self,
        factor_name: str,
        config: FactorConfig,
        condition_code: str,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate a factor value.

        Returns:
            Tuple of (calculated_score, raw_input) or (None, None) if data unavailable
        """
        raw_value = self._get_raw_value(factor_name, config, condition_code)

        if raw_value is None:
            return None, None

        # Apply transformation for bi-weekly questionnaire
        transformed_value = raw_value
        if factor_name == "biweekly":
            transform = BIWEEKLY_TRANSFORMATIONS.get(condition_code)
            if transform:
                transformed_value = transform(float(raw_value))

        # Calculate factor score
        if config.just_math:
            # Special handling for active_energy to use exact 1/3 for precision
            if factor_name == "active_energy":
                calculated = float(transformed_value) / 3.0
            else:
                calculated = float(transformed_value) * (config.multiplier or 1.0)
        else:
            calculated = self._apply_steps(float(transformed_value), config)

        # Cap at weight and apply minimum
        calculated = max(config.minimum_score, min(calculated, config.weight))

        return calculated, raw_value

    def _get_raw_value(
        self,
        factor_name: str,
        config: FactorConfig,
        condition_code: str,
    ) -> Optional[float]:
        """Get raw observation value for a factor"""

        # Special handling for medication compliance
        if factor_name == "medication":
            return self._get_medication_compliance()

        # Special handling for mood (string -> numeric)
        if factor_name == "mood":
            mood_str = self.repo.get_observation_string_for_date(
                self.user_id,
                config.observation_code,
                self.target_date,
                config.observation_variant,
            )
            return float(MOOD_VALUES.get(mood_str, 0)) if mood_str else None

        # Special handling for sleep (sum stages if time-asleep not available)
        if factor_name == "sleep":
            return self._get_sleep_total(config)

        # Special handling for HRV (diff from average)
        if factor_name == "hrv":
            return self._get_hrv_diff(config)

        # Special handling for active energy (10-day average)
        if factor_name == "active_energy":
            avg = self.repo.get_average_value_for_period(
                self.user_id,
                config.observation_code,
                config.time_window_days,
                self.target_date,
                config.observation_variant,
            )
            return float(avg) if avg else None

        # Bi-weekly questionnaire: get most recent in window
        if factor_name == "biweekly":
            value = self.repo.get_latest_value_in_period(
                self.user_id,
                config.observation_code,
                config.time_window_days,
                self.target_date,
                config.observation_variant,
            )
            return float(value) if value else None

        # Default: get today's value
        if not config.observation_code:
            return None

        value = self.repo.get_observation_value_for_date(
            self.user_id,
            config.observation_code,
            self.target_date,
            config.observation_variant,
        )
        return float(value) if value else None

    def _get_medication_compliance(self) -> Optional[float]:
        """
        Calculate medication compliance as percentage (0-1).
        Currently returns None (factor skipped) - to be implemented later.
        """
        # TODO: Implement based on user medications and tracking
        return None

    def _get_sleep_total(self, config: FactorConfig) -> Optional[float]:
        """
        Get total sleep time in minutes.
        First tries 'time-asleep', then sums sleep stages if not available.
        """
        # Try direct time-asleep first
        value = self.repo.get_observation_value_for_date(
            self.user_id,
            config.observation_code,  # "time-asleep"
            self.target_date,
            config.observation_variant,
        )
        if value is not None:
            return float(value)

        # Fall back to summing sleep stages
        sleep_stage_codes = [
            "time-light-sleep",
            "time-rem-sleep",
            "time-deep-sleep",
        ]

        total_sleep = 0.0
        has_any_stage = False

        for code in sleep_stage_codes:
            stage_value = self.repo.get_observation_value_for_date(
                self.user_id,
                code,
                self.target_date,
                None,  # No variant for sleep stage codes
            )
            if stage_value is not None:
                total_sleep += float(stage_value)
                has_any_stage = True

        return total_sleep if has_any_stage else None

    def _get_hrv_diff(self, config: FactorConfig) -> Optional[float]:
        """Get HRV value as difference from 10-day average"""
        # Get all HRV values for the period
        hrv_values = self.repo.get_hrv_values_for_period(
            self.user_id,
            config.observation_code,
            config.time_window_days,
            self.target_date,
            config.observation_variant,
        )

        if len(hrv_values) < 2:
            return None

        # Latest value (index 0 since ordered desc)
        latest_hrv = float(hrv_values[0])

        # Average of previous values (excluding latest)
        previous_values = [float(v) for v in hrv_values[1:11]]  # Up to 10 previous
        if not previous_values:
            return None

        avg_hrv = sum(previous_values) / len(previous_values)

        return latest_hrv - avg_hrv

    def _apply_steps(self, value: float, config: FactorConfig) -> float:
        """Apply step-based calculation"""
        if not config.steps:
            return 0.0

        for step in config.steps:
            if step.lower_bound <= value <= step.upper_bound:
                return config.weight * step.multiplier

        # Default to 0 if no step matches
        return 0.0


def calculate_factors_for_condition(
    repo: JuliScoreRepository,
    user_id: int,
    condition_code: str,
    factors_config: Dict[str, FactorConfig],
    target_date: date,
) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
    """
    Calculate all factors for a condition.

    Returns:
        Dict mapping factor_name to (score, raw_input) tuple
    """
    calculator = FactorCalculator(repo, user_id, target_date)
    results = {}

    for factor_name, config in factors_config.items():
        score, raw_input = calculator.calculate_factor(
            factor_name, config, condition_code
        )
        results[factor_name] = (score, raw_input)

    return results
