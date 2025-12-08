"""API router for journal feature"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.domain.entities import User
from app.features.journal.service import JournalService
from app.features.journal.domain.schemas import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryResponse,
    JournalEntryListResponse,
)


router = APIRouter()


@router.post("", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
def create_journal_entry(
    request: JournalEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new journal entry"""
    service = JournalService(db)
    return service.create_entry(current_user.id, request.content)


@router.get("", response_model=JournalEntryListResponse)
def list_journal_entries(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    start_date: Optional[date] = Query(default=None, description="Filter entries from this date (inclusive)"),
    end_date: Optional[date] = Query(default=None, description="Filter entries until this date (inclusive)"),
    search: Optional[str] = Query(default=None, description="Full-text search query"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get paginated list of journal entries, optionally filtered by date range and search"""
    service = JournalService(db)
    return service.list_entries(current_user.id, page, page_size, start_date, end_date, search)


@router.get("/{entry_id}", response_model=JournalEntryResponse)
def get_journal_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific journal entry"""
    service = JournalService(db)

    try:
        return service.get_entry(current_user.id, entry_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/{entry_id}", response_model=JournalEntryResponse)
def update_journal_entry(
    entry_id: int,
    request: JournalEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a journal entry"""
    service = JournalService(db)

    try:
        return service.update_entry(current_user.id, entry_id, request.content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_journal_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a journal entry"""
    service = JournalService(db)

    try:
        service.delete_entry(current_user.id, entry_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )