"""Pydantic schemas for medication adherence"""
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field


class AdherenceStatusEnum(str, Enum):
    """Possible states for medication adherence"""
    NOT_SET = "not_set"
    TAKEN = "taken"
    NOT_TAKEN = "not_taken"
    PARTLY_TAKEN = "partly_taken"


class MedicationAdherenceUpdate(BaseModel):
    """Schema for updating medication adherence status"""
    status: AdherenceStatusEnum = Field(..., description="Adherence status")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")


class MedicationAdherenceItem(BaseModel):
    """Single medication adherence item for bulk updates"""
    medication_id: int = Field(..., description="Medication ID")
    status: AdherenceStatusEnum = Field(..., description="Adherence status")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")


class BulkAdherenceUpdate(BaseModel):
    """Schema for updating multiple medication adherence records at once"""
    target_date: date = Field(..., description="Date for the adherence records")
    updates: List[MedicationAdherenceItem] = Field(..., description="List of medication adherence updates")


class MedicationAdherenceResponse(BaseModel):
    """Response schema for medication adherence"""
    id: int
    user_id: int
    medication_id: int
    medication_name: str
    date: date
    status: AdherenceStatusEnum
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DailyAdherenceResponse(BaseModel):
    """Response schema for daily adherence (all medications for a day)"""
    date: date
    medications: List[MedicationAdherenceResponse]


class DailyAdherenceHistoryItem(BaseModel):
    """Single day in adherence history"""
    date: date
    medications: List[MedicationAdherenceResponse]


class AdherenceHistoryResponse(BaseModel):
    """Response schema for adherence history"""
    history: List[DailyAdherenceHistoryItem]
