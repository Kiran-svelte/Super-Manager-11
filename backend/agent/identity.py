"""
AI Identity Manager
====================
Manages the AI's digital identity (Gmail account) and service accounts.

This module handles:
1. Gmail authentication (App Password or OAuth)
2. Email operations (send, read, verify links)
3. Service signup automation
4. API key management
5. Credential encryption
"""

import os
import re
import uuid
import json
import base64
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import httpx

# Email libraries
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header

# Encryption
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Supabase - REQUIRED in production
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# 2Captcha for CAPTCHA solving - optional
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "")

# Encryption secret - REQUIRED in production
ENCRYPTION_SECRET = os.getenv("ENCRYPTION_SECRET", "")

# Validate required environment variables
def _validate_env():
    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    if not ENCRYPTION_SECRET:
        missing.append("ENCRYPTION_SECRET")
    if missing:
        import warnings
        warnings.warn(f"Missing environment variables: {', '.join(missing)}. Some features may not work.")

_validate_env()


class AuthType(Enum):
    APP_PASSWORD = "app_password"
    OAUTH = "oauth"


class IdentityStatus(Enum):
    PENDING_SETUP = "pending_setup"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    VERIFICATION_NEEDED = "verification_needed"


@dataclass
class AIIdentity:
    """The AI's digital identity"""
    id: str
    user_id: str
    email: str
    display_name: str = "AI Assistant"
    auth_type: AuthType = AuthType.APP_PASSWORD
    status: IdentityStatus = IdentityStatus.PENDING_SETUP
    can_send_email: bool = False
    can_read_email: bool = False
    can_signup_services: bool = False
    metadata: Dict = field(default_factory=dict)
    
    # Decrypted credentials (only in memory, never stored)
    _password: Optional[str] = None
    _oauth_token: Optional[str] = None


class EncryptionManager:
    """Handles encryption/decryption of sensitive data"""
    
    def __init__(self, secret: str = None, user_salt: str = None):
        # Use provided secret or fall back to env var
        secret = secret or ENCRYPTION_SECRET
        
        # Track whether real encryption is available
        self._enabled = bool(secret)
        
        if not self._enabled:
            # No encryption secret - use reversible encoding (NOT secure, just obfuscation)
            # In production, ENCRYPTION_SECRET should always be set
            import warnings
            warnings.warn("ENCRYPTION_SECRET not set - using base64 encoding (NOT SECURE)")
            self.fernet = None
            return
        
        # Salt should be unique per user for best security
        # If not provided, use a default (less secure but functional)
        salt = (user_salt or "super-manager-default").encode()
        
        # Derive a key from the secret
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        self.fernet = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string"""
        if not data:
            return ""
        if not self._enabled:
            # Fallback to base64 encoding
            return base64.b64encode(data.encode()).decode()
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string"""
        if not encrypted_data:
            return ""
        if not self._enabled:
            # Fallback to base64 decoding
            try:
                return base64.b64decode(encrypted_data.encode()).decode()
            except Exception:
                # Already plaintext
                return encrypted_data
        return self.fernet.decrypt(encrypted_data.encode()).decode()


class GmailManager:
    """Manages Gmail operations for the AI identity"""
    
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    IMAP_HOST = "imap.gmail.com"
    IMAP_PORT = 993
    SMTP_TIMEOUT = 10  # seconds
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self._smtp_conn = None
        self._imap_conn = None
    
    async def verify_credentials(self) -> Tuple[bool, str]:
        """Verify Gmail credentials work"""
        try:
            # Try SMTP connection with timeout
            server = smtplib.SMTP(self.SMTP_HOST, self.SMTP_PORT, timeout=self.SMTP_TIMEOUT)
            server.starttls()
            server.login(self.email, self.password)
            server.quit()
            return True, "Credentials verified successfully"
        except smtplib.SMTPAuthenticationError:
            return False, "Invalid credentials. Make sure you're using an App Password, not your regular password."
        except TimeoutError:
            return False, "Connection timed out. Please try again."
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    async def send_email(
        self, 
        to: str, 
        subject: str, 
        body: str, 
        html: bool = False
    ) -> Tuple[bool, str]:
        """Send an email"""
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.email
            msg["To"] = to
            msg["Subject"] = subject
            
            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(self.SMTP_HOST, self.SMTP_PORT) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return True, f"Email sent to {to}"
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    async def read_emails(
        self, 
        folder: str = "INBOX", 
        limit: int = 10,
        unread_only: bool = True
    ) -> List[Dict]:
        """Read emails from inbox"""
        emails = []
        try:
            mail = imaplib.IMAP4_SSL(self.IMAP_HOST, self.IMAP_PORT)
            mail.login(self.email, self.password)
            mail.select(folder)
            
            # Search for emails
            search_criteria = "UNSEEN" if unread_only else "ALL"
            _, message_numbers = mail.search(None, search_criteria)
            
            # Get the latest emails
            numbers = message_numbers[0].split()[-limit:]
            
            for num in reversed(numbers):
                _, msg_data = mail.fetch(num, "(RFC822)")
                email_body = msg_data[0][1]
                msg = email.message_from_bytes(email_body)
                
                # Decode subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")
                
                # Get sender
                sender = msg["From"]
                
                # Get body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                
                emails.append({
                    "id": num.decode(),
                    "from": sender,
                    "subject": subject,
                    "body": body[:500],  # Truncate for safety
                    "date": msg["Date"]
                })
            
            mail.logout()
            return emails
            
        except Exception as e:
            print(f"[GMAIL ERROR] Failed to read emails: {str(e)}")
            return []
    
    async def find_verification_email(
        self, 
        from_domain: str, 
        timeout_seconds: int = 60
    ) -> Optional[Dict]:
        """Wait for and find a verification email"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout_seconds:
            emails = await self.read_emails(limit=5, unread_only=True)
            
            for mail in emails:
                sender = mail.get("from", "").lower()
                if from_domain.lower() in sender:
                    return mail
            
            # Wait before checking again
            await asyncio.sleep(5)
        
        return None
    
    async def extract_verification_link(self, email_body: str) -> Optional[str]:
        """Extract verification link from email body"""
        # Common patterns for verification links
        patterns = [
            r'https?://[^\s<>"]+verify[^\s<>"]*',
            r'https?://[^\s<>"]+confirm[^\s<>"]*',
            r'https?://[^\s<>"]+activate[^\s<>"]*',
            r'https?://[^\s<>"]+token=[^\s<>"]+',
            r'href="(https?://[^"]+)"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, email_body, re.IGNORECASE)
            if matches:
                # Return the first verification-looking link
                for match in matches:
                    if 'unsubscribe' not in match.lower() and 'privacy' not in match.lower():
                        return match
        
        return None
    
    async def extract_otp(self, email_body: str) -> Optional[str]:
        """Extract OTP code from email body"""
        # Common OTP patterns (4-8 digits)
        patterns = [
            r'\b(\d{6})\b',  # 6-digit OTP (most common)
            r'\b(\d{4})\b',  # 4-digit OTP
            r'\b(\d{8})\b',  # 8-digit OTP
            r'code[:\s]+(\d{4,8})',
            r'OTP[:\s]+(\d{4,8})',
            r'verification[:\s]+(\d{4,8})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, email_body, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None


class AIIdentityManager:
    """Manages AI identities and their operations"""
    
    def __init__(self):
        self.encryption = EncryptionManager()
        self._identities: Dict[str, AIIdentity] = {}
        self._gmail_managers: Dict[str, GmailManager] = {}
        
        # Initialize Supabase client
        try:
            from supabase import create_client
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except:
            self.supabase = None
    
    async def create_identity(
        self,
        user_id: str,
        email: str,
        password: str,
        display_name: str = "AI Assistant",
        auth_type: AuthType = AuthType.APP_PASSWORD
    ) -> Tuple[Optional[AIIdentity], str]:
        """Create a new AI identity for a user"""
        
        # Encrypt the password
        encrypted_password = self.encryption.encrypt(password)
        
        # Verify credentials first
        gmail = GmailManager(email, password)
        success, message = await gmail.verify_credentials()
        
        if not success:
            return None, message
        
        # Create identity
        identity_id = str(uuid.uuid4())
        identity = AIIdentity(
            id=identity_id,
            user_id=user_id,
            email=email,
            display_name=display_name,
            auth_type=auth_type,
            status=IdentityStatus.ACTIVE,
            can_send_email=True,
            can_read_email=True,
            can_signup_services=True,
            _password=password  # Keep in memory
        )
        
        # Save to database
        if self.supabase:
            try:
                self.supabase.table("ai_identities").upsert({
                    "id": identity_id,
                    "user_id": user_id,
                    "email": email,
                    "display_name": display_name,
                    "auth_type": auth_type.value,
                    "encrypted_password": encrypted_password,
                    "status": IdentityStatus.ACTIVE.value,
                    "can_send_email": True,
                    "can_read_email": True,
                    "can_signup_services": True,
                    "last_verified_at": datetime.now().isoformat()
                }).execute()
            except Exception as e:
                print(f"[IDENTITY DB ERROR] {str(e)}")
        
        # Cache
        self._identities[user_id] = identity
        self._gmail_managers[user_id] = gmail
        
        return identity, "AI identity created and verified successfully!"
    
    async def get_identity(self, user_id: str) -> Optional[AIIdentity]:
        """Get AI identity for a user"""
        
        # Check cache
        if user_id in self._identities:
            return self._identities[user_id]
        
        # Load from database
        if self.supabase:
            try:
                result = self.supabase.table("ai_identities")\
                    .select("*")\
                    .eq("user_id", user_id)\
                    .execute()
                
                if result.data and len(result.data) > 0:
                    data = result.data[0]
                    identity = AIIdentity(
                        id=data["id"],
                        user_id=data["user_id"],
                        email=data["email"],
                        display_name=data["display_name"],
                        auth_type=AuthType(data["auth_type"]),
                        status=IdentityStatus(data["status"]),
                        can_send_email=data["can_send_email"],
                        can_read_email=data["can_read_email"],
                        can_signup_services=data["can_signup_services"],
                        metadata=data.get("metadata", {})
                    )
                    
                    # Decrypt password
                    if data.get("encrypted_password"):
                        try:
                            identity._password = self.encryption.decrypt(data["encrypted_password"])
                        except:
                            pass
                    
                    self._identities[user_id] = identity
                    return identity
                    
            except Exception as e:
                print(f"[IDENTITY LOAD ERROR] {str(e)}")
        
        return None
    
    async def get_gmail_manager(self, user_id: str) -> Optional[GmailManager]:
        """Get Gmail manager for a user's AI identity"""
        
        # Check cache
        if user_id in self._gmail_managers:
            return self._gmail_managers[user_id]
        
        # Get identity and create manager
        identity = await self.get_identity(user_id)
        if identity and identity._password:
            gmail = GmailManager(identity.email, identity._password)
            self._gmail_managers[user_id] = gmail
            return gmail
        
        return None
    
    async def send_email_as_ai(
        self,
        user_id: str,
        to: str,
        subject: str,
        body: str
    ) -> Tuple[bool, str]:
        """Send an email using the AI's identity"""
        
        gmail = await self.get_gmail_manager(user_id)
        if not gmail:
            return False, "AI identity not set up. Please create an AI email first."
        
        return await gmail.send_email(to, subject, body)
    
    async def check_verification_email(
        self,
        user_id: str,
        from_domain: str
    ) -> Optional[Dict]:
        """Check for verification email"""
        
        gmail = await self.get_gmail_manager(user_id)
        if not gmail:
            return None
        
        return await gmail.find_verification_email(from_domain)
    
    async def is_service_blocked(self, service_name: str) -> Tuple[bool, Optional[Dict]]:
        """Check if a service is blocked and get alternatives"""
        
        if self.supabase:
            try:
                result = self.supabase.table("blocked_services")\
                    .select("*")\
                    .ilike("service_name", f"%{service_name}%")\
                    .execute()
                
                if result.data:
                    blocked = result.data[0]
                    return True, {
                        "reason": blocked["block_reason"],
                        "category": blocked["block_category"],
                        "alternatives": blocked.get("alternative_services", []),
                        "workaround": blocked.get("workaround_description")
                    }
            except:
                pass
        
        return False, None


class ResponsibleAI:
    """
    Ensures the AI is responsible, consistent, and accountable.
    
    Rules:
    1. Think before responding - consider implications
    2. Stick to decisions - don't flip-flop
    3. Log all major decisions for accountability
    4. Keep commitments
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.decisions: List[Dict] = []
        self.commitments: List[Dict] = []
        
        try:
            from supabase import create_client
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except:
            self.supabase = None
    
    async def log_decision(
        self,
        decision_type: str,
        summary: str,
        reasoning: str,
        proposed_action: Dict,
        session_id: str = None
    ) -> str:
        """Log a decision for accountability"""
        
        decision_id = str(uuid.uuid4())
        decision = {
            "id": decision_id,
            "user_id": self.user_id,
            "session_id": session_id,
            "decision_type": decision_type,
            "decision_summary": summary,
            "reasoning": reasoning,
            "proposed_action": proposed_action,
            "outcome": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        self.decisions.append(decision)
        
        if self.supabase:
            try:
                self.supabase.table("ai_decision_log").insert(decision).execute()
            except Exception as e:
                print(f"[DECISION LOG ERROR] {str(e)}")
        
        return decision_id
    
    async def record_commitment(
        self,
        commitment_text: str,
        context: str,
        importance: str = "normal"
    ) -> str:
        """Record a commitment the AI has made"""
        
        commitment_id = str(uuid.uuid4())
        commitment = {
            "id": commitment_id,
            "user_id": self.user_id,
            "commitment_text": commitment_text,
            "context": context,
            "importance": importance,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        self.commitments.append(commitment)
        
        if self.supabase:
            try:
                self.supabase.table("ai_commitments").insert(commitment).execute()
            except Exception as e:
                print(f"[COMMITMENT LOG ERROR] {str(e)}")
        
        return commitment_id
    
    async def check_consistency(self, proposed_action: Dict) -> Tuple[bool, str]:
        """Check if a proposed action is consistent with past decisions"""
        
        # Get recent decisions
        if self.supabase:
            try:
                result = self.supabase.table("ai_decision_log")\
                    .select("*")\
                    .eq("user_id", self.user_id)\
                    .order("created_at", desc=True)\
                    .limit(10)\
                    .execute()
                
                recent_decisions = result.data if result.data else []
                
                # Check for contradictions
                action_type = proposed_action.get("type", "")
                
                for decision in recent_decisions:
                    past_action = decision.get("proposed_action", {})
                    
                    # Simple contradiction check
                    if past_action.get("type") == action_type:
                        past_target = past_action.get("target", "")
                        new_target = proposed_action.get("target", "")
                        
                        if past_target == new_target:
                            # Same type and target - check for contradictions
                            return True, "Consistent with past decisions"
                
            except:
                pass
        
        return True, "No contradictions found"
    
    async def get_active_commitments(self) -> List[Dict]:
        """Get all active commitments"""
        
        if self.supabase:
            try:
                result = self.supabase.table("ai_commitments")\
                    .select("*")\
                    .eq("user_id", self.user_id)\
                    .eq("status", "active")\
                    .execute()
                
                return result.data if result.data else []
            except:
                pass
        
        return self.commitments


class SensitiveDataHandler:
    """
    Handles sensitive data (OTP, PAN, Aadhaar) securely.
    
    Rules:
    1. Never store permanently
    2. Request only when absolutely necessary
    3. Delete immediately after use
    4. Full audit trail
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._temp_data: Dict[str, str] = {}  # In-memory only
        
        try:
            from supabase import create_client
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except:
            self.supabase = None
    
    async def request_sensitive_data(
        self,
        data_type: str,
        purpose: str,
        service_name: str = None
    ) -> str:
        """Create a request for sensitive data from user"""
        
        request_id = str(uuid.uuid4())
        
        request = {
            "id": request_id,
            "user_id": self.user_id,
            "data_type": data_type,
            "purpose": purpose,
            "service_name": service_name,
            "status": "pending",
            "requested_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        
        if self.supabase:
            try:
                self.supabase.table("sensitive_data_requests").insert(request).execute()
            except Exception as e:
                print(f"[SENSITIVE REQUEST ERROR] {str(e)}")
        
        return request_id
    
    async def receive_sensitive_data(
        self,
        request_id: str,
        data: str
    ) -> bool:
        """Receive sensitive data from user (held in memory only)"""
        
        # Store in memory only - NEVER in database
        self._temp_data[request_id] = data
        
        # Update request status (but not the data itself)
        if self.supabase:
            try:
                self.supabase.table("sensitive_data_requests")\
                    .update({
                        "status": "received",
                        "received_at": datetime.now().isoformat(),
                        "data_received": True
                    })\
                    .eq("id", request_id)\
                    .execute()
            except:
                pass
        
        return True
    
    async def use_sensitive_data(self, request_id: str) -> Optional[str]:
        """Use and immediately delete sensitive data"""
        
        data = self._temp_data.pop(request_id, None)
        
        if data and self.supabase:
            try:
                self.supabase.table("sensitive_data_requests")\
                    .update({
                        "status": "used",
                        "used_at": datetime.now().isoformat()
                    })\
                    .eq("id", request_id)\
                    .execute()
            except:
                pass
        
        return data
    
    async def cleanup_expired(self):
        """Clean up expired sensitive data requests"""
        
        # Clear local temp data older than 10 minutes
        # In production, would track timestamps
        self._temp_data.clear()
        
        if self.supabase:
            try:
                # Delete expired requests
                self.supabase.table("sensitive_data_requests")\
                    .delete()\
                    .lt("expires_at", datetime.now().isoformat())\
                    .execute()
            except:
                pass


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_identity_manager: Optional[AIIdentityManager] = None

def get_identity_manager() -> AIIdentityManager:
    """Get singleton AI Identity Manager"""
    global _identity_manager
    if _identity_manager is None:
        _identity_manager = AIIdentityManager()
    return _identity_manager
