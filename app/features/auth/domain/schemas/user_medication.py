"""Pydantic schemas for user medications"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserMedicationBase(BaseModel):
    """Base schema for user medications"""
    medication_name: str = Field(..., description="Name of the medication")
    dosage: Optional[str] = Field(None, description="Dosage information")
    notes: Optional[str] = Field(None, description="Additional notes")


class UserMedicationCreate(UserMedicationBase):
    """Schema for creating a user medication"""
    pass


class UserMedicationUpdate(BaseModel):
    """Schema for updating a user medication (all fields optional)"""
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class UserMedicationResponse(UserMedicationBase):
    """Schema for user medication response"""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True