"""API package - contains all API versions"""
from fastapi import APIRouter
from app.features.auth.api import router as auth_router
from app.shared.questionnaire.api import router as questionnaire_router
from app.features.dares.api import router as dares_router
from app.features.journal.api import router as journal_router
from app.features.tracking.api import router as tracking_router
from app.features.medication.api import router as medication_router

# Create main API router
api_router_v1 = APIRouter()

# Include feature routers
api_router_v1.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router_v1.include_router(questionnaire_router, prefix="/questionnaire", tags=["questionnaire"])
api_router_v1.include_router(dares_router, prefix="/dares", tags=["dares"])
api_router_v1.include_router(journal_router, prefix="/journal", tags=["journal"])
api_router_v1.include_router(tracking_router, prefix="/tracking-topics", tags=["tracking"])
api_router_v1.include_router(medication_router, prefix="/medications", tags=["medications"])

__all__ = ["api_router_v1"]