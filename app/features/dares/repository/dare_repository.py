"""Repository for dares"""
import random
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.features.dares.domain.entities import Dare


class DareRepository:
    """Repository for managing dares"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, dare_id: int) -> Optional[Dare]:
        """Get a dare by ID"""
        return self.db.query(Dare).filter(Dare.id == dare_id).first()

    def get_all(self, active_only: bool = True) -> List[Dare]:
        """Get all dares"""
        query = self.db.query(Dare)
        if active_only:
            query = query.filter(Dare.is_active == True)
        return query.all()

    def get_by_category(self, category: str, active_only: bool = True) -> List[Dare]:
        """Get dares by category"""
        query = self.db.query(Dare).filter(Dare.category == category)
        if active_only:
            query = query.filter(Dare.is_active == True)
        return query.all()

    def get_random_for_user(
        self,
        category: str,
        exclude_ids: Set[int],
        user_condition_codes: List[str]
    ) -> Optional[Dare]:
        """
        Select a random dare from a category for a user.

        Rules:
        - Must match category
        - Must not be in exclude_ids (recently assigned)
        - If dare has a condition (SNOMED code), user must have that condition
        - If dare has no condition, any user can get it
        """
        # Build query
        query = (
            self.db.query(Dare)
            .filter(Dare.category == category)
            .filter(Dare.is_active == True)
        )

        # Exclude recently used dares
        if exclude_ids:
            query = query.filter(~Dare.id.in_(exclude_ids))

        # Filter by condition: show dares with no condition, OR dares matching user's conditions
        # Both dares.condition and user_condition_codes use SNOMED codes directly
        query = query.filter(
            or_(
                Dare.condition.is_(None),  # No condition required
                Dare.condition.in_(user_condition_codes) if user_condition_codes else False
            )
        )

        dares = query.all()

        if dares:
            return random.choice(dares)

        # Fallback: if no dares available (all recently used), allow repetition
        # but still respect condition filtering
        fallback_query = (
            self.db.query(Dare)
            .filter(Dare.category == category)
            .filter(Dare.is_active == True)
            .filter(
                or_(
                    Dare.condition.is_(None),
                    Dare.condition.in_(user_condition_codes) if user_condition_codes else False
                )
            )
        )
        fallback_dares = fallback_query.all()

        if fallback_dares:
            return random.choice(fallback_dares)

        return None

    def create(self, **kwargs) -> Dare:
        """Create a new dare"""
        dare = Dare(**kwargs)
        self.db.add(dare)
        self.db.flush()
        return dare

    def bulk_create(self, dares_data: List[dict]) -> List[Dare]:
        """Bulk create dares from list of dictionaries"""
        dares = [Dare(**data) for data in dares_data]
        self.db.add_all(dares)
        self.db.flush()
        return dares

    def count_by_category(self) -> dict:
        """Get count of dares per category"""
        from sqlalchemy import func
        results = (
            self.db.query(Dare.category, func.count(Dare.id))
            .filter(Dare.is_active == True)
            .group_by(Dare.category)
            .all()
        )
        return {category: count for category, count in results}