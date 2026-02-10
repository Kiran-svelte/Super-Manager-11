"""
Real Email and Calendar Integrations
Provides actual email sending, calendar management, and meeting scheduling
with proper authentication and verification.
"""

import asyncio
import json
import os
import base64
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)


class EmailProvider(Enum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"


class CalendarProvider(Enum):
    GOOGLE = "google"
    OUTLOOK = "outlook"
    APPLE = "apple"


class MeetingPlatform(Enum):
    GOOGLE_MEET = "google_meet"
    ZOOM = "zoom"
    TEAMS = "microsoft_teams"
    WEBEX = "webex"
    IN_PERSON = "in_person"


class EmailStatus(Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"


@dataclass
class EmailAttachment:
    """Email attachment"""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass
class EmailMessage:
    """Email message structure"""
    id: str
    to: List[str]
    subject: str
    body_text: str
    body_html: Optional[str] = None
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    attachments: List[EmailAttachment] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    status: EmailStatus = EmailStatus.DRAFT
    tracking_id: str = field(default_factory=lambda: secrets.token_hex(16))
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    provider_message_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "to": self.to,
            "cc": self.cc,
            "subject": self.subject,
            "body_preview": self.body_text[:200] + "..." if len(self.body_text) > 200 else self.body_text,
            "status": self.status.value,
            "tracking_id": self.tracking_id,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "has_attachments": len(self.attachments) > 0
        }


@dataclass
class CalendarEvent:
    """Calendar event structure"""
    id: str
    title: str
    description: str = ""
    start_time: datetime = None
    end_time: datetime = None
    location: Optional[str] = None
    attendees: List[Dict] = field(default_factory=list)  # {email, name, response_status}
    organizer: Optional[Dict] = None
    meeting_link: Optional[str] = None
    meeting_platform: Optional[MeetingPlatform] = None
    is_all_day: bool = False
    reminders: List[Dict] = field(default_factory=list)  # {minutes_before, method}
    recurrence: Optional[str] = None  # RRULE string
    status: str = "confirmed"  # confirmed, tentative, cancelled
    visibility: str = "default"  # default, public, private
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    provider_event_id: Optional[str] = None
    calendar_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "location": self.location,
            "attendees": self.attendees,
            "organizer": self.organizer,
            "meeting_link": self.meeting_link,
            "meeting_platform": self.meeting_platform.value if self.meeting_platform else None,
            "status": self.status,
            "provider_event_id": self.provider_event_id
        }


class GoogleOAuthClient:
    """Google OAuth 2.0 client for Gmail and Calendar"""
    
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events"
        ]
    
    def get_auth_url(self, state: str = None) -> str:
        """Get OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        if state:
            params["state"] = state
        
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
    
    async def exchange_code(self, code: str) -> Dict:
        """Exchange authorization code for tokens"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code"
                }
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    logger.error(f"OAuth token exchange failed: {error}")
                    return {"error": error}
    
    async def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh access token"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    logger.error(f"Token refresh failed: {error}")
                    return {"error": error}


class GmailService:
    """Gmail API integration for sending emails"""
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.getenv("GMAIL_ACCESS_TOKEN")
        self.base_url = "https://gmail.googleapis.com/gmail/v1"
    
    async def send_email(self, message: EmailMessage) -> Dict:
        """Send email via Gmail API"""
        
        if not self.access_token:
            return {
                "success": False,
                "error": "Gmail not authenticated. Please connect your Google account.",
                "auth_required": True,
                "auth_url": GoogleOAuthClient().get_auth_url()
            }
        
        # Create MIME message
        mime_message = MIMEMultipart("alternative")
        mime_message["To"] = ", ".join(message.to)
        mime_message["Subject"] = message.subject
        
        if message.from_email:
            mime_message["From"] = f"{message.from_name} <{message.from_email}>" if message.from_name else message.from_email
        
        if message.cc:
            mime_message["Cc"] = ", ".join(message.cc)
        
        if message.reply_to:
            mime_message["Reply-To"] = message.reply_to
        
        # Add body
        mime_message.attach(MIMEText(message.body_text, "plain"))
        if message.body_html:
            mime_message.attach(MIMEText(message.body_html, "html"))
        
        # Add attachments
        for attachment in message.attachments:
            part = MIMEBase(*attachment.content_type.split("/"))
            part.set_payload(attachment.content)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={attachment.filename}"
            )
            mime_message.attach(part)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("utf-8")
        
        # Send via Gmail API
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with session.post(
                f"{self.base_url}/users/me/messages/send",
                headers=headers,
                json={"raw": raw_message}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    message.status = EmailStatus.SENT
                    message.sent_at = datetime.now()
                    message.provider_message_id = data.get("id")
                    
                    return {
                        "success": True,
                        "message_id": data.get("id"),
                        "thread_id": data.get("threadId"),
                        "tracking_id": message.tracking_id,
                        "sent_at": message.sent_at.isoformat()
                    }
                else:
                    error_data = await response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    
                    # Check if token expired
                    if response.status == 401:
                        return {
                            "success": False,
                            "error": "Authentication expired. Please reconnect your Google account.",
                            "auth_required": True
                        }
                    
                    message.status = EmailStatus.FAILED
                    return {
                        "success": False,
                        "error": error_msg
                    }
    
    async def get_messages(self, query: str = None, max_results: int = 10) -> Dict:
        """Get email messages"""
        
        if not self.access_token:
            return {"success": False, "error": "Not authenticated", "auth_required": True}
        
        params = {"maxResults": max_results}
        if query:
            params["q"] = query
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with session.get(
                f"{self.base_url}/users/me/messages",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    return {"success": True, "data": await response.json()}
                else:
                    return {"success": False, "error": "Failed to fetch messages"}


class GoogleCalendarService:
    """Google Calendar API integration"""
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.getenv("GOOGLE_CALENDAR_ACCESS_TOKEN")
        self.base_url = "https://www.googleapis.com/calendar/v3"
    
    async def create_event(self, event: CalendarEvent) -> Dict:
        """Create calendar event"""
        
        if not self.access_token:
            return {
                "success": False,
                "error": "Google Calendar not authenticated",
                "auth_required": True,
                "auth_url": GoogleOAuthClient().get_auth_url()
            }
        
        # Build event payload
        event_body = {
            "summary": event.title,
            "description": event.description,
            "start": {
                "dateTime": event.start_time.isoformat(),
                "timeZone": "Asia/Kolkata"
            },
            "end": {
                "dateTime": event.end_time.isoformat(),
                "timeZone": "Asia/Kolkata"
            },
            "attendees": [{"email": a.get("email")} for a in event.attendees],
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "email", "minutes": 30}, {"method": "popup", "minutes": 10}]
            }
        }
        
        if event.location:
            event_body["location"] = event.location
        
        # Add conference (Google Meet) if requested
        if event.meeting_platform == MeetingPlatform.GOOGLE_MEET:
            event_body["conferenceData"] = {
                "createRequest": {
                    "requestId": secrets.token_hex(8),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            }
        
        calendar_id = event.calendar_id or "primary"
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {"conferenceDataVersion": 1} if event.meeting_platform == MeetingPlatform.GOOGLE_MEET else {}
            
            async with session.post(
                f"{self.base_url}/calendars/{calendar_id}/events",
                headers=headers,
                params=params,
                json=event_body
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    event.provider_event_id = data.get("id")
                    
                    # Extract meeting link if created
                    meeting_link = None
                    if "conferenceData" in data:
                        entry_points = data["conferenceData"].get("entryPoints", [])
                        for ep in entry_points:
                            if ep.get("entryPointType") == "video":
                                meeting_link = ep.get("uri")
                                break
                    
                    event.meeting_link = meeting_link
                    
                    return {
                        "success": True,
                        "event_id": data.get("id"),
                        "html_link": data.get("htmlLink"),
                        "meeting_link": meeting_link,
                        "status": data.get("status"),
                        "attendees_notified": True
                    }
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "error": error_data.get("error", {}).get("message", "Failed to create event")
                    }
    
    async def get_events(
        self,
        time_min: datetime = None,
        time_max: datetime = None,
        max_results: int = 10
    ) -> Dict:
        """Get calendar events"""
        
        if not self.access_token:
            return {"success": False, "error": "Not authenticated", "auth_required": True}
        
        params = {
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        
        if time_min:
            params["timeMin"] = time_min.isoformat() + "Z"
        if time_max:
            params["timeMax"] = time_max.isoformat() + "Z"
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with session.get(
                f"{self.base_url}/calendars/primary/events",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "events": data.get("items", [])}
                else:
                    return {"success": False, "error": "Failed to fetch events"}
    
    async def update_event(self, event_id: str, updates: Dict) -> Dict:
        """Update calendar event"""
        
        if not self.access_token:
            return {"success": False, "error": "Not authenticated"}
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with session.patch(
                f"{self.base_url}/calendars/primary/events/{event_id}",
                headers=headers,
                json=updates
            ) as response:
                if response.status == 200:
                    return {"success": True, "event": await response.json()}
                else:
                    return {"success": False, "error": "Failed to update event"}
    
    async def delete_event(self, event_id: str) -> Dict:
        """Delete calendar event"""
        
        if not self.access_token:
            return {"success": False, "error": "Not authenticated"}
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with session.delete(
                f"{self.base_url}/calendars/primary/events/{event_id}",
                headers=headers
            ) as response:
                if response.status == 204:
                    return {"success": True}
                else:
                    return {"success": False, "error": "Failed to delete event"}


class ZoomService:
    """Zoom API integration for meetings"""
    
    def __init__(self):
        self.account_id = os.getenv("ZOOM_ACCOUNT_ID")
        self.client_id = os.getenv("ZOOM_CLIENT_ID")
        self.client_secret = os.getenv("ZOOM_CLIENT_SECRET")
        self.base_url = "https://api.zoom.us/v2"
        self._access_token = None
        self._token_expires_at = None
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token"""
        
        if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._access_token
        
        if not all([self.account_id, self.client_id, self.client_secret]):
            return None
        
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://zoom.us/oauth/token",
                headers={"Authorization": f"Basic {auth}"},
                data={
                    "grant_type": "account_credentials",
                    "account_id": self.account_id
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self._access_token = data.get("access_token")
                    self._token_expires_at = datetime.now() + timedelta(seconds=data.get("expires_in", 3600) - 60)
                    return self._access_token
                else:
                    logger.error(f"Zoom auth failed: {await response.text()}")
                    return None
    
    async def create_meeting(
        self,
        topic: str,
        start_time: datetime,
        duration_minutes: int = 60,
        agenda: str = "",
        attendees: List[str] = None
    ) -> Dict:
        """Create Zoom meeting"""
        
        access_token = await self._get_access_token()
        if not access_token:
            return {
                "success": False,
                "error": "Zoom not configured. Please set up Zoom credentials.",
                "config_required": True
            }
        
        meeting_data = {
            "topic": topic,
            "type": 2,  # Scheduled meeting
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "duration": duration_minutes,
            "timezone": "Asia/Kolkata",
            "agenda": agenda,
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": True,
                "waiting_room": True,
                "meeting_authentication": False
            }
        }
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with session.post(
                f"{self.base_url}/users/me/meetings",
                headers=headers,
                json=meeting_data
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    
                    return {
                        "success": True,
                        "meeting_id": data.get("id"),
                        "join_url": data.get("join_url"),
                        "start_url": data.get("start_url"),
                        "password": data.get("password"),
                        "topic": data.get("topic"),
                        "start_time": data.get("start_time"),
                        "duration": data.get("duration")
                    }
                else:
                    error = await response.json()
                    return {
                        "success": False,
                        "error": error.get("message", "Failed to create meeting")
                    }


class SendGridService:
    """SendGrid email service for reliable email delivery"""
    
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@supermanager.app")
        self.from_name = os.getenv("SENDGRID_FROM_NAME", "Super Manager")
    
    async def send_email(self, message: EmailMessage) -> Dict:
        """Send email via SendGrid"""
        
        if not self.api_key:
            return {
                "success": False,
                "error": "SendGrid not configured",
                "config_required": True
            }
        
        payload = {
            "personalizations": [
                {
                    "to": [{"email": email} for email in message.to],
                    "subject": message.subject
                }
            ],
            "from": {
                "email": message.from_email or self.from_email,
                "name": message.from_name or self.from_name
            },
            "content": [
                {"type": "text/plain", "value": message.body_text}
            ]
        }
        
        if message.body_html:
            payload["content"].append({"type": "text/html", "value": message.body_html})
        
        if message.cc:
            payload["personalizations"][0]["cc"] = [{"email": email} for email in message.cc]
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with session.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers=headers,
                json=payload
            ) as response:
                if response.status in [200, 202]:
                    message.status = EmailStatus.SENT
                    message.sent_at = datetime.now()
                    
                    return {
                        "success": True,
                        "message_id": response.headers.get("X-Message-Id"),
                        "tracking_id": message.tracking_id
                    }
                else:
                    error = await response.text()
                    message.status = EmailStatus.FAILED
                    return {
                        "success": False,
                        "error": error
                    }


class CommunicationService:
    """Unified service for email, calendar, and meeting management"""
    
    def __init__(self, user_tokens: Dict = None):
        self.user_tokens = user_tokens or {}
        self.gmail = GmailService(user_tokens.get("google_access_token"))
        self.calendar = GoogleCalendarService(user_tokens.get("google_access_token"))
        self.zoom = ZoomService()
        self.sendgrid = SendGridService()
        self.oauth = GoogleOAuthClient()
        
        # Track sent messages and created events
        self.sent_emails: Dict[str, EmailMessage] = {}
        self.created_events: Dict[str, CalendarEvent] = {}
    
    def generate_id(self, prefix: str = "MSG") -> str:
        """Generate unique ID"""
        return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"
    
    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        body_html: str = None,
        cc: List[str] = None,
        attachments: List[Dict] = None,
        use_user_account: bool = True
    ) -> Dict:
        """Send email (tries user's Gmail first, falls back to SendGrid)"""
        
        message = EmailMessage(
            id=self.generate_id("EMAIL"),
            to=to,
            subject=subject,
            body_text=body,
            body_html=body_html,
            cc=cc or []
        )
        
        # Try Gmail first if user has connected their account
        if use_user_account and self.gmail.access_token:
            result = await self.gmail.send_email(message)
            if result.get("success"):
                self.sent_emails[message.id] = message
                return result
            elif not result.get("auth_required"):
                # Real error, not just auth issue
                return result
        
        # Fall back to SendGrid
        result = await self.sendgrid.send_email(message)
        if result.get("success"):
            self.sent_emails[message.id] = message
        
        return result
    
    async def schedule_meeting(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str],
        description: str = "",
        platform: MeetingPlatform = MeetingPlatform.GOOGLE_MEET,
        location: str = None
    ) -> Dict:
        """Schedule a meeting with video conferencing"""
        
        event = CalendarEvent(
            id=self.generate_id("MTG"),
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            attendees=[{"email": email} for email in attendees],
            meeting_platform=platform,
            location=location
        )
        
        # Create meeting based on platform
        meeting_result = None
        
        if platform == MeetingPlatform.ZOOM:
            meeting_result = await self.zoom.create_meeting(
                topic=title,
                start_time=start_time,
                duration_minutes=int((end_time - start_time).total_seconds() / 60),
                agenda=description,
                attendees=attendees
            )
            
            if meeting_result.get("success"):
                event.meeting_link = meeting_result.get("join_url")
                event.location = meeting_result.get("join_url")
        
        # Create calendar event
        calendar_result = await self.calendar.create_event(event)
        
        if calendar_result.get("success"):
            self.created_events[event.id] = event
            
            # Send invitations to attendees
            invite_body = f"""
You have been invited to a meeting.

Meeting: {title}
Date: {start_time.strftime('%B %d, %Y')}
Time: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}
"""
            if event.meeting_link:
                invite_body += f"\nJoin: {event.meeting_link}"
            
            if description:
                invite_body += f"\n\nDescription:\n{description}"
            
            # Send email invitations
            for attendee in attendees:
                await self.send_email(
                    to=[attendee],
                    subject=f"Meeting Invitation: {title}",
                    body=invite_body,
                    use_user_account=True
                )
            
            return {
                "success": True,
                "event_id": event.id,
                "calendar_event_id": calendar_result.get("event_id"),
                "calendar_link": calendar_result.get("html_link"),
                "meeting_link": event.meeting_link or calendar_result.get("meeting_link"),
                "title": title,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "attendees": attendees,
                "invitations_sent": True
            }
        elif calendar_result.get("auth_required"):
            # Calendar not connected, but we might have created a Zoom meeting
            if meeting_result and meeting_result.get("success"):
                return {
                    "success": True,
                    "partial": True,
                    "meeting_link": meeting_result.get("join_url"),
                    "warning": "Calendar not connected. Meeting created but not added to calendar.",
                    "auth_url": calendar_result.get("auth_url")
                }
            
            return {
                "success": False,
                "error": "Please connect your Google Calendar to schedule meetings",
                "auth_required": True,
                "auth_url": calendar_result.get("auth_url")
            }
        
        return calendar_result
    
    async def get_availability(
        self,
        date: datetime,
        attendees: List[str] = None
    ) -> Dict:
        """Get availability for scheduling"""
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59)
        
        events_result = await self.calendar.get_events(
            time_min=start_of_day,
            time_max=end_of_day,
            max_results=50
        )
        
        if not events_result.get("success"):
            return events_result
        
        busy_slots = []
        for event in events_result.get("events", []):
            start = event.get("start", {}).get("dateTime")
            end = event.get("end", {}).get("dateTime")
            if start and end:
                busy_slots.append({
                    "start": start,
                    "end": end,
                    "title": event.get("summary", "Busy")
                })
        
        # Calculate free slots (assuming 9 AM to 6 PM working hours)
        free_slots = []
        work_start = start_of_day.replace(hour=9)
        work_end = start_of_day.replace(hour=18)
        
        # Simple free slot calculation
        current = work_start
        for slot in sorted(busy_slots, key=lambda x: x["start"]):
            slot_start = datetime.fromisoformat(slot["start"].replace("Z", "+00:00"))
            if current < slot_start:
                free_slots.append({
                    "start": current.isoformat(),
                    "end": slot_start.isoformat()
                })
            slot_end = datetime.fromisoformat(slot["end"].replace("Z", "+00:00"))
            current = max(current, slot_end)
        
        if current < work_end:
            free_slots.append({
                "start": current.isoformat(),
                "end": work_end.isoformat()
            })
        
        return {
            "success": True,
            "date": date.strftime("%Y-%m-%d"),
            "busy_slots": busy_slots,
            "free_slots": free_slots
        }
    
    def get_auth_url(self) -> str:
        """Get Google OAuth URL for connecting accounts"""
        return self.oauth.get_auth_url()
    
    async def handle_oauth_callback(self, code: str) -> Dict:
        """Handle OAuth callback and store tokens"""
        result = await self.oauth.exchange_code(code)
        
        if "access_token" in result:
            self.user_tokens["google_access_token"] = result["access_token"]
            self.user_tokens["google_refresh_token"] = result.get("refresh_token")
            
            # Reinitialize services with new token
            self.gmail = GmailService(result["access_token"])
            self.calendar = GoogleCalendarService(result["access_token"])
            
            return {
                "success": True,
                "message": "Google account connected successfully",
                "services": ["Gmail", "Google Calendar"]
            }
        
        return {
            "success": False,
            "error": result.get("error", "OAuth failed")
        }
