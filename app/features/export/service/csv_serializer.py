"""Serializer for CSV/XLSX data download endpoint.

Converts HealthDataPayload dataclasses into the JSON format expected
by the mobile app for client-side XLSX generation.
"""
from typing import List, Optional

from app.features.export.service.data_collector import HealthDataPayload
from app.features.export.service.chart_builder import (
    Measurement,
    DailyMedication,
    PollenData,
    WeatherData,
    SleepPeriodData,
    IndividualTrackingData,
    JournalEntryData,
)


def serialize_health_data_for_csv(payload: HealthDataPayload) -> dict:
    """Convert HealthDataPayload to the JSON format expected by the mobile app."""
    asleep_periods = [p for p in payload.sleep_periods if p.code == "time-asleep"]
    in_bed_periods = [p for p in payload.sleep_periods if p.code == "time-in-bed"]

    return {
        "start_date": payload.start_date.isoformat(),
        "name": payload.name,
        "gender": (payload.gender or "").title(),
        "condition": payload.condition or "",
        "diagnosed": payload.diagnosed or "No",
        "medication": _serialize_medication(payload.medication),
        "weather": _serialize_weather(payload.weather),
        "phq8": _serialize_measurements(payload.phq8),
        "DE5": [],
        "pollen": _serialize_pollen(payload.pollen),
        "time-in-bed": _serialize_sleep_periods(in_bed_periods),
        "time-asleep": _serialize_sleep_periods(asleep_periods),
        "steps-count": _serialize_measurements(payload.steps_count),
        "active-energy-burned": _serialize_measurements(payload.active_energy_burned),
        "workout-duration": _serialize_measurements(payload.workout_duration),
        "mood": _serialize_measurements(payload.mood),
        "heart-rate-variability": _serialize_measurements(payload.heart_rate_variability),
        "weight": _serialize_measurements(payload.weight),
        "air-quality": _serialize_measurements(payload.air_quality),
        "journal": _serialize_journal(payload.journal),
        "individual-tracking": _serialize_individual_tracking(payload.individual_tracking),
    }


def _serialize_measurements(
    measurements: List[Measurement], divide_by: Optional[float] = None
) -> List[dict]:
    result = []
    for m in measurements:
        value = m.value
        if value is not None and divide_by:
            value = value / divide_by
        result.append({"date": m.date.isoformat(), "value": value})
    return result


def _serialize_sleep_periods(periods: List[SleepPeriodData]) -> List[dict]:
    return [
        {
            "code": p.code,
            "start": p.start.isoformat(),
            "end": p.end.isoformat(),
            "value": p.value,
        }
        for p in periods
    ]


def _serialize_medication(medication: List[DailyMedication]) -> List[dict]:
    return [
        {
            "date": day.date.isoformat(),
            "medications": [
                {"title": med.title, "compliance": med.compliance}
                for med in day.medications
            ],
        }
        for day in medication
    ]


def _serialize_pollen(pollen: List[PollenData]) -> List[dict]:
    return [
        {
            "date": p.date.isoformat(),
            "trees": p.trees,
            "grass": p.grass,
            "weeds": p.weeds,
        }
        for p in pollen
    ]


def _serialize_weather(weather: List[WeatherData]) -> List[dict]:
    return [
        {
            "date": w.date.isoformat(),
            "temperature": w.temperature,
            "pressure": w.pressure,
        }
        for w in weather
    ]


def _serialize_journal(journal: List[JournalEntryData]) -> List[dict]:
    return [
        {
            "date": entry.date.isoformat() if entry.date else None,
            "value": entry.value,
        }
        for entry in journal
    ]


def _serialize_individual_tracking(
    tracking: List[IndividualTrackingData],
) -> dict:
    result = {}
    for topic in tracking:
        result[topic.label] = {
            "measurements": _serialize_measurements(topic.measurements),
            "type": topic.data_type,
            "referenceRange": {
                "min": topic.min_value,
                "max": topic.max_value,
            },
        }
    return result
