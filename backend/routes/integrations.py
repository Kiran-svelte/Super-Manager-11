"""
Integration Manager Routes
===========================
The bridge between AI intelligence and real-world execution.

Provides:
- /api/integrations/ — List connected + available services
- /api/integrations/connect — Initiate OAuth flow for a service
- /api/integrations/callback — Handle OAuth callback
- /api/integrations/{id} — Revoke an integration
- /api/integrations/status/{service} — Check integration health

Design principles:
1. Never over-ask — only prompt connection when a task needs it
2. Always fallback — if API unavailable, try browser automation → user input
3. User controls permissions — view/revoke anytime
4. Security > Convenience — tokens encrypted, auto-refresh, auto-revoke
5. Reuse silently — after first connect, use stored token automatically
"""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import logging
import os
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])

# Try to import OAuth manager for actual OAuth flows
try:
    from ..core.oauth_manager import get_oauth_manager, OAuthService
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    get_oauth_manager = None
    OAuthService = None

# Try to import encryption for token storage
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# ============================================================================= 
# Integration Store (Supabase backed)
# ============================================================================= 

from ..core.integration_manager.integration_store import integration_store

def get_integration_store():
    return integration_store

# =============================================================================
# Fallback Router
# =============================================================================

class FallbackRouter:
    """
    Routes tasks to fallback methods when API integration is unavailable.
    
    Priority:
    1. API (OAuth integration) — fastest, most reliable
    2. Browser Automation — Playwright-based
    3. User Input — ask user to perform manually
    4. Partial Assist — provide instructions
    """
    
    FALLBACK_MATRIX = {
        "google_calendar": {
            "api": "Google Calendar API",
            "fallback_1": "Browser automation (open calendar.google.com)",
            "fallback_2": "Ask user to create event manually",
            "last_resort": "Provide step-by-step instructions"
        },
        "gmail": {
            "api": "Gmail OAuth API",
            "fallback_1": "SMTP direct send",
            "fallback_2": "Browser automation",
            "last_resort": "Draft email for user to copy"
        },
        "razorpay": {
            "api": "Razorpay API",
            "fallback_1": "Generate UPI link",
            "fallback_2": "Browser checkout",
            "last_resort": "Share payment details for manual transfer"
        },
        "github": {
            "api": "GitHub API",
            "fallback_1": "Browser automation",
            "fallback_2": "CLI commands",
            "last_resort": "Provide instructions"
        }
    }
    
    @classmethod
    def get_fallback_route(cls, service: str, is_connected: bool) -> Dict:
        """Get the recommended route for a given service"""
        fallback_info = cls.FALLBACK_MATRIX.get(service, {
            "api": f"{service} API",
            "fallback_1": "Browser automation",
            "fallback_2": "Ask user",
            "last_resort": "Provide instructions"
        })
        
        if is_connected:
            return {
                "route": "api",
                "method": fallback_info["api"],
                "message": f"Using {service} API (connected)"
            }
        else:
            return {
                "route": "fallback",
                "method": fallback_info["fallback_1"],
                "alternatives": [
                    fallback_info["fallback_2"],
                    fallback_info["last_resort"]
                ],
                "message": f"{service} not connected. Using fallback: {fallback_info['fallback_1']}"
            }


# =============================================================================
# Request/Response Models
# =============================================================================

class ConnectRequest(BaseModel):
    """Request to initiate an integration connection"""
    user_id: str = Field(..., min_length=1, max_length=100)
    service: str = Field(..., min_length=1, max_length=100)
    scopes: Optional[List[str]] = None


class IntegrationResponse(BaseModel):
    """Standard integration response"""
    status: str
    message: str
    data: Optional[Dict] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/")
async def list_integrations(
    user_id: str = Query(..., description="User identifier")
):
    """
    List all connected and available integrations for a user.
    
    Returns:
    - connected: list of active integrations with manage/revoke options
    - available: list of services that can be connected
    - security: encryption info
    """
    store = get_integration_store()
    
    connected = store.get_user_integrations(user_id)
    available = store.get_available_integrations(user_id)
    
    return {
        "user_id": user_id,
        "connected": connected,
        "connected_count": len(connected),
        "available": available,
        "available_count": len(available),
        "security": {
            "encryption": "AES-256-GCM" if CRYPTO_AVAILABLE else "development-mode",
            "token_storage": "encrypted",
            "user_revocable": True,
            "message": "Your tokens are encrypted with AES-256. You can revoke anytime."
        }
    }


@router.post("/connect")
async def connect_integration(request: ConnectRequest):
    """
    Initiate integration connection.
    
    For OAuth-based services: returns authorization URL
    For API-key services: stores the key securely
    
    Critical Rules Applied:
    - Only asks when a specific task needs it
    - Uses OAuth (never raw API keys from users)
    - Stores tokens encrypted
    """
    store = get_integration_store()
    
    # Check if service is valid
    if request.service not in store.AVAILABLE_INTEGRATIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Unknown service: {request.service}",
                "available_services": list(store.AVAILABLE_INTEGRATIONS.keys())
            }
        )
    
    # Check if already connected
    if store.is_connected(request.user_id, request.service):
        return {
            "status": "already_connected",
            "message": f"{request.service} is already connected. Use it directly.",
            "service": request.service
        }
    
    # Try OAuth flow if available
    if OAUTH_AVAILABLE and get_oauth_manager:
        try:
            # Map our service names to OAuthService enum values
            oauth_service_map = {
                "gmail": "gmail",
                "google_calendar": "gmail",  # Same Google OAuth, different scopes
                "google_drive": "gmail",
                "github": "github",
            }
            
            oauth_service_name = oauth_service_map.get(request.service)
            if oauth_service_name:
                oauth_service = OAuthService(oauth_service_name)
                manager = get_oauth_manager()
                auth_url, state = manager.get_authorization_url(
                    user_id=request.user_id,
                    service=oauth_service,
                    extra_scopes=request.scopes,
                )
                return {
                    "status": "oauth_required",
                    "message": f"Connect your {store.AVAILABLE_INTEGRATIONS[request.service]['name']} to proceed",
                    "oauth_url": auth_url,
                    "state": state,
                    "service": request.service,
                    "instructions": "Click the link to authorize access via OAuth"
                }
        except Exception as e:
            logger.warning(f"OAuth flow failed for {request.service}: {e}")
    
    # Fallback: store as pending (user needs to configure)
    store.connect_integration(
        user_id=request.user_id,
        service=request.service,
        access_token=None,
        scopes=request.scopes or store.AVAILABLE_INTEGRATIONS[request.service].get("scopes", []),
    )
    
    return {
        "status": "pending_setup",
        "message": f"{request.service} integration registered. OAuth configuration needed.",
        "service": request.service,
        "setup_required": True,
        "fallback": FallbackRouter.get_fallback_route(request.service, False)
    }


@router.post("/callback")
async def integration_callback(
    service: str = Query(...),
    user_id: str = Query(...),
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
):
    """
    Handle OAuth callback for integration connection.
    
    After user authorizes on the provider's page, they're redirected here.
    We exchange the code for tokens and store them encrypted.
    """
    if error:
        raise HTTPException(
            status_code=400,
            detail={"error": f"OAuth error: {error}", "service": service}
        )
    
    store = get_integration_store()
    
    if OAUTH_AVAILABLE and get_oauth_manager and code:
        try:
            manager = get_oauth_manager()
            token = await manager.exchange_code(state, code)
            
            if token:
                store.connect_integration(
                    user_id=user_id,
                    service=service,
                    access_token=token.access_token if hasattr(token, 'access_token') else str(token),
                    refresh_token=token.refresh_token if hasattr(token, 'refresh_token') else None,
                    scopes=token.scopes if hasattr(token, 'scopes') else [],
                    expires_at=token.expires_at.isoformat() if hasattr(token, 'expires_at') and token.expires_at else None,
                )
                
                return {
                    "status": "connected",
                    "message": f"{service} successfully connected!",
                    "service": service,
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Integration callback error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    raise HTTPException(status_code=400, detail="Missing authorization code")


@router.delete("/{integration_id}")
async def revoke_integration(
    integration_id: str,
    user_id: str = Query(..., description="User identifier")
):
    """
    Revoke an integration.
    
    Deletes the stored tokens and disconnects the service.
    User can reconnect anytime.
    """
    store = get_integration_store()
    success = store.revoke_integration(user_id, integration_id)
    
    if success:
        return {
            "status": "revoked",
            "message": "Integration revoked successfully. Tokens deleted.",
            "revoked": True
        }
    else:
        raise HTTPException(
            status_code=404,
            detail="Integration not found"
        )


@router.delete("/service/{service_name}")
async def revoke_integration_by_service(
    service_name: str,
    user_id: str = Query(..., description="User identifier")
):
    """Revoke integration by service name (convenience endpoint)"""
    store = get_integration_store()
    success = store.revoke_by_service(user_id, service_name)
    
    if success:
        return {"status": "revoked", "service": service_name, "revoked": True}
    else:
        raise HTTPException(status_code=404, detail=f"No active {service_name} integration found")


@router.get("/status/{service}")
async def check_integration_status(
    service: str,
    user_id: str = Query(..., description="User identifier")
):
    """
    Check health and status of a specific integration.
    
    Returns:
    - connected: whether the service is connected
    - healthy: whether the token is valid and not expired
    - fallback: recommended route if not connected
    """
    store = get_integration_store()
    health = store.check_health(user_id, service)
    
    # Add fallback route info
    health["fallback"] = FallbackRouter.get_fallback_route(
        service, health["connected"]
    )
    
    return health


@router.get("/check-needs")
async def check_integration_needs(
    user_id: str = Query(...),
    task_type: str = Query(..., description="Type of task (e.g., send_email, schedule_meeting)")
):
    """
    Check what integrations are needed for a specific task type.
    
    Used by the AI agent before executing a task to determine
    if integrations need to be connected.
    
    Applies Rule 1: Ask only when a specific task needs it.
    """
    store = get_integration_store()
    
    # Map task types to required integrations
    TASK_INTEGRATION_MAP = {
        "send_email": ["gmail", "outlook"],
        "schedule_meeting": ["google_calendar"],
        "read_email": ["gmail", "outlook"],
        "share_file": ["google_drive"],
        "send_message": ["slack"],
        "create_issue": ["github"],
        "manage_project": ["trello"],
        "create_payment": ["razorpay", "stripe"],
    }
    
    needed_services = TASK_INTEGRATION_MAP.get(task_type, [])
    
    results = []
    any_connected = False
    
    for service in needed_services:
        is_connected = store.is_connected(user_id, service)
        if is_connected:
            any_connected = True
        
        service_info = store.AVAILABLE_INTEGRATIONS.get(service, {})
        results.append({
            "service": service,
            "name": service_info.get("name", service),
            "connected": is_connected,
            "fallback": FallbackRouter.get_fallback_route(service, is_connected)
        })
    
    return {
        "task_type": task_type,
        "needs_integration": len(needed_services) > 0,
        "any_connected": any_connected,
        "required_services": results,
        "recommendation": (
            "All required services connected. Proceed with API route."
            if any_connected
            else f"No integration connected for {task_type}. Will use fallback strategy."
        )
    }


@router.get("/fallback-matrix")
async def get_fallback_matrix():
    """
    Get the complete fallback matrix.
    
    Shows what happens when each integration is unavailable:
    API → Browser Automation → User Input → Partial Assist
    """
    return {
        "matrix": FallbackRouter.FALLBACK_MATRIX,
        "priority_order": [
            "1. API (OAuth integration) — fastest, most reliable",
            "2. Browser Automation (Playwright) — works without API",
            "3. User Input — ask user to perform manually",
            "4. Partial Assist — provide step-by-step instructions"
        ],
        "rules": {
            "rule_1": "Never over-ask: only prompt connection when task requires it",
            "rule_2": "Never stop: always provide a fallback path",
            "rule_3": "User controls: view/revoke permissions anytime",
            "rule_4": "Security first: encrypt all tokens, auto-refresh",
            "rule_5": "Reuse silently: after first connect, no repeated asks"
        }
    }
