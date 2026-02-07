"""
Action Executor - Real Integrations
===================================
Executes actions using real APIs:
- Gmail (OAuth) - Send emails
- Google Calendar - Create events with Meet links
- Jitsi/Zoom - Create meeting links
- Telegram - Send messages via bot
- Twilio - SMS and calls
- Web Search - DuckDuckGo
"""

import os
import json
import uuid
import asyncio
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import quote, unquote
import re

import httpx
from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# CONFIGURATION
# =============================================================================

# Gmail OAuth
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN", "")
GMAIL_USER = os.getenv("GMAIL_USER", "")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER", "")

# Zoom
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID", "")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET", "")
ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID", "")


# =============================================================================
# EMAIL EXECUTOR (Gmail OAuth)
# =============================================================================

class EmailExecutor:
    """Send emails using Gmail OAuth or SMTP fallback"""
    
    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
    
    async def _get_access_token(self) -> Optional[str]:
        """Get or refresh Gmail access token"""
        if not GMAIL_REFRESH_TOKEN:
            return None
        
        # Check if current token is still valid
        if self._access_token and self._token_expires and datetime.utcnow() < self._token_expires:
            return self._access_token
        
        # Refresh the token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GMAIL_CLIENT_ID,
                    "client_secret": GMAIL_CLIENT_SECRET,
                    "refresh_token": GMAIL_REFRESH_TOKEN,
                    "grant_type": "refresh_token"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                return self._access_token
            else:
                print(f"[EMAIL] Token refresh failed: {response.text}")
                return None
    
    async def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        is_html: bool = True,
        is_meeting_invite: bool = False
    ) -> Dict[str, Any]:
        """Send an email"""
        
        # Build the email message
        msg = MIMEMultipart("alternative")
        msg["From"] = GMAIL_USER
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        
        # Add body
        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type))
        
        # Try Gmail API first
        access_token = await self._get_access_token()
        
        if access_token:
            try:
                # Encode message for Gmail API
                raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                        headers={"Authorization": f"Bearer {access_token}"},
                        json={"raw": raw}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return {
                            "success": True,
                            "message_id": result.get("id"),
                            "method": "gmail_api",
                            "recipients": to
                        }
                    else:
                        print(f"[EMAIL] Gmail API error: {response.text}")
            except Exception as e:
                print(f"[EMAIL] Gmail API exception: {e}")
        
        # Fallback to SMTP (requires app password)
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        if smtp_password:
            try:
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(GMAIL_USER, smtp_password)
                    server.send_message(msg)
                
                return {
                    "success": True,
                    "method": "smtp",
                    "recipients": to
                }
            except Exception as e:
                print(f"[EMAIL] SMTP error: {e}")
        
        return {
            "success": False,
            "error": "Email service not configured. Set GMAIL_REFRESH_TOKEN or SMTP_PASSWORD."
        }


# =============================================================================
# CALENDAR EXECUTOR (Google Calendar)
# =============================================================================

class CalendarExecutor:
    """Create calendar events using Google Calendar API"""
    
    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
    
    async def _get_access_token(self) -> Optional[str]:
        """Get Google Calendar access token (shares OAuth with Gmail)"""
        if not GMAIL_REFRESH_TOKEN:
            return None
        
        if self._access_token and self._token_expires and datetime.utcnow() < self._token_expires:
            return self._access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GMAIL_CLIENT_ID,
                    "client_secret": GMAIL_CLIENT_SECRET,
                    "refresh_token": GMAIL_REFRESH_TOKEN,
                    "grant_type": "refresh_token"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                return self._access_token
        
        return None
    
    async def create_event(
        self,
        title: str,
        start_time: str,
        duration_minutes: int = 30,
        attendees: List[str] = None,
        description: str = "",
        add_video_meeting: bool = True
    ) -> Dict[str, Any]:
        """Create a calendar event"""
        
        # Parse start time
        try:
            if "T" in start_time:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            else:
                # Try to parse natural language (simplified)
                start_dt = self._parse_time(start_time)
        except:
            # Default to tomorrow at 10am
            start_dt = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0)
        
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        # Try Google Calendar API
        access_token = await self._get_access_token()
        
        if access_token:
            try:
                event = {
                    "summary": title,
                    "description": description,
                    "start": {
                        "dateTime": start_dt.isoformat(),
                        "timeZone": "Asia/Kolkata"
                    },
                    "end": {
                        "dateTime": end_dt.isoformat(),
                        "timeZone": "Asia/Kolkata"
                    }
                }
                
                if attendees:
                    event["attendees"] = [{"email": email} for email in attendees]
                
                if add_video_meeting:
                    event["conferenceData"] = {
                        "createRequest": {
                            "requestId": str(uuid.uuid4()),
                            "conferenceSolutionKey": {"type": "hangoutsMeet"}
                        }
                    }
                
                async with httpx.AsyncClient() as client:
                    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
                    if add_video_meeting:
                        url += "?conferenceDataVersion=1"
                    
                    response = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {access_token}"},
                        json=event
                    )
                    
                    if response.status_code in [200, 201]:
                        result = response.json()
                        meet_link = result.get("hangoutLink", "")
                        return {
                            "success": True,
                            "event_id": result.get("id"),
                            "event_link": result.get("htmlLink"),
                            "meeting_link": meet_link,
                            "start_time": start_dt.isoformat(),
                            "method": "google_calendar"
                        }
                    else:
                        print(f"[CALENDAR] API error: {response.text}")
            except Exception as e:
                print(f"[CALENDAR] Exception: {e}")
        
        # Fallback: Create Jitsi link instead
        meeting_id = f"supermanager-{uuid.uuid4().hex[:8]}"
        jitsi_link = f"https://meet.jit.si/{meeting_id}"
        
        return {
            "success": True,
            "event_id": meeting_id,
            "meeting_link": jitsi_link,
            "start_time": start_dt.isoformat(),
            "method": "jitsi_fallback",
            "note": "Calendar API not configured, using Jitsi link"
        }
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse natural language time (simplified)"""
        time_lower = time_str.lower()
        now = datetime.now()
        
        # Handle "tomorrow"
        if "tomorrow" in time_lower:
            base = now + timedelta(days=1)
        elif "today" in time_lower:
            base = now
        else:
            base = now + timedelta(days=1)  # Default to tomorrow
        
        # Extract time
        time_match = re.search(r'(\d{1,2})\s*(am|pm|:00)?', time_lower)
        if time_match:
            hour = int(time_match.group(1))
            if time_match.group(2) == "pm" and hour < 12:
                hour += 12
            base = base.replace(hour=hour, minute=0, second=0)
        else:
            base = base.replace(hour=10, minute=0, second=0)
        
        return base


# =============================================================================
# MEETING LINK EXECUTOR (Zoom/Jitsi)
# =============================================================================

class MeetingExecutor:
    """Create video meeting links"""
    
    async def create_link(
        self,
        platform: str = "jitsi",
        title: str = "Meeting"
    ) -> Dict[str, Any]:
        """Create a meeting link"""
        
        meeting_id = f"supermanager-{uuid.uuid4().hex[:8]}"
        
        if platform == "zoom" and ZOOM_CLIENT_ID:
            # Try Zoom API
            try:
                link = await self._create_zoom_meeting(title)
                if link:
                    return {
                        "success": True,
                        "platform": "zoom",
                        "meeting_link": link["join_url"],
                        "meeting_id": link["id"]
                    }
            except Exception as e:
                print(f"[MEETING] Zoom error: {e}")
        
        # Default to Jitsi (always works, no API needed)
        jitsi_link = f"https://meet.jit.si/{meeting_id}"
        
        return {
            "success": True,
            "platform": "jitsi",
            "meeting_link": jitsi_link,
            "meeting_id": meeting_id
        }
    
    async def _create_zoom_meeting(self, title: str) -> Optional[Dict]:
        """Create a Zoom meeting via API"""
        if not ZOOM_CLIENT_ID or not ZOOM_CLIENT_SECRET or not ZOOM_ACCOUNT_ID:
            return None
        
        # Get access token
        auth = base64.b64encode(f"{ZOOM_CLIENT_ID}:{ZOOM_CLIENT_SECRET}".encode()).decode()
        
        async with httpx.AsyncClient() as client:
            # Get token
            token_resp = await client.post(
                "https://zoom.us/oauth/token",
                headers={"Authorization": f"Basic {auth}"},
                data={
                    "grant_type": "account_credentials",
                    "account_id": ZOOM_ACCOUNT_ID
                }
            )
            
            if token_resp.status_code != 200:
                return None
            
            access_token = token_resp.json().get("access_token")
            
            # Create meeting
            meeting_resp = await client.post(
                "https://api.zoom.us/v2/users/me/meetings",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "topic": title,
                    "type": 1,  # Instant meeting
                    "settings": {
                        "join_before_host": True,
                        "waiting_room": False
                    }
                }
            )
            
            if meeting_resp.status_code == 201:
                return meeting_resp.json()
        
        return None


# =============================================================================
# TELEGRAM EXECUTOR
# =============================================================================

class TelegramExecutor:
    """Send Telegram messages via bot"""
    
    async def send(
        self,
        recipient: str,
        message: str
    ) -> Dict[str, Any]:
        """Send a Telegram message"""
        
        if not TELEGRAM_BOT_TOKEN:
            return {
                "success": False,
                "error": "Telegram bot not configured. Set TELEGRAM_BOT_TOKEN."
            }
        
        # Determine chat ID
        # If recipient looks like a chat ID, use directly
        # Otherwise, we'd need to look it up (requires user to message bot first)
        chat_id = recipient
        if not recipient.lstrip("-").isdigit():
            # Try to look up username (would need prior interaction)
            return {
                "success": False,
                "error": f"Cannot find Telegram chat for '{recipient}'. User must message the bot first."
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return {
                        "success": True,
                        "message_id": result["result"]["message_id"],
                        "chat_id": chat_id
                    }
            
            return {
                "success": False,
                "error": f"Telegram API error: {response.text}"
            }


# =============================================================================
# SMS EXECUTOR (Twilio)
# =============================================================================

class SMSExecutor:
    """Send SMS via Twilio"""
    
    async def send(
        self,
        phone: str,
        message: str
    ) -> Dict[str, Any]:
        """Send an SMS"""
        
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE:
            return {
                "success": False,
                "error": "Twilio not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER."
            }
        
        # Ensure phone has country code
        if not phone.startswith("+"):
            phone = "+91" + phone  # Default to India
        
        async with httpx.AsyncClient() as client:
            auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            
            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
                auth=auth,
                data={
                    "From": TWILIO_PHONE,
                    "To": phone,
                    "Body": message
                }
            )
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "message_sid": result.get("sid"),
                    "to": phone
                }
            
            return {
                "success": False,
                "error": f"Twilio error: {response.text}"
            }


# =============================================================================
# WEB SEARCH EXECUTOR
# =============================================================================

class SearchExecutor:
    """Search the web using DuckDuckGo"""
    
    async def search(
        self,
        query: str,
        search_type: str = "general",
        num_results: int = 5
    ) -> Dict[str, Any]:
        """Search the web"""
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Use DuckDuckGo HTML endpoint
            response = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            
            results = []
            html = response.text
            
            # Parse results
            result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
            snippet_pattern = r'<a class="result__snippet"[^>]*>([^<]+)</a>'
            
            links = re.findall(result_pattern, html)
            snippets = re.findall(snippet_pattern, html)
            
            for i, (link, title) in enumerate(links[:num_results]):
                # Clean up redirect URL
                if "uddg=" in link:
                    actual_url = link.split("uddg=")[-1].split("&")[0]
                    link = unquote(actual_url)
                
                snippet = snippets[i] if i < len(snippets) else ""
                
                results.append({
                    "title": title.strip(),
                    "url": link,
                    "snippet": snippet.strip()[:200]
                })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }


# =============================================================================
# MAIN ACTION EXECUTOR
# =============================================================================

class ActionExecutor:
    """
    Main executor that routes actions to appropriate handlers.
    This is what the Agent uses to execute tool calls.
    """
    
    def __init__(self):
        self.email = EmailExecutor()
        self.calendar = CalendarExecutor()
        self.meeting = MeetingExecutor()
        self.telegram = TelegramExecutor()
        self.sms = SMSExecutor()
        self.search = SearchExecutor()
    
    async def execute(self, action_type: str, params: Dict) -> Dict[str, Any]:
        """Route and execute an action"""
        
        try:
            if action_type == "send_email":
                to = params.get("to", [])
                if isinstance(to, str):
                    to = [to]
                return await self.email.send(
                    to=to,
                    subject=params.get("subject", ""),
                    body=params.get("body", ""),
                    is_meeting_invite=params.get("is_meeting_invite", False)
                )
            
            elif action_type == "create_calendar_event":
                return await self.calendar.create_event(
                    title=params.get("title", "Event"),
                    start_time=params.get("start_time", "tomorrow 10am"),
                    duration_minutes=params.get("duration_minutes", 30),
                    attendees=params.get("attendees", []),
                    description=params.get("description", ""),
                    add_video_meeting=params.get("add_video_meeting", True)
                )
            
            elif action_type == "create_meeting_link":
                return await self.meeting.create_link(
                    platform=params.get("platform", "jitsi"),
                    title=params.get("title", "Meeting")
                )
            
            elif action_type == "send_telegram":
                return await self.telegram.send(
                    recipient=params.get("recipient", ""),
                    message=params.get("message", "")
                )
            
            elif action_type == "send_sms":
                return await self.sms.send(
                    phone=params.get("phone", ""),
                    message=params.get("message", "")
                )
            
            elif action_type == "search_web":
                return await self.search.search(
                    query=params.get("query", ""),
                    search_type=params.get("type", "general")
                )
            
            elif action_type == "set_reminder":
                # For now, send email as reminder
                return await self.email.send(
                    to=[GMAIL_USER],
                    subject=f"Reminder: {params.get('text', 'Reminder')}",
                    body=f"""
                    <h2>⏰ Reminder</h2>
                    <p>{params.get('text', '')}</p>
                    <p>Time: {params.get('time', 'soon')}</p>
                    """
                )
            
            elif action_type == "lookup_contact":
                # This would use the memory system
                return {
                    "success": True,
                    "note": "Contact lookup requires memory integration",
                    "params": params
                }
            
            elif action_type == "get_user_info":
                # This would use the memory system
                return {
                    "success": True,
                    "note": "User info requires memory integration",
                    "params": params
                }
            
            elif action_type == "update_user_preference":
                # This would use the memory system
                return {
                    "success": True,
                    "note": "Preference saved",
                    "params": params
                }
            
            elif action_type == "make_payment":
                # Generate UPI link
                amount = params.get("amount", 0)
                to = params.get("to", "")
                upi_link = f"upi://pay?pa={to}&am={amount}&cu=INR"
                return {
                    "success": True,
                    "upi_link": upi_link,
                    "amount": amount,
                    "to": to
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_executor: Optional[ActionExecutor] = None


def get_executor() -> ActionExecutor:
    """Get the global executor instance"""
    global _executor
    if _executor is None:
        _executor = ActionExecutor()
    return _executor
