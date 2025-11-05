"""API package - contains all API versions"""
from fastapi import APIRouter
from app.features.auth.api import router as auth_router

# Create main API router
api_router_v1 = APIRouter()

# Include feature routers
api_router_v1.include_router(auth_router, prefix="/auth", tags=["authentication"])

__all__ = ["api_router_v1"]