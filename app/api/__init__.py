"""API package - contains all API versions"""
from fastapi import APIRouter
from app.features.auth.api import router as auth_router
from app.shared.questionnaire.api import router as questionnaire_router

# Create main API router
api_router_v1 = APIRouter()

# Include feature routers
api_router_v1.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router_v1.include_router(questionnaire_router, prefix="/questionnaire", tags=["questionnaire"])

__all__ = ["api_router_v1"]