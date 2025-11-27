"""Repository layer for dares feature"""
from app.features.dares.repository.dare_repository import DareRepository
from app.features.dares.repository.daily_dare_assignment_repository import DailyDareAssignmentRepository

__all__ = ["DareRepository", "DailyDareAssignmentRepository"]