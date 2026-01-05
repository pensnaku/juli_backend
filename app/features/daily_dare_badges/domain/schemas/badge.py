"""Pydantic schemas for daily dare badges"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class BadgeBase(BaseModel):
    """Base schema for badges"""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    type: str
    level: Optional[int] = None
    priority: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None
    image_earned: Optional[str] = None
    image_not_earned: Optional[str] = None


class BadgeResponse(BadgeBase):
    """Response schema for a badge"""
    pre_text: Optional[str] = None
    post_text: Optional[str] = None

    class Config:
        from_attributes = True


class UserBadgeResponse(BadgeBase):
    """Response schema for a user's earned badge"""
    earned_at: Optional[datetime] = None
    times_earned: int = 1

    class Config:
        from_attributes = True


class BadgeWithStatusResponse(BadgeBase):
    """Response schema for a badge with earned status"""
    is_earned: bool = False
    times_earned: int = 0

    class Config:
        from_attributes = True


class UserBadgesListResponse(BaseModel):
    """Response schema for list of user badges"""
    badges: List[UserBadgeResponse]


class DashboardOverviewResponse(BaseModel):
    """Response schema for badge dashboard overview"""
    last_earned_regular: Optional[UserBadgeResponse] = None
    last_earned_monthly: Optional[UserBadgeResponse] = None
    next_regular: Optional[BadgeResponse] = None
    next_monthly: Optional[BadgeResponse] = None


class AllBadgesResponse(BaseModel):
    """Response schema for all badges with status"""
    regular_badges: List[BadgeWithStatusResponse]
    monthly_badges: List[BadgeWithStatusResponse]
