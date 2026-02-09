"""Service layer for medication adherence business logic"""
from typing import List, Optional
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session

from app.features.auth.repository import UserMedicationRepository
from app.features.medication.repository import MedicationAdherenceRepository
from app.features.medication.domain.entities import AdherenceStatus
from app.features.medication.domain.schemas import (
    AdherenceStatusEnum,
    MedicationAdherenceResponse,
    DailyAdherenceResponse,
    AdherenceHistoryResponse,
    DailyAdherenceHistoryItem,
)


class MedicationAdherenceService:
    """Service for managing medication adherence"""

    def __init__(self, db: Session):
        self.db = db
        self.adherence_repo = MedicationAdherenceRepository(db)
        self.medication_repo = UserMedicationRepository(db)

    def _build_adherence_response(self, adherence, medication_name: str) -> MedicationAdherenceResponse:
        """Build adherence response with medication name"""
        # Handle both enum and string status values
        status_value = adherence.status.value if hasattr(adherence.status, 'value') else adherence.status
        return MedicationAdherenceResponse(
            id=adherence.id,
            user_id=adherence.user_id,
            medication_id=adherence.medication_id,
            medication_name=medication_name,
            date=adherence.date,
            status=AdherenceStatusEnum(status_value),
            notes=adherence.notes,
            created_at=adherence.created_at,
            updated_at=adherence.updated_at,
        )

    def _build_not_set_response(
        self,
        user_id: int,
        medication_id: int,
        medication_name: str,
        target_date: date,
        created_at: datetime,
    ) -> MedicationAdherenceResponse:
        """Build a NOT_SET response without persisting to database"""
        return MedicationAdherenceResponse(
            id=0,
            user_id=user_id,
            medication_id=medication_id,
            medication_name=medication_name,
            date=target_date,
            status=AdherenceStatusEnum.NOT_SET,
            notes=None,
            created_at=created_at,
            updated_at=None,
        )

    def _get_medication_created_date(self, medication) -> date:
        """Extract the date portion from medication created_at"""
        if medication.created_at:
            return medication.created_at.date()
        return date.min  # Fallback for medications without created_at

    def get_daily_adherence(self, user_id: int, target_date: date) -> DailyAdherenceResponse:
        """
        Get adherence status for all active medications for a specific date.
        Only returns medications that existed on or before the target date.
        Does NOT persist records - returns NOT_SET for medications without records.
        """
        # Get all active medications for the user
        medications = self.medication_repo.get_by_user_id(user_id, active_only=True)

        # Filter to only medications created on or before the target date
        medications = [
            med for med in medications
            if self._get_medication_created_date(med) <= target_date
        ]

        medication_map = {med.id: med for med in medications}

        # Get existing adherence records for the date
        existing_adherence = self.adherence_repo.get_by_user_and_date(user_id, target_date)
        existing_map = {a.medication_id: a for a in existing_adherence}

        adherence_list = []

        for med in medications:
            if med.id in existing_map:
                # Use existing adherence record
                adherence = existing_map[med.id]
                adherence_list.append(self._build_adherence_response(adherence, med.medication_name))
            else:
                # Return NOT_SET without persisting
                adherence_list.append(self._build_not_set_response(
                    user_id=user_id,
                    medication_id=med.id,
                    medication_name=med.medication_name,
                    target_date=target_date,
                    created_at=med.created_at,
                ))

        return DailyAdherenceResponse(
            date=target_date,
            medications=adherence_list,
        )

    def update_adherence(
        self,
        user_id: int,
        medication_id: int,
        target_date: date,
        status: AdherenceStatusEnum,
        notes: Optional[str] = None,
    ) -> Optional[MedicationAdherenceResponse]:
        """Update adherence status for a specific medication on a specific date"""
        # Verify medication belongs to user
        medication = self.medication_repo.get_by_id(medication_id)
        if not medication or medication.user_id != user_id:
            return None

        # Verify medication existed on the target date
        if self._get_medication_created_date(medication) > target_date:
            return None

        # Convert enum to AdherenceStatus
        db_status = AdherenceStatus(status.value)

        # Upsert the adherence record
        adherence = self.adherence_repo.upsert(
            user_id=user_id,
            medication_id=medication_id,
            target_date=target_date,
            status=db_status,
            notes=notes,
        )

        return self._build_adherence_response(adherence, medication.medication_name)

    def bulk_update_adherence(
        self,
        user_id: int,
        target_date: date,
        updates: List[dict],
    ) -> DailyAdherenceResponse:
        """Update adherence status for multiple medications at once"""
        for update in updates:
            medication_id = update["medication_id"]
            status = update["status"]
            notes = update.get("notes")

            self.update_adherence(
                user_id=user_id,
                medication_id=medication_id,
                target_date=target_date,
                status=status,
                notes=notes,
            )

        # Return the full daily adherence after updates
        return self.get_daily_adherence(user_id, target_date)

    def get_adherence_history(
        self,
        user_id: int,
        days: int = 7,
    ) -> AdherenceHistoryResponse:
        """Get adherence history for the past N days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Get all active medications
        medications = self.medication_repo.get_by_user_id(user_id, active_only=True)
        medication_map = {med.id: med for med in medications}

        # Get all adherence records in the date range
        adherence_records = self.adherence_repo.get_by_user_date_range(
            user_id, start_date, end_date
        )

        # Group by date
        adherence_by_date = {}
        for record in adherence_records:
            if record.date not in adherence_by_date:
                adherence_by_date[record.date] = []
            if record.medication_id in medication_map:
                med_name = medication_map[record.medication_id].medication_name
                adherence_by_date[record.date].append(
                    self._build_adherence_response(record, med_name)
                )

        # Build history for each day
        history = []
        current_date = end_date

        while current_date >= start_date:
            # Filter medications that existed on this date
            meds_for_date = [
                med for med in medications
                if self._get_medication_created_date(med) <= current_date
            ]

            if current_date in adherence_by_date:
                day_adherence = adherence_by_date[current_date]
                # Add NOT_SET for medications without records on this date
                recorded_med_ids = {a.medication_id for a in day_adherence}
                for med in meds_for_date:
                    if med.id not in recorded_med_ids:
                        day_adherence.append(self._build_not_set_response(
                            user_id=user_id,
                            medication_id=med.id,
                            medication_name=med.medication_name,
                            target_date=current_date,
                            created_at=med.created_at,
                        ))
            else:
                # No records for this day - create NOT_SET entries for eligible medications
                day_adherence = [
                    self._build_not_set_response(
                        user_id=user_id,
                        medication_id=med.id,
                        medication_name=med.medication_name,
                        target_date=current_date,
                        created_at=med.created_at,
                    )
                    for med in meds_for_date
                ]

            history.append(DailyAdherenceHistoryItem(
                date=current_date,
                medications=day_adherence,
            ))

            current_date -= timedelta(days=1)

        return AdherenceHistoryResponse(
            history=history,
        )
