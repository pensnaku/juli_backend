"""Pydantic schemas for dares feature"""
from app.features.dares.domain.schemas.dare import (
    DareBase,
    DareCreate,
    DareResponse,
)
from app.features.dares.domain.schemas.daily_dare_assignment import (
    DailyDareAssignmentBase,
    DailyDareAssignmentCreate,
    DareWithAssignment,
    DailySummary,
    DailyDaresResponse,
    UpdateDareCompletionRequest,
    UpdateDareCompletionResponse,
    CompleteDareResponse,
    DailyHistoryItem,
    DareHistoryResponse,
)

__all__ = [
    "DareBase",
    "DareCreate",
    "DareResponse",
    "DailyDareAssignmentBase",
    "DailyDareAssignmentCreate",
    "DareWithAssignment",
    "DailySummary",
    "DailyDaresResponse",
    "UpdateDareCompletionRequest",
    "UpdateDareCompletionResponse",
    "CompleteDareResponse",
    "DailyHistoryItem",
    "DareHistoryResponse",
]