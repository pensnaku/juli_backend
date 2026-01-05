"""Pydantic schemas for daily dare assignments"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field


class DailyDareAssignmentBase(BaseModel):
    """Base schema for daily dare assignments"""
    dare_id: int
    assigned_date: date


class DailyDareAssignmentCreate(DailyDareAssignmentBase):
    """Schema for creating a daily dare assignment"""
    user_id: int


class DareWithAssignment(BaseModel):
    """Schema for a dare with its assignment info (used in responses)"""
    assignment_id: int
    dare_id: int
    text: str
    category: str
    subcategory: Optional[str] = None
    points: int
    is_completed: bool
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DailySummary(BaseModel):
    """Summary of daily dares progress"""
    total_points_possible: int
    points_earned: int
    completed_count: int


class DailyDaresResponse(BaseModel):
    """Response schema for daily dares endpoint"""
    date: date
    dares: List[DareWithAssignment]
    summary: DailySummary
    seven_day_total_points: int


class UpdateDareCompletionRequest(BaseModel):
    """Request schema for updating dare completion status"""
    completed: bool = Field(..., description="Set to true to complete, false to uncomplete")


class UpdateDareCompletionResponse(BaseModel):
    """Response schema for updating dare completion status"""
    success: bool
    assignment_id: int
    is_completed: bool
    points_earned: int
    completed_at: Optional[datetime] = None
    badges_earned: Optional[List[str]] = None  # List of badge slugs earned


class CompleteDareResponse(UpdateDareCompletionResponse):
    """Response schema for completing a dare (alias for UpdateDareCompletionResponse)"""
    pass


class DailyHistoryItem(BaseModel):
    """Single day's dares in history"""
    date: date
    dares: List[DareWithAssignment]
    completed_count: int
    points_earned: int


class DareHistoryResponse(BaseModel):
    """Response schema for dare history endpoint"""
    history: List[DailyHistoryItem]
    total_points: int
    total_completed: int