from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import api_router_v1

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Juli Backend API",
    docs_url="/docs",
    redoc_url="/redoc"
)

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


@app.get("/")
def root():
    return {
        "message": "Welcome to Juli Backend API",
        "docs": "/docs",
        "version": settings.VERSION
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
