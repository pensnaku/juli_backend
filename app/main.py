import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging to show INFO level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.scheduler import start_scheduler, stop_scheduler
from app.api import api_router_v1
from app.universal_links import router as universal_links_router
from app.features.juli_score.scheduler import register_juli_score_job
from app.features.auth.scheduler import register_reminder_job
from app.features.notifications.service.notification_queue import start_notification_workers
from app.features.notifications.service import NotificationService
from app.features.notifications.scheduler.daily_push_scheduler import register_daily_push_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events"""
    # Startup
    register_juli_score_job()
    register_reminder_job()
    register_daily_push_job()
    start_scheduler()

    # Start notification queue workers
    db = SessionLocal()
    try:
        notification_service = NotificationService(db)
        await start_notification_workers(notification_service)
    finally:
        db.close()

    yield
    # Shutdown
    stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Juli Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Track when the app started (for deployment verification)
APP_START_TIME = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router_v1, prefix="/api/v1")

# Universal links (AASA + Android asset links) — no prefix, served at root
app.include_router(universal_links_router)


@app.get("/")
def root():
    return {
        "message": "Juli Backend API",
        "docs": "/docs",
        "version": settings.VERSION,
        "deployed_at": APP_START_TIME
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
