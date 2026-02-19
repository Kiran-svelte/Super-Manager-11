"""
Brevo (SendinBlue) Transactional Email Integration
Sends emails via the Brevo API v3.
"""
from typing import Optional
import os
import httpx
import logging

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


async def send_email_via_brevo(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = "",
    sender_name: str = "Super Manager",
    sender_email: Optional[str] = None,
) -> dict:
    """
    Send a transactional email using the Brevo API.

    Returns a dict with 'success' bool and 'message' string.
    """
    api_key = os.getenv("BREVO_API_KEY", "")
    if not api_key:
        return {"success": False, "message": "BREVO_API_KEY not configured"}

    from_email = sender_email or os.getenv("BREVO_SENDER_EMAIL", "noreply@supermanager.ai")

    payload = {
        "sender": {"name": sender_name, "email": from_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }
    if text_content:
        payload["textContent"] = text_content

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(BREVO_API_URL, json=payload, headers=headers)

        if response.status_code in (200, 201):
            data = response.json()
            msg_id = data.get("messageId", "")
            logger.info("[BREVO] Email sent to %s, messageId=%s", to_email, msg_id)
            return {"success": True, "message": f"Email sent via Brevo (messageId={msg_id})"}

        logger.error("[BREVO] API error %s: %s", response.status_code, response.text)
        return {
            "success": False,
            "message": f"Brevo API error {response.status_code}: {response.text}",
        }

    except Exception as exc:
        logger.error("[BREVO] Exception sending email: %s", exc)
        return {"success": False, "message": f"Brevo send failed: {exc}"}
