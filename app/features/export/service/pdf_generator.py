"""PDF generator using WeasyPrint and Jinja2"""
import base64
from pathlib import Path
from datetime import date, timedelta

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from jinja2 import Environment

from app.features.export.service.data_collector import HealthDataPayload
from app.features.export.constants import REPORT_DAYS


class PDFGenerator:
    """Generates PDF documents from health data"""

    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.fonts_dir = Path(__file__).parent.parent / "fonts"
        self.font_config = FontConfiguration()
        self._template_cache = self._load_template()

    def _load_template(self) -> str:
        """Load template from file"""
        template_path = self.template_dir / "health_data_history.html"
        with open(template_path) as f:
            return f.read()

    def _get_font_css(self) -> str:
        """Generate CSS for font faces"""
        book_font = self.fonts_dir / "ParaType-Futura_PT_Book.otf"
        medium_font = self.fonts_dir / "ParaType-Futura_PT_Medium.otf"
        return f"""
            @font-face {{
                font-family: 'Futura PT Book';
                src: url('file://{book_font}') format('opentype')
            }}
            @font-face {{
                font-family: 'Futura PT Medium';
                src: url('file://{medium_font}') format('opentype')
            }}
            @page {{ size: a4; margin: 0.5cm }}
        """

    def generate_health_data_pdf(
        self, payload: HealthDataPayload, chart_data: dict
    ) -> str:
        """
        Generate health data PDF and return base64-encoded content.

        Args:
            payload: HealthDataPayload with user and measurement data
            chart_data: Chart data from ChartBuilder

        Returns:
            Base64-encoded PDF content
        """
        # Prepare template context
        period = self.format_period(payload.start_date)
        timeline = [
            (payload.start_date + timedelta(days=n)).day
            for n in range(REPORT_DAYS)
        ]

        # Extract individual_tracking to pass separately to template
        individual_tracking = chart_data.pop("individual_tracking", {})

        # Render template using Environment().from_string() like printer service
        html_content = (
            Environment(autoescape=True)
            .from_string(self._template_cache)
            .render(
                name=payload.name,
                gender=payload.gender,
                condition=payload.condition,
                diagnosed=payload.diagnosed,
                period=period,
                timeline=timeline,
                score=chart_data,
                individual_tracking=individual_tracking,
            )
        )

        # Generate PDF with separate stylesheets (like printer service)
        pdf_bytes = HTML(string=html_content).write_pdf(
            stylesheets=[
                CSS(string=self._get_font_css(), font_config=self.font_config)
            ],
            font_config=self.font_config,
        )

        return base64.b64encode(pdf_bytes).decode("utf-8")

    def format_period(self, start_date: date) -> str:
        """
        Format the report period as a human-readable string.

        Examples:
            - Same month: "01 – 28 January, 2024"
            - Different months: "15 January – 12 February, 2024"
            - Different years: "15 December, 2023 – 12 January, 2024"

        Args:
            start_date: Report start date

        Returns:
            Formatted period string
        """
        end_date = start_date + timedelta(days=REPORT_DAYS - 1)

        if start_date.year == end_date.year:
            if start_date.month == end_date.month:
                return f"{start_date.day:02d} – {end_date.day:02d} {end_date.strftime('%B')}, {end_date.year}"
            else:
                return f"{start_date.day:02d} {start_date.strftime('%B')} – {end_date.day:02d} {end_date.strftime('%B')}, {end_date.year}"
        else:
            return f"{start_date.day:02d} {start_date.strftime('%B')}, {start_date.year} – {end_date.day:02d} {end_date.strftime('%B')}, {end_date.year}"
