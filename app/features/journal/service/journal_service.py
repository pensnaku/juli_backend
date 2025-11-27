"""Service layer for journal business logic"""
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session

from app.features.journal.repository import JournalEntryRepository
from app.features.journal.domain.schemas import (
    JournalEntryResponse,
    JournalEntryListResponse,
)


class JournalService:
    """Service for managing journal entries"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = JournalEntryRepository(db)

    def create_entry(self, user_id: int, content: str) -> JournalEntryResponse:
        """Create a new journal entry"""
        entry = self.repo.create(user_id, content)
        self.db.commit()
        return JournalEntryResponse.model_validate(entry)

    def get_entry(self, user_id: int, entry_id: int) -> JournalEntryResponse:
        """Get a specific journal entry"""
        entry = self.repo.get_by_id(entry_id)

        if not entry:
            raise ValueError("Journal entry not found")

        if entry.user_id != user_id:
            raise ValueError("This journal entry does not belong to you")

        return JournalEntryResponse.model_validate(entry)

    def list_entries(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> JournalEntryListResponse:
        """Get paginated list of journal entries for a user"""
        entries, total = self.repo.get_by_user_paginated(
            user_id, page, page_size, start_date, end_date
        )

        return JournalEntryListResponse(
            entries=[JournalEntryResponse.model_validate(e) for e in entries],
            total=total,
            page=page,
            page_size=page_size,
        )

    def update_entry(
        self, user_id: int, entry_id: int, content: str
    ) -> JournalEntryResponse:
        """Update a journal entry"""
        entry = self.repo.get_by_id(entry_id)

        if not entry:
            raise ValueError("Journal entry not found")

        if entry.user_id != user_id:
            raise ValueError("This journal entry does not belong to you")

        updated_entry = self.repo.update(entry, content)
        self.db.commit()
        return JournalEntryResponse.model_validate(updated_entry)

    def delete_entry(self, user_id: int, entry_id: int) -> None:
        """Delete a journal entry"""
        entry = self.repo.get_by_id(entry_id)

        if not entry:
            raise ValueError("Journal entry not found")

        if entry.user_id != user_id:
            raise ValueError("This journal entry does not belong to you")

        self.repo.delete(entry)
        self.db.commit()