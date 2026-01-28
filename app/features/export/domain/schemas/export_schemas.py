"""Pydantic schemas for export feature"""
from typing import Literal, Optional
from datetime import date, timedelta
from pydantic import BaseModel, Field, model_validator

from app.features.export.service.chart_builder import REPORT_DAYS


class HealthDataExportRequest(BaseModel):
    """Request schema for health data PDF export"""

    start_date: Optional[date] = Field(
        default=None,
        description="Start date for the report period. Defaults to 28 days ago.",
    )
    format: Literal["pdf"] = Field(default="pdf", description="Export format (currently only PDF)")

    @model_validator(mode="after")
    def set_default_start_date(self):
        if self.start_date is None:
            self.start_date = date.today() - timedelta(days=REPORT_DAYS - 1)
        return self


class HealthDataExportResponse(BaseModel):
    """Response schema for health data PDF export"""

    status: str = Field(..., description="Status: 'OK' or 'ERROR'")
    content: str = Field(..., description="Base64-encoded PDF content")
    period: str = Field(..., description="Human-readable period string")
