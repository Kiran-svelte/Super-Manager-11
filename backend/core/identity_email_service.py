"""
Identity-Aware Email Service
===============================
Enhanced email service that pulls credentials from user's stored AIIdentity
instead of relying solely on environment variables.

This enables per-user email sending with their own Gmail credentials.

Author: Super Manager AI
"""

import os
import asyncio
import logging
import base64
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load .env from backend directory if not already loaded
try:
    from dotenv import load_dotenv
    backend_env = Path(__file__).parent.parent / ".env"
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Check for Google API
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


class IdentityEmailService:
    """
    Email service that uses credentials from AIIdentity.
    
    This allows each user to send emails from their own Gmail account
    using their stored OAuth tokens or app passwords.
    
    Usage:
        service = IdentityEmailService()
        
        # Send email for a specific user
        result = await service.send_email_for_user(
            user_id="user123",
            to="recipient@example.com",
            subject="Hello",
            body="Your message here"
        )
    """
    
    def __init__(self):
        self._identity_manager = None
        self._oauth_manager = None
        self._firebase_store = None
        
    def _get_identity_manager(self):
        """Lazy load identity manager"""
        if self._identity_manager is None:
            try:
                from ..agent.identity import get_identity_manager
                self._identity_manager = get_identity_manager()
            except ImportError as e:
                logger.warning(f"Could not import identity manager: {e}")
        return self._identity_manager
    
    def _get_oauth_manager(self):
        """Lazy load OAuth manager"""
        if self._oauth_manager is None:
            try:
                from .oauth_manager import get_oauth_manager
                self._oauth_manager = get_oauth_manager()
            except ImportError as e:
                logger.warning(f"Could not import OAuth manager: {e}")
        return self._oauth_manager
    
    def _get_firebase_store(self):
        """Lazy load Firebase store"""
        if self._firebase_store is None:
            try:
                from .firebase_config import get_firebase_identity_store
                self._firebase_store = get_firebase_identity_store()
            except ImportError as e:
                logger.warning(f"Could not import Firebase store: {e}")
        return self._firebase_store
    
    async def get_user_email_credentials(
        self, 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get email credentials for a user from their stored AIIdentity.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with 'email', 'auth_type', and credentials
        """
        # Try identity manager (Supabase)
        identity_manager = self._get_identity_manager()
        if identity_manager:
            try:
                identity = await identity_manager.get_identity(user_id)
                if identity and identity.email:
                    return {
                        "email": identity.email,
                        "auth_type": identity.auth_type.value if identity.auth_type else "app_password",
                        "password": identity._password,
                        "can_send_email": identity.can_send_email,
                        "display_name": identity.display_name,
                    }
            except Exception as e:
                logger.warning(f"Failed to get identity from manager: {e}")
        
        # Try Firebase store
        firebase_store = self._get_firebase_store()
        if firebase_store and firebase_store.available:
            try:
                identity_data = await firebase_store.get_identity(user_id)
                if identity_data:
                    return {
                        "email": identity_data.get("email"),
                        "auth_type": identity_data.get("auth_type", "oauth"),
                        "display_name": identity_data.get("display_name", "AI Assistant"),
                        "can_send_email": True,
                    }
            except Exception as e:
                logger.warning(f"Failed to get identity from Firebase: {e}")
        
        # Try OAuth manager for Gmail token
        oauth_manager = self._get_oauth_manager()
        if oauth_manager:
            try:
                from .oauth_manager import OAuthService
                token = await oauth_manager.get_valid_token(user_id, OAuthService.GMAIL)
                if token and token.access_token:
                    return {
                        "email": token.user_email,
                        "auth_type": "oauth",
                        "access_token": token.access_token,
                        "refresh_token": token.refresh_token,
                        "can_send_email": True,
                    }
            except Exception as e:
                logger.warning(f"Failed to get OAuth token: {e}")
        
        return None
    
    async def send_email_for_user(
        self,
        user_id: str,
        to: str,
        subject: str,
        body: str,
        html_body: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send email using the user's stored credentials.
        Falls back to environment OAuth if user has no credentials.
        
        Args:
            user_id: User identifier
            to: Recipient email
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            **kwargs: Additional parameters
            
        Returns:
            Result dict with status, message, etc.
        """
        # Get user credentials
        credentials = await self.get_user_email_credentials(user_id)
        
        # If no user credentials, try environment OAuth directly
        if not credentials:
            logger.info(f"No user credentials for {user_id}, using env OAuth")
            return await self._send_via_env_oauth(
                sender_email="",
                to=to,
                subject=subject,
                body=body,
                html_body=html_body,
                **kwargs
            )
        
        if not credentials.get("can_send_email", True):
            return {
                "status": "failed", 
                "error": "Email sending is not enabled for this identity.",
            }
        
        auth_type = credentials.get("auth_type", "")
        sender_email = credentials.get("email", "")
        
        # Send based on auth type
        if auth_type == "oauth" and credentials.get("access_token"):
            return await self._send_via_oauth(
                credentials, to, subject, body, html_body, **kwargs
            )
        elif credentials.get("password"):
            return await self._send_via_smtp(
                credentials, to, subject, body, html_body, **kwargs
            )
        else:
            # Try falling back to env-based OAuth
            return await self._send_via_env_oauth(
                sender_email, to, subject, body, html_body, **kwargs
            )
    
    async def _send_via_oauth(
        self,
        credentials: Dict[str, Any],
        to: str,
        subject: str,
        body: str,
        html_body: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send email using OAuth credentials"""
        if not GOOGLE_API_AVAILABLE:
            return {
                "status": "failed",
                "error": "Google API not available. Install: pip install google-auth google-api-python-client",
            }
        
        try:
            # Build credentials
            from google.oauth2.credentials import Credentials
            
            creds = Credentials(
                token=credentials.get("access_token"),
                refresh_token=credentials.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GMAIL_CLIENT_ID", ""),
                client_secret=os.getenv("GMAIL_CLIENT_SECRET", ""),
            )
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds)
            
            # Create message
            message = self._create_message(
                credentials.get("email", ""),
                to, 
                subject, 
                body, 
                html_body,
                credentials.get("display_name", "AI Assistant")
            )
            
            # Encode for Gmail API
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send
            result = service.users().messages().send(
                userId='me',
                body={'raw': encoded_message}
            ).execute()
            
            email_id = result.get('id', '')
            
            logger.info(f"Email sent via user OAuth to {to}, ID: {email_id}")
            
            return {
                "status": "completed",
                "result": f"Email sent successfully to {to}",
                "email_id": email_id,
                "method": "user_oauth",
                "from": credentials.get("email"),
            }
            
        except HttpError as e:
            error_msg = f"Gmail API error: {e.reason if hasattr(e, 'reason') else str(e)}"
            logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
                "method": "user_oauth",
            }
        except Exception as e:
            logger.error(f"OAuth send error: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "method": "user_oauth",
            }
    
    async def _send_via_smtp(
        self,
        credentials: Dict[str, Any],
        to: str,
        subject: str,
        body: str,
        html_body: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send email using SMTP with app password"""
        import smtplib
        
        try:
            sender_email = credentials.get("email", "")
            password = credentials.get("password", "")
            display_name = credentials.get("display_name", "AI Assistant")
            
            message = self._create_message(
                sender_email, to, subject, body, html_body, display_name
            )
            
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, password)
                server.send_message(message)
            
            logger.info(f"Email sent via user SMTP to {to}")
            
            return {
                "status": "completed",
                "result": f"Email sent successfully to {to}",
                "method": "user_smtp",
                "from": sender_email,
            }
            
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "method": "user_smtp",
            }
    
    async def _send_via_env_oauth(
        self,
        sender_email: str,
        to: str,
        subject: str,
        body: str,
        html_body: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Fallback to environment-based OAuth, then SMTP"""
        refresh_token = os.getenv("GMAIL_REFRESH_TOKEN", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "") or os.getenv("GMAIL_APP_PASSWORD", "")
        
        # Try OAuth first
        if GOOGLE_API_AVAILABLE and refresh_token:
            try:
                creds = Credentials(
                    token=None,
                    refresh_token=refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=os.getenv("GMAIL_CLIENT_ID", ""),
                    client_secret=os.getenv("GMAIL_CLIENT_SECRET", ""),
                )
                
                # Refresh token
                creds.refresh(Request())
                
                service = build('gmail', 'v1', credentials=creds)
                
                env_email = os.getenv("GMAIL_USER", sender_email) or os.getenv("SMTP_EMAIL", "")
                message = self._create_message(
                    env_email, to, subject, body, html_body, "AI Assistant"
                )
                
                encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                
                result = service.users().messages().send(
                    userId='me',
                    body={'raw': encoded_message}
                ).execute()
                
                return {
                    "status": "completed",
                    "result": f"Email sent to {to}",
                    "email_id": result.get('id', ''),
                    "method": "env_oauth",
                    "from": env_email,
                }
                
            except Exception as e:
                logger.warning(f"OAuth failed, trying SMTP: {e}")
        
        # Try SMTP fallback
        if smtp_password:
            try:
                import smtplib
                smtp_email = os.getenv("SMTP_EMAIL", "") or os.getenv("GMAIL_USER", "")
                smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
                smtp_port = int(os.getenv("SMTP_PORT", "587"))
                
                message = self._create_message(
                    smtp_email, to, subject, body, html_body, "AI Assistant"
                )
                
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_email, smtp_password)
                    server.send_message(message)
                
                return {
                    "status": "completed",
                    "result": f"Email sent to {to}",
                    "method": "env_smtp",
                    "from": smtp_email,
                }
            except Exception as e:
                logger.error(f"SMTP also failed: {e}")
                return {
                    "status": "failed",
                    "error": f"Both OAuth and SMTP failed: {str(e)}",
                    "setup_required": True,
                }
        
        return {
            "status": "failed",
            "error": "No working email credentials. OAuth token may be expired. Run 'python scripts/get_gmail_refresh_token.py' to get a new token.",
            "setup_required": True,
        }
    
    def _create_message(
        self,
        sender: str,
        to: str,
        subject: str,
        body: str,
        html_body: str = None,
        display_name: str = "AI Assistant"
    ) -> MIMEMultipart:
        """Create email message"""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{display_name} <{sender}>"
        message["To"] = to
        message["Reply-To"] = sender
        
        # Plain text
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        # HTML
        if html_body:
            message.attach(MIMEText(html_body, "html", "utf-8"))
        
        return message


# Global instance
_identity_email_service: Optional[IdentityEmailService] = None


def get_identity_email_service() -> IdentityEmailService:
    """Get the global identity email service"""
    global _identity_email_service
    
    if _identity_email_service is None:
        _identity_email_service = IdentityEmailService()
    
    return _identity_email_service


# =============================================================================
# Enhanced Plugin Integration
# =============================================================================

class IdentityAwareEmailPlugin:
    """
    Email plugin that uses AIIdentity for credentials.
    
    This wraps the GmailOAuthPlugin with identity-aware sending.
    """
    
    def __init__(self):
        self.name = "email"
        self.description = "Identity-aware email operations"
        self.enabled = True
        self.email_service = get_identity_email_service()
        
        # Fall back to standard plugin for non-user-specific operations
        try:
            from .gmail_oauth_plugin import GmailOAuthPlugin
            self.fallback_plugin = GmailOAuthPlugin()
        except:
            self.fallback_plugin = None
    
    async def execute(self, step: Dict, state: Dict) -> Dict[str, Any]:
        """Execute email action"""
        action = step.get("action", "").lower()
        parameters = step.get("parameters", {})
        
        # Get user_id from state if available
        user_id = state.get("user_id") or parameters.get("user_id")
        
        if "send" in action or "invite" in action:
            if user_id:
                # Use identity-aware sending
                return await self.email_service.send_email_for_user(
                    user_id=user_id,
                    to=parameters.get("to", ""),
                    subject=parameters.get("subject", ""),
                    body=parameters.get("body", parameters.get("message", "")),
                    html_body=parameters.get("html_body"),
                    meeting_link=parameters.get("meeting_link"),
                    topic=parameters.get("topic"),
                )
            elif self.fallback_plugin:
                # Use standard plugin
                return await self.fallback_plugin.execute(step, state)
            else:
                return {"status": "failed", "error": "No email plugin available"}
        
        # For other actions, use fallback
        if self.fallback_plugin:
            return await self.fallback_plugin.execute(step, state)
        
        return {"status": "failed", "error": f"Unknown action: {action}"}
    
    def get_capabilities(self) -> list:
        return ["email", "send_email", "send_invitation"]
