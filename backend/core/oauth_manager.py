"""
OAuth Manager - Multi-Service OAuth 2.0 Management
=====================================================
Handles OAuth flows for multiple services:
- Gmail (reading and sending emails)
- Zoom (meeting creation)
- Google Calendar
- Google Drive
- And more...

This module provides:
1. OAuth flow initiation and callback handling
2. Token storage and refresh
3. Per-user credential management
4. Integration with Firebase for token persistence

Author: Super Manager AI
"""

import os
import json
import asyncio
import logging
import secrets
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from urllib.parse import urlencode, parse_qs, urlparse
from enum import Enum

import httpx

# Load .env from backend directory
try:
    from dotenv import load_dotenv
    backend_env = Path(__file__).parent.parent / ".env"
    if backend_env.exists():
        load_dotenv(backend_env, override=True)
except ImportError:
    pass

logger = logging.getLogger(__name__)


class OAuthService(Enum):
    """Supported OAuth services"""
    GMAIL = "gmail"
    GOOGLE_CALENDAR = "google_calendar"
    GOOGLE_DRIVE = "google_drive"
    ZOOM = "zoom"
    MICROSOFT = "microsoft"
    SLACK = "slack"


@dataclass
class OAuthConfig:
    """OAuth configuration for a service"""
    service: OAuthService
    client_id: str
    client_secret: str
    auth_url: str
    token_url: str
    scopes: List[str]
    redirect_uri: str = ""
    
    @classmethod
    def gmail(cls) -> 'OAuthConfig':
        """Gmail/Google OAuth configuration"""
        return cls(
            service=OAuthService.GMAIL,
            client_id=os.getenv("GMAIL_CLIENT_ID", ""),
            client_secret=os.getenv("GMAIL_CLIENT_SECRET", ""),
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=[
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.modify",
            ],
            redirect_uri=os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/api/oauth/callback"),
        )
    
    @classmethod
    def google_full(cls) -> 'OAuthConfig':
        """Full Google OAuth (Gmail + Calendar + Drive)"""
        return cls(
            service=OAuthService.GOOGLE_CALENDAR,
            client_id=os.getenv("GMAIL_CLIENT_ID", ""),
            client_secret=os.getenv("GMAIL_CLIENT_SECRET", ""),
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=[
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/calendar.events",
                "https://www.googleapis.com/auth/drive.file",
            ],
            redirect_uri=os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/api/oauth/callback"),
        )
    
    @classmethod
    def zoom(cls) -> 'OAuthConfig':
        """Zoom OAuth configuration"""
        return cls(
            service=OAuthService.ZOOM,
            client_id=os.getenv("ZOOM_CLIENT_ID", ""),
            client_secret=os.getenv("ZOOM_CLIENT_SECRET", ""),
            auth_url="https://zoom.us/oauth/authorize",
            token_url="https://zoom.us/oauth/token",
            scopes=["meeting:write", "user:read"],
            redirect_uri=os.getenv("ZOOM_REDIRECT_URI", "http://localhost:8000/api/oauth/zoom/callback"),
        )


@dataclass
class OAuthToken:
    """OAuth token with metadata"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    scopes: List[str] = field(default_factory=list)
    service: str = ""
    user_email: str = ""
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scopes": self.scopes,
            "service": self.service,
            "user_email": self.user_email,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OAuthToken':
        """Create from dictionary"""
        expires_at = None
        if data.get("expires_at"):
            try:
                expires_at = datetime.fromisoformat(data["expires_at"])
            except:
                pass
        
        return cls(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scopes=data.get("scopes", []),
            service=data.get("service", ""),
            user_email=data.get("user_email", ""),
        )


class OAuthManager:
    """
    Manages OAuth flows and tokens for multiple services.
    
    Usage:
        manager = OAuthManager()
        
        # Start OAuth flow
        auth_url, state = manager.get_authorization_url("user123", OAuthService.GMAIL)
        
        # After callback with code
        token = await manager.exchange_code(state, code)
        
        # Use token
        valid_token = await manager.get_valid_token("user123", OAuthService.GMAIL)
    """
    
    def __init__(self):
        # Pending OAuth states (state -> user_id mapping)
        self._pending_states: Dict[str, Dict[str, Any]] = {}
        
        # Token cache (user_id -> service -> token)
        self._token_cache: Dict[str, Dict[str, OAuthToken]] = {}
        
        # Firebase store for persistence
        self._firebase_store = None
        
    def _get_firebase_store(self):
        """Lazy load Firebase store"""
        if self._firebase_store is None:
            try:
                from .firebase_config import get_firebase_identity_store
                self._firebase_store = get_firebase_identity_store()
            except ImportError:
                logger.warning("Firebase not available for OAuth token storage")
        return self._firebase_store
    
    def get_config(self, service: OAuthService) -> OAuthConfig:
        """Get OAuth configuration for a service"""
        configs = {
            OAuthService.GMAIL: OAuthConfig.gmail,
            OAuthService.GOOGLE_CALENDAR: OAuthConfig.google_full,
            OAuthService.GOOGLE_DRIVE: OAuthConfig.google_full,
            OAuthService.ZOOM: OAuthConfig.zoom,
        }
        
        config_factory = configs.get(service)
        if config_factory:
            return config_factory()
        
        raise ValueError(f"Unsupported OAuth service: {service}")
    
    def get_authorization_url(
        self,
        user_id: str,
        service: OAuthService,
        extra_scopes: List[str] = None,
        override_redirect_uri: str = None
    ) -> Tuple[str, str]:
        """
        Get OAuth authorization URL.
        
        Args:
            user_id: User identifier
            service: OAuth service
            extra_scopes: Additional scopes to request
            override_redirect_uri: Optional dynamic redirect URI from request
            
        Returns:
            Tuple of (authorization_url, state)
        """
        config = self.get_config(service)
        
        # Generate secure state
        state = secrets.token_urlsafe(32)
        
        # Store state mapping
        self._pending_states[state] = {
            "user_id": user_id,
            "service": service.value,
            "created_at": datetime.utcnow().isoformat(),
            "redirect_uri": redirect_uri,
        }
        
        # Build scopes
        scopes = config.scopes.copy()
        if extra_scopes:
            scopes.extend(extra_scopes)
            
        # Determine redirect URI dynamically if possible
        redirect_uri = override_redirect_uri or config.redirect_uri
        
        # Build authorization URL
        params = {
            "client_id": config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent to get refresh token
        }
        
        auth_url = f"{config.auth_url}?{urlencode(params)}"
        
        logger.info(f"Generated OAuth URL for user {user_id}, service {service.value}")
        return auth_url, state
    
    async def exchange_code(
        self,
        state: str,
        code: str
    ) -> Optional[OAuthToken]:
        """
        Exchange authorization code for tokens.
        
        Args:
            state: OAuth state from callback
            code: Authorization code from callback
            
        Returns:
            OAuthToken or None if failed
        """
        # Validate state
        state_data = self._pending_states.pop(state, None)
        if not state_data:
            logger.error("Invalid or expired OAuth state")
            return None
        
        user_id = state_data["user_id"]
        service = OAuthService(state_data["service"])
        redirect_uri = state_data.get("redirect_uri")
        config = self.get_config(service)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config.token_url,
                    data={
                        "client_id": config.client_id,
                        "client_secret": config.client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri or config.redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    headers={"Accept": "application/json"},
                )
                
                if response.status_code != 200:
                    logger.error(f"Token exchange failed: {response.text}")
                    return None
                
                data = response.json()
                
                # Calculate expiry
                expires_in = data.get("expires_in", 3600)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                # Create token
                token = OAuthToken(
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token", ""),
                    token_type=data.get("token_type", "Bearer"),
                    expires_at=expires_at,
                    scopes=data.get("scope", "").split(" "),
                    service=service.value,
                )
                
                # Get user email (for Google)
                if service in [OAuthService.GMAIL, OAuthService.GOOGLE_CALENDAR]:
                    email = await self._get_google_user_email(token.access_token)
                    token.user_email = email or ""
                
                # Save token
                await self._save_token(user_id, service, token)
                
                logger.info(f"OAuth tokens obtained for user {user_id}, service {service.value}")
                return token
                
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None
    
    async def refresh_token(
        self,
        user_id: str,
        service: OAuthService
    ) -> Optional[OAuthToken]:
        """
        Refresh an expired token.
        
        Args:
            user_id: User identifier
            service: OAuth service
            
        Returns:
            Refreshed OAuthToken or None
        """
        token = await self._get_stored_token(user_id, service)
        if not token or not token.refresh_token:
            logger.error("No refresh token available")
            return None
        
        config = self.get_config(service)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config.token_url,
                    data={
                        "client_id": config.client_id,
                        "client_secret": config.client_secret,
                        "refresh_token": token.refresh_token,
                        "grant_type": "refresh_token",
                    },
                    headers={"Accept": "application/json"},
                )
                
                if response.status_code != 200:
                    logger.error(f"Token refresh failed: {response.text}")
                    return None
                
                data = response.json()
                
                # Update token
                expires_in = data.get("expires_in", 3600)
                token.access_token = data["access_token"]
                token.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                # Some services return a new refresh token
                if "refresh_token" in data:
                    token.refresh_token = data["refresh_token"]
                
                # Save updated token
                await self._save_token(user_id, service, token)
                
                logger.info(f"Token refreshed for user {user_id}, service {service.value}")
                return token
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    async def get_valid_token(
        self,
        user_id: str,
        service: OAuthService
    ) -> Optional[OAuthToken]:
        """
        Get a valid (non-expired) token, refreshing if necessary.
        
        Args:
            user_id: User identifier
            service: OAuth service
            
        Returns:
            Valid OAuthToken or None
        """
        token = await self._get_stored_token(user_id, service)
        
        if not token:
            return None
        
        # Refresh if expired or about to expire (within 5 minutes)
        if token.expires_at:
            margin = timedelta(minutes=5)
            if datetime.utcnow() >= (token.expires_at - margin):
                token = await self.refresh_token(user_id, service)
        
        return token
    
    async def revoke_token(
        self,
        user_id: str,
        service: OAuthService
    ) -> bool:
        """
        Revoke OAuth token for a service.
        
        Args:
            user_id: User identifier
            service: OAuth service
            
        Returns:
            True if successful
        """
        token = await self._get_stored_token(user_id, service)
        
        if not token:
            return True
        
        # Revoke with provider (optional - just delete locally for now)
        try:
            if service in [OAuthService.GMAIL, OAuthService.GOOGLE_CALENDAR]:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        "https://oauth2.googleapis.com/revoke",
                        params={"token": token.access_token},
                    )
        except:
            pass
        
        # Delete locally
        await self._delete_token(user_id, service)
        
        logger.info(f"Revoked {service.value} token for user {user_id}")
        return True
    
    async def _save_token(
        self,
        user_id: str,
        service: OAuthService,
        token: OAuthToken
    ):
        """Save token to cache and persistent storage"""
        # Update cache
        if user_id not in self._token_cache:
            self._token_cache[user_id] = {}
        self._token_cache[user_id][service.value] = token
        
        # Save to Firebase
        store = self._get_firebase_store()
        if store and store.available:
            await store.save_oauth_token(user_id, service.value, token.to_dict())
    
    async def _get_stored_token(
        self,
        user_id: str,
        service: OAuthService
    ) -> Optional[OAuthToken]:
        """Get token from cache or persistent storage"""
        # Check cache
        if user_id in self._token_cache:
            if service.value in self._token_cache[user_id]:
                return self._token_cache[user_id][service.value]
        
        # Try Firebase
        store = self._get_firebase_store()
        if store and store.available:
            data = await store.get_oauth_token(user_id, service.value)
            if data:
                token = OAuthToken.from_dict(data)
                # Update cache
                if user_id not in self._token_cache:
                    self._token_cache[user_id] = {}
                self._token_cache[user_id][service.value] = token
                return token
        
        return None
    
    async def _delete_token(
        self,
        user_id: str,
        service: OAuthService
    ):
        """Delete token from cache and storage"""
        # Remove from cache
        if user_id in self._token_cache:
            self._token_cache[user_id].pop(service.value, None)
        
        # Remove from Firebase
        store = self._get_firebase_store()
        if store and store.available:
            await store.delete_oauth_token(user_id, service.value)
    
    async def _get_google_user_email(self, access_token: str) -> Optional[str]:
        """Get Google user email from access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                
                if response.status_code == 200:
                    return response.json().get("email")
        except:
            pass
        return None
    
    def get_pending_states_count(self) -> int:
        """Get count of pending OAuth states"""
        # Clean expired states (older than 10 minutes)
        cutoff = datetime.utcnow() - timedelta(minutes=10)
        self._pending_states = {
            k: v for k, v in self._pending_states.items()
            if datetime.fromisoformat(v["created_at"]) > cutoff
        }
        return len(self._pending_states)


# Global OAuth manager instance
_oauth_manager: Optional[OAuthManager] = None


def get_oauth_manager() -> OAuthManager:
    """Get the global OAuth manager instance"""
    global _oauth_manager
    
    if _oauth_manager is None:
        _oauth_manager = OAuthManager()
    
    return _oauth_manager
