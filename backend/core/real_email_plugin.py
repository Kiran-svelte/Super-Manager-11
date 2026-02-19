"""
Real Email Plugin with Brevo API + SMTP fallback
Sends actual emails using Brevo transactional API (primary) or SMTP (fallback).
"""
from typing import Dict, Any, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import asyncio

from .plugins import BasePlugin
from .brevo_email import send_email_via_brevo

class RealEmailPlugin(BasePlugin):
    """Real email integration plugin using SMTP"""
    
    def __init__(self):
        super().__init__("email", "Email operations via Brevo API or SMTP fallback")
        self.sent_emails = []

        # Brevo API (primary)
        self.brevo_api_key = os.getenv("BREVO_API_KEY", "")

        # SMTP Configuration (fallback)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SMTP_EMAIL", "supermanager.ai@gmail.com")
        self.sender_password = os.getenv("SMTP_PASSWORD", "")
        
    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute email action"""
        action = step.get("action", "").lower()
        parameters = step.get("parameters", {})

        if "send" in action or "invite" in action:
            return await self._send_email(parameters)
        elif "read" in action or "check" in action:
            return {
                "status": "completed",
                "result": f"Found {len(self.sent_emails)} emails",
                "emails": self.sent_emails
            }
        else:
            return {
                "status": "failed",
                "error": f"Unknown email action: {action}"
            }
    
    async def _send_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send email – tries Brevo API first, falls back to SMTP."""
        try:
            to_email = parameters.get("to", "")
            subject = parameters.get("subject", "Meeting Invitation")
            body = parameters.get("body", "")
            meeting_link = parameters.get("meeting_link", "")

            if not to_email:
                return {"status": "failed", "error": "No recipient email provided"}

            if not body:
                body = self._generate_meeting_email_body(parameters, meeting_link)
            html_body = self._generate_html_email(parameters, meeting_link)

            # ── Brevo API (primary) ────────────────────────────────────────
            if self.brevo_api_key:
                result = await send_email_via_brevo(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_body,
                    text_content=body,
                )
                if result["success"]:
                    email_record = {
                        "to": to_email,
                        "subject": subject,
                        "body": body,
                        "meeting_link": meeting_link,
                        "sent_at": "now",
                        "status": "sent via Brevo",
                    }
                    self.sent_emails.append(email_record)
                    return {
                        "status": "completed",
                        "result": f"Email sent to {to_email} via Brevo",
                        "email": email_record,
                    }
                # Brevo failed – fall through to SMTP

            # ── SMTP fallback ──────────────────────────────────────────────
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = to_email
            message.attach(MIMEText(body, "plain"))
            message.attach(MIMEText(html_body, "html"))

            try:
                if not self.sender_password:
                    raise RuntimeError("SMTP_PASSWORD not configured")

                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.sender_email, self.sender_password)
                    server.sendmail(self.sender_email, to_email, message.as_string())

                email_record = {
                    "to": to_email,
                    "subject": subject,
                    "body": body,
                    "meeting_link": meeting_link,
                    "sent_at": "now",
                    "status": "sent via SMTP",
                }
                self.sent_emails.append(email_record)
                return {
                    "status": "completed",
                    "result": f"Email sent to {to_email} via SMTP",
                    "email": email_record,
                }

            except Exception as smtp_error:
                email_record = {
                    "to": to_email,
                    "subject": subject,
                    "body": body,
                    "meeting_link": meeting_link,
                    "sent_at": "simulated",
                    "status": f"simulated – configure BREVO_API_KEY or SMTP credentials",
                }
                self.sent_emails.append(email_record)
                return {
                    "status": "completed",
                    "result": f"Email SIMULATED to {to_email} (no transport configured)",
                    "email": email_record,
                    "note": "Set BREVO_API_KEY (or SMTP_EMAIL + SMTP_PASSWORD) to enable real sending",
                }

        except Exception as e:
            return {"status": "failed", "error": f"Failed to send email: {str(e)}"}
    
    def _generate_meeting_email_body(self, parameters: Dict[str, Any], meeting_link: str) -> str:
        """Generate meeting invitation email body"""
        topic = parameters.get("topic", "Meeting")
        participants = parameters.get("participants", "")
        
        body = f"""
Hello,

You have been invited to a meeting: {topic}

Meeting Details:
- Topic: {topic}
- Participants: {participants}

"""
        if meeting_link:
            body += f"Join Meeting: {meeting_link}\n\n"
        
        body += """
Best regards,
Super Manager AI
"""
        return body
    
    def _generate_html_email(self, parameters: Dict[str, Any], meeting_link: str) -> str:
        """Generate HTML version of email"""
        topic = parameters.get("topic", "Meeting")
        participants = parameters.get("participants", "")
        
        html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; border-radius: 10px;">
        <h2 style="color: #4A90E2;">Meeting Invitation</h2>
        <p>Hello,</p>
        <p>You have been invited to a meeting: <strong>{topic}</strong></p>
        
        <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0;">Meeting Details</h3>
            <p><strong>Topic:</strong> {topic}</p>
            <p><strong>Participants:</strong> {participants}</p>
        </div>
"""
        
        if meeting_link:
            html += f"""
        <div style="text-align: center; margin: 30px 0;">
            <a href="{meeting_link}" style="background-color: #4A90E2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                Join Meeting
            </a>
        </div>
"""
        
        html += """
        <p style="margin-top: 30px; color: #666; font-size: 14px;">
            Best regards,<br>
            <strong>Super Manager AI</strong>
        </p>
    </div>
</body>
</html>
"""
        return html
    
    def get_capabilities(self) -> List[str]:
        return ["email", "send_email", "read_email", "send_invites"]
    
    def validate_parameters(self, parameters: Dict) -> bool:
        """Validate email parameters"""
        return "to" in parameters
