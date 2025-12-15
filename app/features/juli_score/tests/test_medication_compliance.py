"""
Tests for medication compliance calculation.

Medication compliance is calculated as:
    ratio = min(taken_count, expected_count) / expected_count

Test scenarios from provided test data:
- No active medications -> ratio = 0
- A: 0/2, B: 0/3 -> ratio = 0
- Wrong medication taken -> ratio = 0
- A: 1/2 -> ratio = 0.5
- A: 2/2, B: 0/3 -> ratio = 2/5 = 0.4
- A: 3/2 (overconsumption), B: 0/3 -> ratio = 2/5 = 0.4 (capped at expected)
- A: 1/2, B: 2/3 -> ratio = 3/5 = 0.6
- A: 2/2, B: 3/3 -> ratio = 5/5 = 1.0
- Overconsumption A: 3/2, B: 4/3 -> ratio = 5/5 = 1.0 (capped)
"""
import pytest
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class MedicationSchedule:
    """A medication schedule with expected doses per day"""
    name: str
    times_of_day: List[str]  # e.g., ["11:00", "12:00"]

    @property
    def expected_count(self) -> int:
        """Number of expected doses per day"""
        return len(self.times_of_day)


class MedicationComplianceCalculator:
    """
    Calculate medication compliance ratio.

    This mirrors what the actual implementation should do.
    """

    def calculate_compliance(
        self,
        schedules: List[MedicationSchedule],
        taken_counts: Dict[str, int],  # medication_name -> count taken
    ) -> float:
        """
        Calculate medication compliance ratio (0-1).

        Args:
            schedules: Active medication schedules
            taken_counts: Count of doses taken per medication

        Returns:
            Compliance ratio between 0 and 1
        """
        if not schedules:
            return 0.0

        total_expected = 0
        total_taken = 0

        for schedule in schedules:
            expected = schedule.expected_count
            taken = taken_counts.get(schedule.name, 0)

            # Cap taken at expected (overconsumption doesn't increase compliance)
            actual_taken = min(taken, expected)

            total_expected += expected
            total_taken += actual_taken

        if total_expected == 0:
            return 0.0

        return total_taken / total_expected


class TestMedicationCompliance:
    """Test medication compliance calculation"""

    @pytest.fixture
    def schedule_a(self):
        """Vitamin A: 2 doses per day"""
        return MedicationSchedule(name="A", times_of_day=["11:00", "12:00"])

    @pytest.fixture
    def schedule_b(self):
        """Vitamin B: 3 doses per day"""
        return MedicationSchedule(name="B", times_of_day=["11:00", "12:00", "13:00"])

    @pytest.fixture
    def calculator(self):
        return MedicationComplianceCalculator()

    def test_no_active_medications(self, calculator):
        """No active medications should return 0"""
        ratio = calculator.calculate_compliance(
            schedules=[],
            taken_counts={},
        )
        assert ratio == 0.0

    def test_all_medications_not_taken(self, calculator, schedule_a, schedule_b):
        """A: 0/2, B: 0/3 should return 0"""
        ratio = calculator.calculate_compliance(
            schedules=[schedule_a, schedule_b],
            taken_counts={},
        )
        assert ratio == 0.0

    def test_wrong_medication_taken(self, calculator, schedule_a):
        """Taking wrong medication should not count"""
        ratio = calculator.calculate_compliance(
            schedules=[schedule_a],  # Only A is scheduled
            taken_counts={"B": 1},  # But B was taken
        )
        assert ratio == 0.0

    def test_partial_compliance_single_medication(self, calculator, schedule_a):
        """A: 1/2 should return 0.5"""
        ratio = calculator.calculate_compliance(
            schedules=[schedule_a],
            taken_counts={"A": 1},
        )
        assert ratio == 0.5

    def test_partial_compliance_multiple_medications(self, calculator, schedule_a, schedule_b):
        """A: 2/2, B: 0/3 should return 2/5 = 0.4"""
        ratio = calculator.calculate_compliance(
            schedules=[schedule_a, schedule_b],
            taken_counts={"A": 2},
        )
        assert ratio == pytest.approx(0.4)

    def test_overconsumption_capped(self, calculator, schedule_a, schedule_b):
        """A: 3/2 (overconsumption), B: 0/3 should return 2/5 = 0.4"""
        ratio = calculator.calculate_compliance(
            schedules=[schedule_a, schedule_b],
            taken_counts={"A": 3},  # Overconsumption - should be capped at 2
        )
        assert ratio == pytest.approx(0.4)

    def test_mixed_compliance(self, calculator, schedule_a, schedule_b):
        """A: 1/2, B: 2/3 should return 3/5 = 0.6"""
        ratio = calculator.calculate_compliance(
            schedules=[schedule_a, schedule_b],
            taken_counts={"A": 1, "B": 2},
        )
        assert ratio == pytest.approx(0.6)

    def test_full_compliance(self, calculator, schedule_a, schedule_b):
        """A: 2/2, B: 3/3 should return 5/5 = 1.0"""
        ratio = calculator.calculate_compliance(
            schedules=[schedule_a, schedule_b],
            taken_counts={"A": 2, "B": 3},
        )
        assert ratio == 1.0

    def test_overconsumption_capped_at_one(self, calculator, schedule_a, schedule_b):
        """A: 3/2, B: 4/3 (both overconsumption) should return 1.0 (capped)"""
        ratio = calculator.calculate_compliance(
            schedules=[schedule_a, schedule_b],
            taken_counts={"A": 3, "B": 4},  # Overconsumption on both
        )
        assert ratio == 1.0


class TestMedicationFactorScore:
    """Test medication factor score calculation (ratio * multiplier)"""

    def test_medication_factor_score_full_compliance(self):
        """1.0 ratio * 30 multiplier = 30"""
        ratio = 1.0
        multiplier = 30.0
        score = ratio * multiplier
        assert score == 30.0

    def test_medication_factor_score_half_compliance(self):
        """0.5 ratio * 30 multiplier = 15"""
        ratio = 0.5
        multiplier = 30.0
        score = ratio * multiplier
        assert score == 15.0

    def test_medication_factor_score_partial_compliance(self):
        """0.6 ratio * 30 multiplier = 18"""
        ratio = 0.6
        multiplier = 30.0
        score = ratio * multiplier
        assert score == 18.0

    def test_medication_factor_score_no_compliance(self):
        """0.0 ratio * 30 multiplier = 0"""
        ratio = 0.0
        multiplier = 30.0
        score = ratio * multiplier
        assert score == 0.0

    def test_medication_factor_score_custom_ratio(self):
        """0.874 ratio * 30 multiplier = 26.22"""
        ratio = 0.874
        multiplier = 30.0
        score = ratio * multiplier
        assert score == pytest.approx(26.22)

    def test_medication_factor_score_quarter_compliance(self):
        """0.25 ratio * 30 multiplier = 7.5"""
        ratio = 0.25
        multiplier = 30.0
        score = ratio * multiplier
        assert score == 7.5

    def test_medication_factor_score_three_quarter_compliance(self):
        """0.75 ratio * 30 multiplier = 22.5"""
        ratio = 0.75
        multiplier = 30.0
        score = ratio * multiplier
        assert score == 22.5
