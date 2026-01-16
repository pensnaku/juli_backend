"""Repository for medication adherence database operations"""
from typing import Optional, List, Dict
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.features.medication.domain.entities import MedicationAdherence, AdherenceStatus


class MedicationAdherenceRepository:
    """Handles all database operations for medication adherence"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, adherence_id: int) -> Optional[MedicationAdherence]:
        """Get adherence record by ID"""
        return self.db.query(MedicationAdherence).filter(
            MedicationAdherence.id == adherence_id
        ).first()

    def get_by_user_medication_date(
        self,
        user_id: int,
        medication_id: int,
        target_date: date
    ) -> Optional[MedicationAdherence]:
        """Get adherence record for specific user, medication, and date"""
        return self.db.query(MedicationAdherence).filter(
            and_(
                MedicationAdherence.user_id == user_id,
                MedicationAdherence.medication_id == medication_id,
                MedicationAdherence.date == target_date
            )
        ).first()

    def get_by_user_and_date(
        self,
        user_id: int,
        target_date: date
    ) -> List[MedicationAdherence]:
        """Get all adherence records for a user on a specific date"""
        return self.db.query(MedicationAdherence).filter(
            and_(
                MedicationAdherence.user_id == user_id,
                MedicationAdherence.date == target_date
            )
        ).all()

    def get_daily_adherence_map(
        self,
        user_id: int,
        target_date: date
    ) -> Dict[int, MedicationAdherence]:
        """
        Get all adherence records for a user on a specific date.
        Returns dict mapping medication_id -> adherence record.
        """
        records = self.get_by_user_and_date(user_id, target_date)
        return {r.medication_id: r for r in records}

    def get_by_user_date_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[MedicationAdherence]:
        """Get all adherence records for a user within a date range"""
        return self.db.query(MedicationAdherence).filter(
            and_(
                MedicationAdherence.user_id == user_id,
                MedicationAdherence.date >= start_date,
                MedicationAdherence.date <= end_date
            )
        ).order_by(MedicationAdherence.date.desc()).all()

    def create(
        self,
        user_id: int,
        medication_id: int,
        target_date: date,
        status: AdherenceStatus = AdherenceStatus.NOT_SET,
        notes: Optional[str] = None
    ) -> MedicationAdherence:
        """Create a new adherence record"""
        adherence = MedicationAdherence(
            user_id=user_id,
            medication_id=medication_id,
            date=target_date,
            status=status,
            notes=notes
        )
        self.db.add(adherence)
        self.db.commit()
        self.db.refresh(adherence)
        return adherence

    def upsert(
        self,
        user_id: int,
        medication_id: int,
        target_date: date,
        status: AdherenceStatus,
        notes: Optional[str] = None
    ) -> MedicationAdherence:
        """Create or update an adherence record"""
        existing = self.get_by_user_medication_date(user_id, medication_id, target_date)

        if existing:
            existing.status = status
            if notes is not None:
                existing.notes = notes
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            return self.create(user_id, medication_id, target_date, status, notes)

    def update(
        self,
        adherence: MedicationAdherence,
        status: AdherenceStatus,
        notes: Optional[str] = None
    ) -> MedicationAdherence:
        """Update an existing adherence record"""
        adherence.status = status
        if notes is not None:
            adherence.notes = notes
        self.db.commit()
        self.db.refresh(adherence)
        return adherence

    def delete(self, adherence: MedicationAdherence) -> None:
        """Delete an adherence record"""
        self.db.delete(adherence)
        self.db.commit()

    def get_by_medication_date_range(
        self,
        medication_id: int,
        start_date: date,
        end_date: date
    ) -> List[MedicationAdherence]:
        """Get adherence records for a specific medication within a date range"""
        return self.db.query(MedicationAdherence).filter(
            and_(
                MedicationAdherence.medication_id == medication_id,
                MedicationAdherence.date >= start_date,
                MedicationAdherence.date <= end_date
            )
        ).order_by(MedicationAdherence.date.desc()).all()
