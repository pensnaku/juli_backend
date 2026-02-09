"""Push subscription request/response schemas"""
from typing import Literal
from pydantic import BaseModel


class SubscriptionRequest(BaseModel):
    """Request schema for registering a device for push notifications"""
    device_token: str
    device_type: Literal["ios", "android"]


class SubscriptionResponse(BaseModel):
    """Response schema for subscription operations"""
    status: str
