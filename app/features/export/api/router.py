"""API router for export feature"""
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.api.dependencies import get_current_user
from app.features.auth.domain.entities import User
from app.features.export.service import ExportService
from app.features.export.domain.schemas import (
    HealthDataExportRequest,
    HealthDataExportResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/health-data/pdf", response_model=HealthDataExportResponse)
def export_health_data_pdf(
    request: HealthDataExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export health data as PDF.

    Generates a PDF report containing the user's health data for the specified
    period (default: 28 days from start_date).

    The response contains base64-encoded PDF content that can be decoded
    and saved as a PDF file.

    Returns:
        HealthDataExportResponse with status, base64 content, and period string
    """
    service = ExportService(db)
    try:
        return service.export_health_data_pdf(current_user.id, request.start_date)
    except ValueError as e:
        logger.error(f"Export validation error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e), "code": "validation_error"},
        )
    except Exception as e:
        logger.error(f"Export failed for user {current_user.id}: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to generate PDF export", "code": "export_failed"},
        )
