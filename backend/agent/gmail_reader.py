"""
Gmail Email Reader
==================
Reads emails from the AI's Gmail account to:
- Get verification codes/links
- Read OTPs
- Extract API keys sent via email
"""

import os
import re
import base64
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from email.mime.text import MIMEText

import httpx
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Gmail OAuth Configuration
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN", "")
GMAIL_USER = os.getenv("GMAIL_USER", "")


@dataclass
class Email:
    """Represents an email message"""
    id: str
    thread_id: str
    subject: str
    sender: str
    recipient: str
    date: datetime
    body_text: str
    body_html: str
    snippet: str


@dataclass
class VerificationCode:
    """Extracted verification code/link"""
    code: Optional[str] = None
    link: Optional[str] = None
    otp: Optional[str] = None
    source_email_id: Optional[str] = None
    service: Optional[str] = None


class GmailReader:
    """
    Reads emails from Gmail using OAuth 2.0.
    
    Capabilities:
    - Fetch recent emails
    - Search for verification emails
    - Extract OTPs and verification links
    """
    
    # Common verification patterns
    OTP_PATTERNS = [
        r'\b(\d{4})\b',  # 4-digit OTP
        r'\b(\d{6})\b',  # 6-digit OTP
        r'code[:\s]+(\d{4,8})',  # "code: 123456"
        r'verification code[:\s]+(\d{4,8})',
        r'OTP[:\s]+(\d{4,8})',
        r'one-time password[:\s]+(\d{4,8})',
    ]
    
    VERIFICATION_LINK_PATTERNS = [
        r'(https?://[^\s]+verify[^\s]*)',
        r'(https?://[^\s]+confirm[^\s]*)',
        r'(https?://[^\s]+activate[^\s]*)',
        r'(https?://[^\s]+auth[^\s]*)',
        r'(https?://[^\s]+token=[^\s]*)',
    ]
    
    def __init__(
        self,
        client_id: str = GMAIL_CLIENT_ID,
        client_secret: str = GMAIL_CLIENT_SECRET,
        refresh_token: str = GMAIL_REFRESH_TOKEN,
        user_email: str = GMAIL_USER
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.user_email = user_email
        self._service = None
        self._credentials = None
    
    def _get_credentials(self) -> Credentials:
        """Get OAuth credentials, refreshing if needed"""
        if self._credentials and self._credentials.valid:
            return self._credentials
        
        self._credentials = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=[
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.modify"
            ]
        )
        
        # Refresh the token
        if self._credentials.expired or not self._credentials.valid:
            self._credentials.refresh(Request())
        
        return self._credentials
    
    def _get_service(self):
        """Get Gmail API service"""
        if self._service:
            return self._service
        
        creds = self._get_credentials()
        self._service = build('gmail', 'v1', credentials=creds)
        return self._service
    
    async def fetch_recent_emails(
        self, 
        max_results: int = 10,
        query: str = "",
        after_date: Optional[datetime] = None
    ) -> List[Email]:
        """Fetch recent emails from inbox"""
        
        service = self._get_service()
        
        # Build query
        search_query = query or "in:inbox"
        if after_date:
            search_query += f" after:{after_date.strftime('%Y/%m/%d')}"
        
        # Run in thread pool since gmail API is synchronous
        loop = asyncio.get_event_loop()
        
        def fetch():
            results = service.users().messages().list(
                userId='me',
                q=search_query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg_ref in messages:
                msg = service.users().messages().get(
                    userId='me',
                    id=msg_ref['id'],
                    format='full'
                ).execute()
                
                email = self._parse_message(msg)
                if email:
                    emails.append(email)
            
            return emails
        
        return await loop.run_in_executor(None, fetch)
    
    def _parse_message(self, msg: Dict) -> Optional[Email]:
        """Parse a Gmail message into an Email object"""
        try:
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            
            # Extract body
            body_text = ""
            body_html = ""
            
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                    elif part['mimeType'] == 'text/html':
                        data = part['body'].get('data', '')
                        body_html = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            elif msg['payload']['body'].get('data'):
                data = msg['payload']['body']['data']
                body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            
            # Parse date
            date_str = headers.get('Date', '')
            try:
                # Try common date formats
                from email.utils import parsedate_to_datetime
                date = parsedate_to_datetime(date_str)
            except:
                date = datetime.now()
            
            return Email(
                id=msg['id'],
                thread_id=msg['threadId'],
                subject=headers.get('Subject', ''),
                sender=headers.get('From', ''),
                recipient=headers.get('To', ''),
                date=date,
                body_text=body_text,
                body_html=body_html,
                snippet=msg.get('snippet', '')
            )
        except Exception as e:
            print(f"[GMAIL] Error parsing message: {e}")
            return None
    
    async def wait_for_verification_email(
        self,
        from_service: str,
        timeout_seconds: int = 120,
        poll_interval: int = 5
    ) -> Optional[VerificationCode]:
        """
        Wait for a verification email from a service.
        
        Args:
            from_service: Part of sender domain/name to match (e.g., "groq", "github")
            timeout_seconds: How long to wait
            poll_interval: How often to check (seconds)
        
        Returns:
            VerificationCode with extracted code/link, or None if timeout
        """
        
        start_time = datetime.now()
        search_start = start_time - timedelta(minutes=2)  # Check emails from 2 min ago
        
        print(f"[GMAIL] Waiting for verification email from {from_service}...")
        
        while (datetime.now() - start_time).seconds < timeout_seconds:
            try:
                # Search for verification emails
                query = f"from:{from_service} (verification OR verify OR confirm OR code OR OTP)"
                emails = await self.fetch_recent_emails(
                    max_results=5,
                    query=query,
                    after_date=search_start
                )
                
                if emails:
                    # Get the most recent one
                    email = emails[0]
                    verification = self._extract_verification(email, from_service)
                    
                    if verification.code or verification.link or verification.otp:
                        print(f"[GMAIL] Found verification from {from_service}!")
                        return verification
                
            except Exception as e:
                print(f"[GMAIL] Error fetching emails: {e}")
            
            await asyncio.sleep(poll_interval)
        
        print(f"[GMAIL] Timeout waiting for verification from {from_service}")
        return None
    
    def _extract_verification(self, email: Email, service: str) -> VerificationCode:
        """Extract verification code/link from email"""
        
        verification = VerificationCode(
            source_email_id=email.id,
            service=service
        )
        
        # Combine body text and subject for searching
        text = f"{email.subject} {email.body_text} {email.body_html}"
        
        # Try to find OTP
        for pattern in self.OTP_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1)
                if len(code) >= 4:  # Valid OTP length
                    verification.otp = code
                    verification.code = code
                    break
        
        # Try to find verification link
        for pattern in self.VERIFICATION_LINK_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                link = match.group(1)
                # Clean up the link (remove trailing punctuation)
                link = re.sub(r'[.,!?\'">\]]+$', '', link)
                verification.link = link
                break
        
        return verification
    
    async def get_api_key_from_email(
        self,
        from_service: str,
        timeout_seconds: int = 120
    ) -> Optional[str]:
        """
        Wait for and extract an API key from an email.
        
        Some services send API keys via email after signup.
        """
        
        # Common API key patterns
        api_key_patterns = [
            r'API[_\s]?key[:\s]+([a-zA-Z0-9_\-]{20,})',
            r'api[_\s]?key[:\s]+([a-zA-Z0-9_\-]{20,})',
            r'API[_\s]?token[:\s]+([a-zA-Z0-9_\-]{20,})',
            r'secret[_\s]?key[:\s]+([a-zA-Z0-9_\-]{20,})',
            r'access[_\s]?token[:\s]+([a-zA-Z0-9_\-]{20,})',
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI-style
            r'gsk_[a-zA-Z0-9]{20,}',  # Groq-style
        ]
        
        start_time = datetime.now()
        search_start = start_time - timedelta(minutes=5)
        
        while (datetime.now() - start_time).seconds < timeout_seconds:
            try:
                query = f"from:{from_service} (api key OR API key OR access token)"
                emails = await self.fetch_recent_emails(
                    max_results=5,
                    query=query,
                    after_date=search_start
                )
                
                for email in emails:
                    text = f"{email.body_text} {email.body_html}"
                    for pattern in api_key_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            return match.group(1) if match.lastindex else match.group(0)
                
            except Exception as e:
                print(f"[GMAIL] Error: {e}")
            
            await asyncio.sleep(10)
        
        return None


# Singleton instance
_gmail_reader: Optional[GmailReader] = None

def get_gmail_reader() -> GmailReader:
    """Get singleton Gmail reader instance"""
    global _gmail_reader
    if _gmail_reader is None:
        _gmail_reader = GmailReader()
    return _gmail_reader
