"""Data collector service for PDF export"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
from sqlalchemy.orm import Session

from app.features.auth.repository import UserRepository, UserMedicationRepository, UserTrackingTopicRepository
from app.features.auth.domain.entities import User
from app.features.observations.repository import ObservationRepository
from app.features.medication.repository import MedicationAdherenceRepository
from app.features.medication.domain.entities import AdherenceStatus
from app.features.observations.constants import ObservationCodes, EnvironmentVariants
from app.features.journal.repository import JournalEntryRepository
from app.shared.constants import CONDITION_CODES, MOOD_VALUES_CHART
from app.features.export.constants import REPORT_DAYS
from app.features.export.service.chart_builder import (
    Measurement,
    MedicationCompliance,
    DailyMedication,
    PollenData,
    WeatherData,
    SleepPeriodData,
    IndividualTrackingData,
    JournalEntryData,
)


def get_condition_label(condition_code: Optional[str]) -> Optional[str]:
    """Convert condition code to human-readable label for PDF export"""
    if condition_code and condition_code in CONDITION_CODES:
        return CONDITION_CODES[condition_code].get("label", condition_code)
    return condition_code


# Observation codes used for PDF export (maps to printer service keys)
class ExportObservationCodes:
    """Observation codes specific to PDF export data collection"""

    PHQ8 = ObservationCodes.CONDITION_ASSESSMENT_DEPRESSION_SCORE
    MOOD = "mood"  # Simple mood observation code


@dataclass
class HealthDataPayload:
    """All data needed for PDF generation"""

    # User info
    name: str
    gender: Optional[str]
    age: Optional[int]
    condition: Optional[str]
    diagnosed: Optional[str]

    # 28-day measurements
    phq8: List[Measurement]
    mood: List[Measurement]
    steps_count: List[Measurement]
    active_energy_burned: List[Measurement]
    workout_duration: List[Measurement]
    heart_rate_variability: List[Measurement]
    weight: List[Measurement]
    air_quality: List[Measurement]
    time_asleep: List[Measurement]
    time_in_bed: List[Measurement]

    # Environmental
    pollen: List[PollenData]
    weather: List[WeatherData]

    # Medications
    medication: List[DailyMedication]

    # Individual tracking
    individual_tracking: List[IndividualTrackingData]

    # Sleep periods (for CSV export — individual sleep sessions with start/end)
    sleep_periods: List[SleepPeriodData]

    # Journal entries
    journal: List[JournalEntryData]

    # Report period
    start_date: date


class DataCollector:
    """Collects all health data needed for PDF export"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.observation_repo = ObservationRepository(db)
        self.medication_repo = UserMedicationRepository(db)
        self.adherence_repo = MedicationAdherenceRepository(db)
        self.tracking_topic_repo = UserTrackingTopicRepository(db)
        self.journal_repo = JournalEntryRepository(db)

    def collect_health_data(self, user_id: int, start_date: date, end_date: date = None) -> HealthDataPayload:
        """
        Collect all health data for a report period.

        Args:
            user_id: The user's ID
            start_date: Start date of the report period
            end_date: End date of the report period. Defaults to start_date + REPORT_DAYS - 1

        Returns:
            HealthDataPayload with all data needed for export
        """
        if end_date is None:
            end_date = start_date + timedelta(days=REPORT_DAYS - 1)

        # Get user profile
        user = self._get_user_profile(user_id)

        # Fetch all observations in one query
        observations = self._fetch_observations(user_id, start_date, end_date)

        # Fetch medication compliance
        medication_data = self._fetch_medication_compliance(user_id, start_date, end_date)

        # Fetch individual tracking data
        individual_tracking_data = self._fetch_individual_tracking(user_id, start_date, end_date)

        # Fetch journal entries
        journal_data = self._fetch_journal_entries(user_id, start_date, end_date)

        # Extract environment data
        pollen_data = self._extract_pollen_data(observations.get(ObservationCodes.ENVIRONMENT, []))
        weather_data = self._extract_weather_data(observations.get(ObservationCodes.ENVIRONMENT, []))
        air_quality_data = self._extract_air_quality_data(observations.get(ObservationCodes.ENVIRONMENT, []))

        return HealthDataPayload(
            name=user.full_name or "Unknown",
            gender=user.gender,
            age=self._calculate_age(user_id),
            condition=get_condition_label(self._get_leading_condition(user)),
            diagnosed=self._get_diagnosis_status(user),
            phq8=self._extract_measurements(observations.get(ExportObservationCodes.PHQ8, [])),
            mood=self._extract_mood_measurements(observations.get(ExportObservationCodes.MOOD, [])),
            steps_count=self._sum_observations_by_date(observations.get(ObservationCodes.STEPS_COUNT, [])),
            active_energy_burned=self._sum_observations_by_date(observations.get(ObservationCodes.ACTIVE_ENERGY_BURNED, [])),
            workout_duration=self._sum_observations_by_date(observations.get(ObservationCodes.WORKOUT, [])),
            heart_rate_variability=self._extract_measurements(observations.get(ObservationCodes.HEART_RATE_VARIABILITY, [])),
            weight=self._extract_measurements(observations.get(ObservationCodes.WEIGHT, [])),
            air_quality=air_quality_data,
            time_asleep=(time_asleep_data := self._extract_time_asleep(
                observations.get(ObservationCodes.TIME_LIGHT_SLEEP, []),
                observations.get(ObservationCodes.TIME_REM_SLEEP, []),
                observations.get(ObservationCodes.TIME_DEEP_SLEEP, []),
            )),
            time_in_bed=self._extract_time_in_bed(
                observations.get(ObservationCodes.TIME_IN_BED, []),
                time_asleep_data,
            ),
            pollen=pollen_data,
            weather=weather_data,
            medication=medication_data,
            individual_tracking=individual_tracking_data,
            sleep_periods=self._extract_sleep_periods(
                observations.get(ObservationCodes.TIME_LIGHT_SLEEP, []),
                observations.get(ObservationCodes.TIME_REM_SLEEP, []),
                observations.get(ObservationCodes.TIME_DEEP_SLEEP, []),
                observations.get(ObservationCodes.TIME_IN_BED, []),
            ),
            journal=journal_data,
            start_date=start_date,
        )

    def _get_user_profile(self, user_id: int) -> User:
        """Get user profile from database"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user

    def _fetch_observations(
        self, user_id: int, start_date: date, end_date: date
    ) -> Dict[str, List[Any]]:
        """
        Fetch all required observations in one query.

        Returns:
            Dictionary mapping observation codes to lists of observations
        """
        codes = [
            ExportObservationCodes.PHQ8,
            ExportObservationCodes.MOOD,
            ObservationCodes.STEPS_COUNT,
            ObservationCodes.ACTIVE_ENERGY_BURNED,
            ObservationCodes.WORKOUT,
            ObservationCodes.HEART_RATE_VARIABILITY,
            ObservationCodes.WEIGHT,
            ObservationCodes.TIME_ASLEEP,
            ObservationCodes.TIME_IN_BED,
            ObservationCodes.TIME_LIGHT_SLEEP,
            ObservationCodes.TIME_REM_SLEEP,
            ObservationCodes.TIME_DEEP_SLEEP,
            ObservationCodes.ENVIRONMENT,
        ]

        results = self.observation_repo.get_by_codes_and_date_range(
            user_id=user_id,
            codes=codes,
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.max.time()),
        )

        # Group by code
        grouped: Dict[str, List] = defaultdict(list)
        for row in results:
            grouped[row.code].append(row)

        return dict(grouped)

    def _extract_measurements(self, observations: List[Any]) -> List[Measurement]:
        """Convert observations to Measurement objects"""
        measurements = []
        for obs in observations:
            value = None
            if obs.value_decimal is not None:
                value = float(obs.value_decimal)
            elif obs.value_integer is not None:
                value = float(obs.value_integer)
            elif obs.value_string is not None:
                try:
                    value = float(obs.value_string)
                except ValueError:
                    continue

            if value is not None:
                measurements.append(
                    Measurement(
                        date=obs.effective_at.date(),
                        value=value,
                    )
                )
        return measurements

    def _sum_observations_by_date(self, observations: List[Any]) -> List[Measurement]:
        """
        Sum observation values by date.

        Used for observations where multiple entries per day should be summed
        (e.g., active energy burned from different workout sessions).
        """
        values_by_date: Dict[date, float] = defaultdict(float)

        for obs in observations:
            value = None
            if obs.value_decimal is not None:
                value = float(obs.value_decimal)
            elif obs.value_integer is not None:
                value = float(obs.value_integer)

            if value is not None:
                values_by_date[obs.effective_at.date()] += value

        return [
            Measurement(date=d, value=v)
            for d, v in sorted(values_by_date.items())
        ]

    def _extract_mood_measurements(self, observations: List[Any]) -> List[Measurement]:
        """
        Extract mood observations, converting string values to numbers (0-4 scale)
        and averaging multiple values per day.
        """
        values_by_date: Dict[date, List[float]] = defaultdict(list)

        for obs in observations:
            # Mood values are stored as strings
            if obs.value_string and obs.value_string in MOOD_VALUES_CHART:
                numeric_value = MOOD_VALUES_CHART[obs.value_string]
                values_by_date[obs.effective_at.date()].append(float(numeric_value))

        return [
            Measurement(date=d, value=sum(values) / len(values))
            for d, values in sorted(values_by_date.items())
        ]

    def _extract_time_asleep(
        self,
        light_sleep_obs: List[Any],
        rem_sleep_obs: List[Any],
        deep_sleep_obs: List[Any],
    ) -> List[Measurement]:
        """
        Extract time-asleep by summing light + REM + deep sleep stages per day.
        """
        stages_by_date: Dict[date, float] = defaultdict(float)

        for obs in light_sleep_obs + rem_sleep_obs + deep_sleep_obs:
            value = None
            if obs.value_decimal is not None:
                value = float(obs.value_decimal)
            elif obs.value_integer is not None:
                value = float(obs.value_integer)

            if value is not None:
                obs_date = obs.effective_at.date()
                stages_by_date[obs_date] += value

        return [
            Measurement(date=d, value=v)
            for d, v in sorted(stages_by_date.items())
        ]

    def _extract_time_in_bed(
        self,
        time_in_bed_obs: List[Any],
        time_asleep_measurements: List[Measurement],
    ) -> List[Measurement]:
        """
        Extract time-in-bed from time-in-bed observation.
        Falls back to time-asleep if time-in-bed not available for a date.
        """
        # Group time-in-bed observations by date
        in_bed_by_date: Dict[date, float] = defaultdict(float)

        for obs in time_in_bed_obs:
            value = None
            if obs.value_decimal is not None:
                value = float(obs.value_decimal)
            elif obs.value_integer is not None:
                value = float(obs.value_integer)

            if value is not None:
                obs_date = obs.effective_at.date()
                in_bed_by_date[obs_date] += value

        # Build time-asleep lookup for fallback
        asleep_by_date = {m.date: m.value for m in time_asleep_measurements}

        # Merge: use time-in-bed if available, else fall back to time-asleep
        all_dates = set(in_bed_by_date.keys()) | set(asleep_by_date.keys())
        measurements = []
        for d in sorted(all_dates):
            if d in in_bed_by_date:
                measurements.append(Measurement(date=d, value=in_bed_by_date[d]))
            elif d in asleep_by_date:
                measurements.append(Measurement(date=d, value=asleep_by_date[d]))

        return measurements

    def _extract_sleep_periods(
        self,
        light_sleep_obs: List[Any],
        rem_sleep_obs: List[Any],
        deep_sleep_obs: List[Any],
        time_in_bed_obs: List[Any],
    ) -> List[SleepPeriodData]:
        """
        Extract sleep periods with start/end times for CSV export.

        For time-asleep: groups sleep stage observations (light+REM+deep) by date,
        uses the earliest period_start and latest period_end.

        For time-in-bed: uses period_start/period_end from time-in-bed observations.
        """
        def _get_obs_value(obs) -> Optional[float]:
            if obs.value_decimal is not None:
                return float(obs.value_decimal)
            if obs.value_integer is not None:
                return float(obs.value_integer)
            return None

        # time-asleep: derive from sleep stages per day
        asleep_by_date: Dict[date, dict] = {}
        for obs in light_sleep_obs + rem_sleep_obs + deep_sleep_obs:
            if obs.period_start and obs.period_end:
                obs_date = obs.effective_at.date()
                value = _get_obs_value(obs) or 0.0
                if obs_date not in asleep_by_date:
                    asleep_by_date[obs_date] = {
                        "start": obs.period_start,
                        "end": obs.period_end,
                        "minutes": value,
                    }
                else:
                    entry = asleep_by_date[obs_date]
                    if obs.period_start < entry["start"]:
                        entry["start"] = obs.period_start
                    if obs.period_end > entry["end"]:
                        entry["end"] = obs.period_end
                    entry["minutes"] += value

        # time-in-bed: derive from time-in-bed observations per day
        in_bed_by_date: Dict[date, dict] = {}
        for obs in time_in_bed_obs:
            if obs.period_start and obs.period_end:
                obs_date = obs.effective_at.date()
                value = _get_obs_value(obs) or 0.0
                if obs_date not in in_bed_by_date:
                    in_bed_by_date[obs_date] = {
                        "start": obs.period_start,
                        "end": obs.period_end,
                        "minutes": value,
                    }
                else:
                    entry = in_bed_by_date[obs_date]
                    if obs.period_start < entry["start"]:
                        entry["start"] = obs.period_start
                    if obs.period_end > entry["end"]:
                        entry["end"] = obs.period_end
                    entry["minutes"] += value

        periods = []
        for d in sorted(asleep_by_date):
            entry = asleep_by_date[d]
            periods.append(SleepPeriodData(
                code="time-asleep",
                start=entry["start"],
                end=entry["end"],
                value=entry["minutes"] / 60,
            ))
        for d in sorted(in_bed_by_date):
            entry = in_bed_by_date[d]
            periods.append(SleepPeriodData(
                code="time-in-bed",
                start=entry["start"],
                end=entry["end"],
                value=entry["minutes"] / 60,
            ))

        return periods

    def _extract_pollen_data(self, environment_obs: List[Any]) -> List[PollenData]:
        """Extract pollen data from environment observations"""
        # Group by date
        pollen_by_date: Dict[date, Dict[str, Optional[float]]] = defaultdict(
            lambda: {"grass": None, "trees": None, "weeds": None}
        )

        for obs in environment_obs:
            if obs.variant in [
                EnvironmentVariants.POLLEN_GRASS,
                EnvironmentVariants.POLLEN_TREE,
                EnvironmentVariants.POLLEN_WEED,
            ]:
                obs_date = obs.effective_at.date()
                value = obs.value_integer if obs.value_integer is not None else obs.value_decimal

                if obs.variant == EnvironmentVariants.POLLEN_GRASS:
                    pollen_by_date[obs_date]["grass"] = float(value) if value else None
                elif obs.variant == EnvironmentVariants.POLLEN_TREE:
                    pollen_by_date[obs_date]["trees"] = float(value) if value else None
                elif obs.variant == EnvironmentVariants.POLLEN_WEED:
                    pollen_by_date[obs_date]["weeds"] = float(value) if value else None

        return [
            PollenData(date=d, grass=v["grass"], trees=v["trees"], weeds=v["weeds"])
            for d, v in sorted(pollen_by_date.items())
        ]

    def _extract_weather_data(self, environment_obs: List[Any]) -> List[WeatherData]:
        """Extract weather data from environment observations"""
        # Group by date
        weather_by_date: Dict[date, Dict[str, Optional[float]]] = defaultdict(
            lambda: {"temperature": None, "pressure": None}
        )

        for obs in environment_obs:
            if obs.variant in [
                EnvironmentVariants.TEMPERATURE,
                EnvironmentVariants.AIR_PRESSURE,
            ]:
                obs_date = obs.effective_at.date()
                value = obs.value_decimal if obs.value_decimal is not None else obs.value_integer

                if obs.variant == EnvironmentVariants.TEMPERATURE:
                    weather_by_date[obs_date]["temperature"] = float(value) if value else None
                elif obs.variant == EnvironmentVariants.AIR_PRESSURE:
                    weather_by_date[obs_date]["pressure"] = float(value) if value else None

        return [
            WeatherData(date=d, temperature=v["temperature"], pressure=v["pressure"])
            for d, v in sorted(weather_by_date.items())
        ]

    def _extract_air_quality_data(self, environment_obs: List[Any]) -> List[Measurement]:
        """Extract air quality index from environment observations"""
        measurements = []
        for obs in environment_obs:
            if obs.variant == EnvironmentVariants.AIR_QUALITY_INDEX:
                value = obs.value_integer if obs.value_integer is not None else obs.value_decimal
                if value is not None:
                    measurements.append(
                        Measurement(
                            date=obs.effective_at.date(),
                            value=float(value),
                        )
                    )
        return measurements

    def _fetch_medication_compliance(
        self, user_id: int, start_date: date, end_date: date
    ) -> List[DailyMedication]:
        """
        Get daily medication compliance for the report period.

        Returns:
            List of DailyMedication with compliance data per day
        """
        # Get active medications
        medications = self.medication_repo.get_by_user_id(user_id, active_only=True)
        if not medications:
            return []

        # Get adherence records for the period
        adherence_records = self.adherence_repo.get_by_user_date_range(
            user_id, start_date, end_date
        )

        # Build map: date -> medication_id -> adherence
        adherence_map: Dict[date, Dict[int, Any]] = defaultdict(dict)
        for record in adherence_records:
            adherence_map[record.date][record.medication_id] = record

        # Build daily medication list
        daily_medications = []
        current_date = start_date
        while current_date <= end_date:
            day_meds = []
            for med in medications:
                adherence = adherence_map.get(current_date, {}).get(med.id)
                if adherence:
                    # Calculate compliance based on status
                    if adherence.status == AdherenceStatus.TAKEN:
                        compliance = 1.0
                    elif adherence.status == AdherenceStatus.PARTLY_TAKEN:
                        compliance = 0.5
                    elif adherence.status == AdherenceStatus.NOT_TAKEN:
                        compliance = 0.0
                    else:  # NOT_SET
                        compliance = 0.0

                    day_meds.append(
                        MedicationCompliance(
                            title=med.medication_name,
                            compliance=compliance,
                        )
                    )

            if day_meds:
                daily_medications.append(
                    DailyMedication(date=current_date, medications=day_meds)
                )
            current_date += timedelta(days=1)

        return daily_medications

    def _fetch_individual_tracking(
        self, user_id: int, start_date: date, end_date: date
    ) -> List[IndividualTrackingData]:
        """
        Fetch individual tracking data for active topics.

        Individual tracking observations are stored with:
        - code = "individual-tracking"
        - variant = topic_code (e.g., "coffee-consumption")

        Returns:
            List of IndividualTrackingData with measurements for each topic
        """
        # Get active tracking topics for the user
        tracking_topics = self.tracking_topic_repo.get_by_user_id(user_id, active_only=True)
        if not tracking_topics:
            return []

        # Fetch all individual-tracking observations
        tracking_observations = self.observation_repo.get_by_codes_and_date_range(
            user_id=user_id,
            codes=["individual-tracking"],
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.max.time()),
        )

        # Group observations by variant (topic_code)
        obs_by_topic: Dict[str, List] = defaultdict(list)
        for obs in tracking_observations:
            if obs.variant:
                obs_by_topic[obs.variant].append(obs)

        # Build IndividualTrackingData for each active topic
        result = []
        for topic in tracking_topics:
            topic_obs = obs_by_topic.get(topic.topic_code, [])

            # Extract measurements
            measurements = []
            for obs in topic_obs:
                value = None
                if topic.data_type == "boolean":
                    # Boolean stored as value_boolean or value_integer (0/1)
                    if obs.value_boolean is not None:
                        value = 1.0 if obs.value_boolean else 0.0
                    elif obs.value_integer is not None:
                        value = float(obs.value_integer)
                else:
                    # Number type
                    if obs.value_integer is not None:
                        value = float(obs.value_integer)
                    elif obs.value_decimal is not None:
                        value = float(obs.value_decimal)

                if value is not None:
                    measurements.append(
                        Measurement(date=obs.effective_at.date(), value=value)
                    )

            result.append(
                IndividualTrackingData(
                    topic_code=topic.topic_code,
                    label=topic.topic_label,
                    data_type=topic.data_type or "number",
                    measurements=measurements,
                    min_value=topic.min_value,
                    max_value=topic.max_value,
                    unit=topic.unit,
                )
            )

        return result

    def _fetch_journal_entries(
        self, user_id: int, start_date: date, end_date: date
    ) -> List[JournalEntryData]:
        """Fetch journal entries for the report period."""
        entries, _ = self.journal_repo.get_by_user_paginated(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            page=1,
            page_size=10000,
        )
        return [
            JournalEntryData(
                date=entry.created_at,
                value=entry.content,
            )
            for entry in entries
        ]

    def _calculate_age(self, user_id: int) -> Optional[int]:
        """Calculate age from birthdate observation"""
        birthdate_obs = self.observation_repo.get_latest_by_code(
            user_id, ObservationCodes.BIRTHDATE
        )
        if birthdate_obs and birthdate_obs.value_string:
            try:
                birthdate = date.fromisoformat(birthdate_obs.value_string)
                today = date.today()
                return (
                    today.year
                    - birthdate.year
                    - ((today.month, today.day) < (birthdate.month, birthdate.day))
                )
            except ValueError:
                return None
        return None

    def _get_leading_condition(self, user: User) -> Optional[str]:
        """Get the user's leading (primary) condition"""
        if hasattr(user, "ordered_conditions") and user.ordered_conditions:
            # Return the first condition (leading)
            return user.ordered_conditions[0].condition_code
        elif hasattr(user, "conditions") and user.conditions:
            return user.conditions[0].condition_code
        return None

    def _get_diagnosis_status(self, user: User) -> Optional[str]:
        """Get the diagnosis status for the leading condition"""
        if hasattr(user, "ordered_conditions") and user.ordered_conditions:
            condition = user.ordered_conditions[0]
            if hasattr(condition, "diagnosed") and condition.diagnosed:
                return "Yes"
            return "No"
        elif hasattr(user, "conditions") and user.conditions:
            condition = user.conditions[0]
            if hasattr(condition, "diagnosed") and condition.diagnosed:
                return "Yes"
            return "No"
        return None
