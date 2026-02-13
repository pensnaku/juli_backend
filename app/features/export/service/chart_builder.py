"""SVG chart path building for PDF export"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, List, Tuple, Dict

from app.features.export.constants import REPORT_DAYS


@dataclass
class Point:
    """A point on the SVG chart"""

    x: int  # 0-27 for 28 days
    y: int  # 0-100 scaled value


@dataclass
class ChartPath:
    """SVG path data with continuous sections and gap connectors"""

    sections: List[List[Point]]  # Continuous line segments
    joints: List[Tuple[Point, Point]]  # Dashed lines connecting gaps


@dataclass(kw_only=True)
class Measurement:
    """A single measurement value on a specific date"""

    date: date
    value: Optional[float]


@dataclass(kw_only=True)
class MedicationCompliance:
    """Medication compliance data"""

    title: str
    compliance: float  # 0.0-1.0


@dataclass(kw_only=True)
class DailyMedication:
    """Daily medication schedule with compliance"""

    date: date
    medications: List[MedicationCompliance]


@dataclass(kw_only=True)
class PollenData:
    """Pollen information for a specific date"""

    date: date
    grass: Optional[float]
    trees: Optional[float]
    weeds: Optional[float]


@dataclass(kw_only=True)
class WeatherData:
    """Weather information for a specific date"""

    date: date
    temperature: Optional[float]
    pressure: Optional[float]


@dataclass(kw_only=True)
class SleepPeriodData:
    """Sleep period data with start/end times for CSV export"""

    code: str  # "time-in-bed" or "time-asleep"
    start: datetime
    end: datetime
    value: float  # duration in hours


@dataclass(kw_only=True)
class JournalEntryData:
    """Journal entry data for export"""

    date: datetime
    value: str


@dataclass(kw_only=True)
class IndividualTrackingData:
    """Individual tracking topic data for PDF export"""

    topic_code: str
    label: str
    data_type: str  # "number" or "boolean"
    measurements: List[Measurement]
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    unit: Optional[str] = None


def build_path(measurements: List[Optional[int]]) -> ChartPath:
    """
    Convert a list of 28 measurements to SVG path data.

    Args:
        measurements: List of 28 values (None for missing data)

    Returns:
        ChartPath with continuous sections and gap joints
    """
    paths = ChartPath(sections=[], joints=[])
    next_path_components: List[Point] = []
    last_point_seen: Optional[Point] = None
    had_missing_points = False

    for index, measurement in enumerate(measurements):
        if measurement is not None:
            point = Point(x=index, y=measurement)

            if had_missing_points and last_point_seen is not None:
                paths.joints.append((last_point_seen, point))

            had_missing_points = False
            last_point_seen = point
            next_path_components.append(point)
        else:
            if next_path_components:
                paths.sections.append(next_path_components)
                next_path_components = []

            had_missing_points = True

    if next_path_components:
        paths.sections.append(next_path_components)

    return paths


def clamp_to_borders(
    value: Optional[float],
    maximum: float,
    minimum: float = 0,
    lower_bound: int = 0,
    upper_bound: int = 100,
    inverted: bool = False,
) -> Optional[int]:
    """
    Normalize a value to SVG coordinate space.

    Args:
        value: Raw measurement value
        maximum: Upper bound of measurement scale
        minimum: Lower bound of measurement scale
        lower_bound: SVG y-axis minimum
        upper_bound: SVG y-axis maximum
        inverted: Flip scale (True = inverted)

    Returns:
        Normalized integer value for SVG, or None if value is None
    """
    if value is None:
        return None

    bounded = max(
        0,
        min(
            (value - minimum) / (maximum - minimum) * (upper_bound - lower_bound),
            upper_bound - lower_bound,
        ),
    )
    result = lower_bound + bounded if not inverted else upper_bound - bounded
    return int(result)


def assign_to_period_range(
    measurements: List[Measurement], days: int, from_date: date
) -> List[Optional[float]]:
    """
    Map measurements to a date range, filling gaps with None.

    Args:
        measurements: List of Measurement objects
        days: Number of days in the range
        from_date: Start date of the range

    Returns:
        List of values aligned to each day (None for missing)
    """
    history_period = [from_date + timedelta(days=d) for d in range(days)]

    return [
        next((m.value for m in measurements if m.date == day), None)
        for day in history_period
    ]


class ChartBuilder:
    """Builds all chart data for PDF export"""

    def prepare_chart_content(
        self,
        start_date: date,
        phq8: List[Measurement],
        mood: List[Measurement],
        medication_schedule: List[DailyMedication],
        steps_count: List[Measurement],
        active_energy_burned: List[Measurement],
        workout_duration: List[Measurement],
        time_asleep: List[Measurement],
        time_in_bed: List[Measurement],
        heart_rate_variability: List[Measurement],
        weight: List[Measurement],
        air_quality: List[Measurement],
        pollen: List[PollenData],
        weather: List[WeatherData],
        individual_tracking: Optional[List[IndividualTrackingData]] = None,
    ) -> dict:
        """
        Prepare all chart data for PDF rendering.

        Args:
            start_date: Report start date
            All measurement lists for 28 days

        Returns:
            Dictionary with all chart paths ready for template rendering
        """
        has_medication = bool(medication_schedule)

        return {
            "phq8": build_path(
                [
                    clamp_to_borders(
                        m,
                        maximum=24,
                        lower_bound=20 if has_medication else 0,
                        inverted=True,
                    )
                    for m in assign_to_period_range(phq8, REPORT_DAYS, start_date)
                ]
            ),
            "mood": build_path(
                [
                    clamp_to_borders(
                        m,
                        maximum=4,
                        lower_bound=20 if has_medication else 0,
                    )
                    for m in assign_to_period_range(mood, REPORT_DAYS, start_date)
                ]
            ),
            "medication": self._build_medication_chart(
                medication_schedule, start_date
            ),
            "activity": {
                "steps": {
                    "legend": [20000, 15000, 10000, 5000, 0],
                    "measurements": build_path(
                        [
                            clamp_to_borders(m, maximum=20000)
                            for m in assign_to_period_range(
                                steps_count, REPORT_DAYS, start_date
                            )
                        ]
                    ),
                },
                "calories": {
                    "legend": [400, 300, 200, 100, 0],
                    "measurements": build_path(
                        [
                            clamp_to_borders(m, maximum=400)
                            for m in assign_to_period_range(
                                active_energy_burned, REPORT_DAYS, start_date
                            )
                        ]
                    ),
                },
                "workout": {
                    "legend": [40, 30, 20, 10, 0],
                    "measurements": build_path(
                        [
                            clamp_to_borders(m, maximum=40)
                            for m in assign_to_period_range(
                                workout_duration, REPORT_DAYS, start_date
                            )
                        ]
                    ),
                },
            },
            "sleep": {
                "legend": [10, 7.5, 5, 2.5, 0],
                "measurements": {
                    "inbed": build_path(
                        [
                            # Convert minutes to hours
                            clamp_to_borders(m / 60 if m else None, maximum=10)
                            for m in assign_to_period_range(
                                time_in_bed, REPORT_DAYS, start_date
                            )
                        ]
                    ),
                    "asleep": build_path(
                        [
                            # Convert minutes to hours
                            clamp_to_borders(m / 60 if m else None, maximum=10)
                            for m in assign_to_period_range(
                                time_asleep, REPORT_DAYS, start_date
                            )
                        ]
                    ),
                },
            },
            "hrv": {
                "legend": [100, 75, 50, 25, 0],
                "measurements": build_path(
                    [
                        clamp_to_borders(m, maximum=100)
                        for m in assign_to_period_range(
                            heart_rate_variability, REPORT_DAYS, start_date
                        )
                    ]
                ),
            },
            "weight": {
                "legend": [75, 70, 65, 60, 55],
                "measurements": build_path(
                    [
                        clamp_to_borders(m, minimum=55, maximum=75)
                        for m in assign_to_period_range(weight, REPORT_DAYS, start_date)
                    ]
                ),
            },
            "airquality": {
                "legend": [120, 90, 60, 30, 0],
                "measurements": build_path(
                    [
                        clamp_to_borders(m, maximum=120)
                        for m in assign_to_period_range(
                            air_quality, REPORT_DAYS, start_date
                        )
                    ]
                ),
            },
            "pollen": self._build_pollen_charts(pollen, start_date),
            "weather": self._build_weather_charts(weather, start_date),
            "individual_tracking": self._build_individual_tracking_charts(
                individual_tracking or [], start_date
            ),
        }

    def _build_medication_chart(
        self, medication_schedule: List[DailyMedication], start_date: date
    ) -> dict:
        """Build medication compliance chart data"""
        if not medication_schedule:
            return {"title": "", "compliance": None}

        # Get unique medication titles
        titles = dict.fromkeys(
            m.title
            for day in medication_schedule
            for m in day.medications
        )

        # Calculate daily average compliance
        compliance_measurements = [
            Measurement(
                date=day.date,
                value=sum(m.compliance for m in day.medications) / len(day.medications),
            )
            for day in medication_schedule
            if day.medications
        ]

        return {
            "title": ", ".join(titles),
            "compliance": build_path(
                [
                    clamp_to_borders(m, maximum=1, upper_bound=10)
                    for m in assign_to_period_range(
                        compliance_measurements, REPORT_DAYS, start_date
                    )
                ]
            ),
        }

    def _build_pollen_charts(
        self, pollen: List[PollenData], start_date: date
    ) -> dict:
        """Build pollen chart data for grass, trees, and weeds"""
        return {
            "grass": build_path(
                [
                    clamp_to_borders(m, maximum=3)
                    for m in assign_to_period_range(
                        [
                            Measurement(date=p.date, value=p.grass)
                            for p in pollen
                            if p.grass is not None
                        ],
                        REPORT_DAYS,
                        start_date,
                    )
                ]
            ),
            "trees": build_path(
                [
                    clamp_to_borders(m, maximum=3)
                    for m in assign_to_period_range(
                        [
                            Measurement(date=p.date, value=p.trees)
                            for p in pollen
                            if p.trees is not None
                        ],
                        REPORT_DAYS,
                        start_date,
                    )
                ]
            ),
            "weeds": build_path(
                [
                    clamp_to_borders(m, maximum=3)
                    for m in assign_to_period_range(
                        [
                            Measurement(date=p.date, value=p.weeds)
                            for p in pollen
                            if p.weeds is not None
                        ],
                        REPORT_DAYS,
                        start_date,
                    )
                ]
            ),
        }

    def _build_weather_charts(
        self, weather: List[WeatherData], start_date: date
    ) -> dict:
        """Build weather chart data for temperature and pressure"""
        return {
            "temperature": {
                "legend": [35, 20, 5, -10, -25],
                "measurements": build_path(
                    [
                        clamp_to_borders(m, minimum=-25, maximum=35)
                        for m in assign_to_period_range(
                            [
                                Measurement(date=w.date, value=w.temperature)
                                for w in weather
                                if w.temperature is not None
                            ],
                            REPORT_DAYS,
                            start_date,
                        )
                    ]
                ),
            },
            "pressure": {
                "legend": [780, 770, 760, 750, 740],
                "measurements": build_path(
                    [
                        clamp_to_borders(m, minimum=740, maximum=780)
                        for m in assign_to_period_range(
                            [
                                Measurement(date=w.date, value=w.pressure)
                                for w in weather
                                if w.pressure is not None
                            ],
                            REPORT_DAYS,
                            start_date,
                        )
                    ]
                ),
            },
        }

    def _build_individual_tracking_charts(
        self, tracking_data: List[IndividualTrackingData], start_date: date
    ) -> Dict[str, dict]:
        """Build individual tracking chart data for each topic"""
        result = {}

        for topic in tracking_data:
            # For number types, use min/max to determine scale
            if topic.data_type == "number":
                min_val = topic.min_value or 0
                max_val = topic.max_value or 10

                # Generate legend (5 evenly spaced values)
                step = (max_val - min_val) / 4
                legend = [max_val - i * step for i in range(5)]

                period_values = assign_to_period_range(topic.measurements, REPORT_DAYS, start_date)
                clamped_values = [clamp_to_borders(m, minimum=min_val, maximum=max_val) for m in period_values]

                result[topic.topic_code] = {
                    "label": topic.label,
                    "type": topic.data_type,
                    "unit": topic.unit,
                    "legend": legend,
                    "referenceRange": {
                        "min": min_val,
                        "max": max_val,
                    },
                    "measurements": build_path(clamped_values),
                }
            else:
                # Boolean type - 0 or 1
                period_values = assign_to_period_range(topic.measurements, REPORT_DAYS, start_date)
                clamped_values = [clamp_to_borders(m, minimum=0, maximum=1) for m in period_values]
                result[topic.topic_code] = {
                    "label": topic.label,
                    "type": topic.data_type,
                    "unit": None,
                    "legend": ["Yes", "No"],
                    "referenceRange": {"min": 0, "max": 1},
                    "measurements": build_path(clamped_values),
                }

        return result
