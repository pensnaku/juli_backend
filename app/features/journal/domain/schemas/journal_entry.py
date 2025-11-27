"""Pydantic schemas for journal entries"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class JournalEntryCreate(BaseModel):
    """Schema for creating a journal entry"""
    content: str = Field(..., min_length=1)


class JournalEntryUpdate(BaseModel):
    """Schema for updating a journal entry"""
    content: str = Field(..., min_length=1)


class JournalEntryResponse(BaseModel):
    """Schema for journal entry response"""
    id: int
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JournalEntryListResponse(BaseModel):
    """Schema for paginated journal entries list"""
    entries: List[JournalEntryResponse]
    total: int
    page: int
    page_size: int