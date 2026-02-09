"""API package - contains all API versions"""
from fastapi import APIRouter
from app.features.auth.api import router as auth_router
from app.shared.questionnaire.api import router as questionnaire_router
from app.features.dares.api import router as dares_router
from app.features.journal.api import router as journal_router
from app.features.tracking.api import router as tracking_router
from app.features.medication.api import router as medication_router
from app.features.observations.api import router as observations_router
from app.features.juli_score.api import router as juli_score_router
from app.features.environment.api import router as environment_router
from app.features.daily_dare_badges.api import router as badges_router
from app.features.export.api import router as export_router
from app.features.notifications.api import router as notifications_router
from app.features.notifications.api.admin_router import router as notifications_admin_router

# Create main API router
api_router_v1 = APIRouter()

# Include feature routers
api_router_v1.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router_v1.include_router(questionnaire_router, prefix="/questionnaire", tags=["questionnaire"])
api_router_v1.include_router(dares_router, prefix="/dares", tags=["dares"])
api_router_v1.include_router(journal_router, prefix="/journal", tags=["journal"])
api_router_v1.include_router(tracking_router, prefix="/tracking-topics", tags=["tracking"])
api_router_v1.include_router(medication_router, prefix="/medications", tags=["medications"])
api_router_v1.include_router(observations_router, prefix="/observations", tags=["observations"])
api_router_v1.include_router(juli_score_router, prefix="/juli-score", tags=["juli-score"])
api_router_v1.include_router(environment_router, prefix="/environment", tags=["environment"])
api_router_v1.include_router(badges_router, prefix="/badges", tags=["badges"])
api_router_v1.include_router(export_router, prefix="/export", tags=["export"])
api_router_v1.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router_v1.include_router(notifications_admin_router, prefix="/admin/notifications", tags=["admin"])

__all__ = ["api_router_v1"]