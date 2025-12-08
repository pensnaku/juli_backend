"""Repository for journal entries"""
from typing import List, Optional, Tuple
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.features.journal.domain.entities import JournalEntry


class JournalEntryRepository:
    """Repository for managing journal entries"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, content: str) -> JournalEntry:
        """Create a new journal entry"""
        entry = JournalEntry(user_id=user_id, content=content)
        self.db.add(entry)
        self.db.flush()
        return entry

    def get_by_id(self, entry_id: int) -> Optional[JournalEntry]:
        """Get a journal entry by ID"""
        return (
            self.db.query(JournalEntry)
            .filter(JournalEntry.id == entry_id)
            .first()
        )

    def get_by_user_paginated(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[JournalEntry], int]:
        """Get paginated journal entries for a user, newest first"""
        query = (
            self.db.query(JournalEntry)
            .filter(JournalEntry.user_id == user_id)
        )

        # Only filter by start_date if provided
        if start_date:
            query = query.filter(func.date(JournalEntry.created_at) >= start_date)

        # Default end_date to today if not provided
        effective_end_date = end_date if end_date else date.today()
        query = query.filter(func.date(JournalEntry.created_at) <= effective_end_date)

        if search:
            # Full-text search using PostgreSQL ts_vector
            search_filter = func.to_tsvector('english', JournalEntry.content).match(search)
            query = query.filter(search_filter)

        query = query.order_by(JournalEntry.created_at.desc())

        total = query.count()
        offset = (page - 1) * page_size
        entries = query.offset(offset).limit(page_size).all()

        return entries, total

    def update(self, entry: JournalEntry, content: str) -> JournalEntry:
        """Update a journal entry"""
        entry.content = content
        self.db.flush()
        return entry

    def delete(self, entry: JournalEntry) -> None:
        """Delete a journal entry"""
        self.db.delete(entry)
        self.db.flush()