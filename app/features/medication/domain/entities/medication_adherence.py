"""MedicationAdherence entity - tracks daily medication adherence status"""
import enum
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AdherenceStatus(str, enum.Enum):
    """Possible states for medication adherence"""
    NOT_SET = "not_set"
    TAKEN = "taken"
    NOT_TAKEN = "not_taken"
    PARTLY_TAKEN = "partly_taken"


# Create PostgreSQL ENUM that uses the string values
adherence_status_enum = PgEnum(
    'not_set', 'taken', 'not_taken', 'partly_taken',
    name='adherencestatus',
    create_type=False
)


class MedicationAdherence(Base):
    """Tracks daily medication adherence for each user medication"""
    __tablename__ = "medication_adherence"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    medication_id = Column(Integer, ForeignKey("user_medications.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(
        adherence_status_enum,
        nullable=False,
        default='not_set'
    )
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    medication = relationship("UserMedication")

    # Ensure one record per medication per day
    __table_args__ = (
        UniqueConstraint('user_id', 'medication_id', 'date', name='uq_user_medication_date'),
    )

    def __repr__(self):
        return f"<MedicationAdherence(user_id={self.user_id}, medication_id={self.medication_id}, date={self.date}, status={self.status})>"
