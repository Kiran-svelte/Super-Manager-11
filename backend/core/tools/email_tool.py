"""
Email Tool - Gmail SMTP
========================
Send emails using Gmail SMTP with app password.
Requires user confirmation before sending.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .base import Tool, ToolResult


class SendEmailTool(Tool):
    name = "send_email"
    description = "Send an email to a recipient"
    parameters = {
        "to": {"description": "Recipient email address", "required": True, "type": "string"},
        "subject": {"description": "Email subject line", "required": True, "type": "string"},
        "body": {"description": "Email body content (supports HTML)", "required": True, "type": "string"},
    }
    requires_confirmation = True

    async def execute(self, **params) -> ToolResult:
        to = params.get("to", "")
        subject = params.get("subject", "")
        body = params.get("body", "")

        if not to or not subject or not body:
            missing = [k for k in ["to", "subject", "body"] if not params.get(k)]
            return ToolResult(
                success=False,
                output=f"Missing required fields: {', '.join(missing)}",
                error="missing_fields",
            )

        # Try identity email first, then SMTP config
        sent = False
        provider = ""

        # Try configured SMTP
        smtp_email = os.getenv("SMTP_EMAIL", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        if smtp_email and smtp_password:
            try:
                msg = MIMEMultipart("alternative")
                msg["From"] = smtp_email
                msg["To"] = to
                msg["Subject"] = subject

                # Detect HTML
                if "<" in body and ">" in body:
                    msg.attach(MIMEText(body, "html"))
                else:
                    msg.attach(MIMEText(body, "plain"))

                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_email, smtp_password)
                    server.send_message(msg)

                sent = True
                provider = "Gmail SMTP"
            except Exception as e:
                return ToolResult(
                    success=False,
                    output=f"Failed to send email: {str(e)}",
                    error=str(e),
                )

        if not sent:
            return ToolResult(
                success=False,
                output="Email not configured. Set SMTP_EMAIL and SMTP_PASSWORD environment variables, or configure an AI email identity in Settings.",
                error="not_configured",
            )

        return ToolResult(
            success=True,
            output=f"Email sent successfully to {to} with subject '{subject}' via {provider}.",
            data={
                "to": to,
                "subject": subject,
                "provider": provider,
            },
        )
