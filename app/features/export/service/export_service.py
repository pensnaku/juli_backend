"""Main export service that orchestrates PDF generation"""
from datetime import date
from sqlalchemy.orm import Session

from app.features.export.domain.schemas import HealthDataExportResponse
from app.features.export.service.data_collector import DataCollector
from app.features.export.service.chart_builder import ChartBuilder, REPORT_DAYS
from app.features.export.service.pdf_generator import PDFGenerator


class ExportService:
    """Service for exporting health data as PDF"""

    def __init__(self, db: Session):
        self.db = db
        self.data_collector = DataCollector(db)
        self.chart_builder = ChartBuilder()
        self.pdf_generator = PDFGenerator()

    def export_health_data_pdf(
        self, user_id: int, start_date: date
    ) -> HealthDataExportResponse:
        """
        Generate a health data PDF export for the configured report period.

        The report period is defined by REPORT_DAYS constant (default: 28 days).

        Args:
            user_id: The user's ID
            start_date: Start date for the report period

        Returns:
            HealthDataExportResponse with base64-encoded PDF content
        """
        # 1. Collect all health data for the report period
        payload = self.data_collector.collect_health_data(user_id, start_date)

        # 2. Build chart data from measurements
        chart_data = self.chart_builder.prepare_chart_content(
            start_date=payload.start_date,
            phq8=payload.phq8,
            mood=payload.mood,
            medication_schedule=payload.medication,
            steps_count=payload.steps_count,
            active_energy_burned=payload.active_energy_burned,
            workout_duration=payload.workout_duration,
            time_asleep=payload.time_asleep,
            time_in_bed=payload.time_in_bed,
            heart_rate_variability=payload.heart_rate_variability,
            weight=payload.weight,
            air_quality=payload.air_quality,
            pollen=payload.pollen,
            weather=payload.weather,
            individual_tracking=payload.individual_tracking,
        )

        # 3. Generate PDF
        pdf_content = self.pdf_generator.generate_health_data_pdf(payload, chart_data)

        return HealthDataExportResponse(
            status="OK",
            content=pdf_content,
            period=self.pdf_generator.format_period(start_date),
        )
