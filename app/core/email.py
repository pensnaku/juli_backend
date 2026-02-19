"""Postmark email service for sending template-based transactional emails"""
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

POSTMARK_TEMPLATE_URL = "https://api.postmarkapp.com/email/withTemplate"


def send_template_email(to: str, template_alias: str, template_model: dict) -> bool:
    """
    Send a template email via Postmark.

    Falls back to console logging if POSTMARK_API_TOKEN is not configured.

    Args:
        to: Recipient email address
        template_alias: Postmark template alias (e.g., 'welcome-to-juli')
        template_model: Template variables dict

    Returns:
        True if sent successfully, False otherwise
    """
    if not settings.POSTMARK_API_TOKEN:
        logger.info(
            f"[Email Dev Mode] To: {to}, Template: {template_alias}, "
            f"Model: {template_model}"
        )
        return True

    try:
        response = httpx.post(
            POSTMARK_TEMPLATE_URL,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Postmark-Server-Token": settings.POSTMARK_API_TOKEN,
            },
            json={
                "From": settings.POSTMARK_EMAIL_FROM,
                "To": to,
                "TemplateAlias": template_alias,
                "TemplateModel": template_model,
            },
        )

        if response.status_code == 200:
            logger.info(f"Email sent to {to} using template '{template_alias}'")
            return True

        logger.error(
            f"Postmark error sending to {to}: "
            f"status={response.status_code}, body={response.text}"
        )
        return False

    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False
