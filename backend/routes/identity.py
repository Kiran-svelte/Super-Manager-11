"""
AI Identity API Routes
=======================
Endpoints for managing the AI's digital identity:
- Setup AI email (Gmail)
- Verify credentials
- Manage service accounts
- Handle sensitive data requests
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ..agent.identity import (
    get_identity_manager, 
    AIIdentity, 
    AuthType, 
    IdentityStatus,
    ResponsibleAI,
    SensitiveDataHandler
)
from ..agent.service_signup import ServiceSignup, ServiceRegistry
from ..agent.browser_automation import ServiceSignupAutomation
from ..agent.gmail_reader import get_gmail_reader

router = APIRouter(prefix="/api/identity", tags=["AI Identity"])


# =============================================================================
# REQUEST MODELS
# =============================================================================

class SetupIdentityRequest(BaseModel):
    """Request to set up AI identity"""
    user_id: str
    email: str = Field(..., description="Gmail address for the AI")
    app_password: str = Field(..., description="Gmail App Password (not regular password)")
    display_name: Optional[str] = "AI Assistant"


class StoreServiceAccountRequest(BaseModel):
    """Request to store a service account"""
    user_id: str
    service_name: str
    api_key: str
    api_secret: Optional[str] = None
    account_email: Optional[str] = None
    account_username: Optional[str] = None


class SensitiveDataRequest(BaseModel):
    """Request for sensitive data from user"""
    user_id: str
    request_id: str
    data: str  # OTP, PAN, etc.


class SignupServiceRequest(BaseModel):
    """Request to sign up for a service"""
    user_id: str
    service_name: str


# =============================================================================
# IDENTITY ENDPOINTS
# =============================================================================

@router.post("/setup")
async def setup_ai_identity(request: SetupIdentityRequest):
    """
    Set up the AI's email identity.
    
    User must:
    1. Create a new Gmail account for the AI
    2. Enable 2-Step Verification
    3. Create an App Password
    4. Provide the App Password here
    
    Returns setup status and capabilities unlocked.
    """
    manager = get_identity_manager()
    
    identity, message = await manager.create_identity(
        user_id=request.user_id,
        email=request.email,
        password=request.app_password,
        display_name=request.display_name,
        auth_type=AuthType.APP_PASSWORD
    )
    
    if not identity:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "identity": {
            "email": identity.email,
            "display_name": identity.display_name,
            "status": identity.status.value,
            "capabilities": {
                "can_send_email": identity.can_send_email,
                "can_read_email": identity.can_read_email,
                "can_signup_services": identity.can_signup_services
            }
        }
    }


@router.get("/status/{user_id}")
async def get_identity_status(user_id: str):
    """Get the status of user's AI identity"""
    
    manager = get_identity_manager()
    identity = await manager.get_identity(user_id)
    
    if not identity:
        return {
            "has_identity": False,
            "message": "No AI identity set up. Create a Gmail for your AI first."
        }
    
    return {
        "has_identity": True,
        "email": identity.email,
        "display_name": identity.display_name,
        "status": identity.status.value,
        "capabilities": {
            "can_send_email": identity.can_send_email,
            "can_read_email": identity.can_read_email,
            "can_signup_services": identity.can_signup_services
        }
    }


@router.post("/verify")
async def verify_identity(user_id: str):
    """Verify that the AI identity credentials still work"""
    
    manager = get_identity_manager()
    gmail = await manager.get_gmail_manager(user_id)
    
    if not gmail:
        raise HTTPException(status_code=404, detail="No AI identity found")
    
    success, message = await gmail.verify_credentials()
    
    return {
        "success": success,
        "message": message
    }


# =============================================================================
# SERVICE ACCOUNT ENDPOINTS
# =============================================================================

@router.post("/services/signup")
async def signup_for_service(request: SignupServiceRequest, background_tasks: BackgroundTasks):
    """
    Initiate signup for an online service using browser automation.
    
    This endpoint:
    1. Checks if the service is blocked
    2. Uses browser automation to sign up
    3. Waits for verification emails
    4. Extracts and stores API keys
    
    Supported services: groq, together, huggingface, openrouter
    """
    
    # Check if service is blocked
    blocked, reason = ServiceRegistry.is_blocked(request.service_name)
    if blocked:
        # Get alternatives
        service_info = ServiceRegistry.get_service_info(request.service_name)
        return {
            "success": False,
            "blocked": True,
            "reason": reason,
            "alternatives": ServiceRegistry.get_service_for_task(
                service_info.get("category") if service_info else "general"
            )
        }
    
    # Get AI identity
    manager = get_identity_manager()
    identity = await manager.get_identity(request.user_id)
    
    if not identity:
        raise HTTPException(
            status_code=400, 
            detail="Set up AI identity first before signing up for services"
        )
    
    # Check if service is supported for automated signup
    automation = ServiceSignupAutomation(identity.email)
    available_services = automation.get_available_services()
    
    if request.service_name.lower() not in available_services:
        return {
            "success": False,
            "service": request.service_name,
            "message": f"Automated signup not yet available for {request.service_name}. Available: {', '.join(available_services)}",
            "available_services": available_services
        }
    
    # Run signup automation
    result = await automation.signup(request.service_name, request.user_id)
    
    # Store API key if obtained
    if result.success and result.api_key:
        signup = ServiceSignup(identity.email, "")
        await signup.store_service_account(
            user_id=request.user_id,
            ai_identity_id=str(identity.id) if hasattr(identity, 'id') else request.user_id,
            service_name=request.service_name,
            api_key=result.api_key,
            api_secret=result.api_secret,
            account_email=result.account_email,
            account_username=result.account_username
        )
    
    return {
        "success": result.success,
        "service": result.service_name,
        "message": result.message,
        "needs_verification": result.needs_verification,
        "api_key_obtained": result.api_key is not None,
        "account_email": result.account_email
    }


@router.get("/services/available")
async def get_available_services():
    """
    Get list of services available for automated signup.
    """
    automation = ServiceSignupAutomation("dummy@example.com")
    available = automation.get_available_services()
    
    return {
        "automated_signup": available,
        "message": f"{len(available)} services support automated signup"
    }


@router.post("/services/store")
async def store_service_account(request: StoreServiceAccountRequest):
    """
    Store API credentials after manual signup.
    
    User signs up for a service manually, then provides the API key here.
    """
    
    manager = get_identity_manager()
    identity = await manager.get_identity(request.user_id)
    
    if not identity:
        raise HTTPException(status_code=400, detail="No AI identity found")
    
    signup = ServiceSignup(identity.email, "")
    
    success = await signup.store_service_account(
        user_id=request.user_id,
        ai_identity_id=identity.id,
        service_name=request.service_name,
        api_key=request.api_key,
        api_secret=request.api_secret,
        account_email=request.account_email,
        account_username=request.account_username
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store credentials")
    
    return {
        "success": True,
        "message": f"Credentials for {request.service_name} stored securely"
    }


@router.get("/services/{user_id}")
async def list_service_accounts(user_id: str):
    """List all service accounts for a user's AI"""
    
    manager = get_identity_manager()
    identity = await manager.get_identity(user_id)
    
    if not identity:
        return {"services": []}
    
    signup = ServiceSignup(identity.email, "")
    services = await signup.list_service_accounts(user_id)
    
    return {"services": services}


@router.get("/services/{user_id}/{service_name}")
async def get_service_credentials(user_id: str, service_name: str):
    """Get credentials for a specific service"""
    
    manager = get_identity_manager()
    identity = await manager.get_identity(user_id)
    
    if not identity:
        raise HTTPException(status_code=404, detail="No AI identity found")
    
    signup = ServiceSignup(identity.email, "")
    creds = await signup.get_service_credentials(user_id, service_name)
    
    if not creds:
        raise HTTPException(status_code=404, detail=f"No credentials found for {service_name}")
    
    return creds


# =============================================================================
# SENSITIVE DATA ENDPOINTS
# =============================================================================

@router.post("/sensitive/request")
async def request_sensitive_data(
    user_id: str,
    data_type: str,
    purpose: str,
    service_name: Optional[str] = None
):
    """
    Create a request for sensitive data (OTP, PAN, etc.).
    
    The AI calls this when it needs sensitive data from the user.
    User must provide the data through /sensitive/provide endpoint.
    """
    
    handler = SensitiveDataHandler(user_id)
    request_id = await handler.request_sensitive_data(
        data_type=data_type,
        purpose=purpose,
        service_name=service_name
    )
    
    return {
        "request_id": request_id,
        "data_type": data_type,
        "purpose": purpose,
        "message": f"Please provide your {data_type}. This will be used once and immediately deleted.",
        "expires_in_minutes": 10
    }


@router.post("/sensitive/provide")
async def provide_sensitive_data(request: SensitiveDataRequest):
    """
    User provides sensitive data for a pending request.
    
    Data is stored in memory only and deleted after use.
    """
    
    handler = SensitiveDataHandler(request.user_id)
    success = await handler.receive_sensitive_data(
        request_id=request.request_id,
        data=request.data
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to process sensitive data")
    
    return {
        "success": True,
        "message": "Data received. It will be used and immediately deleted."
    }


# =============================================================================
# AI DECISION LOG ENDPOINTS
# =============================================================================

@router.get("/decisions/{user_id}")
async def get_ai_decisions(user_id: str, limit: int = 20):
    """Get recent AI decisions for accountability"""
    
    responsible_ai = ResponsibleAI(user_id)
    
    # This would normally query the database
    # For now, return placeholder
    return {
        "decisions": [],
        "message": "Decision log endpoint - see ai_decision_log table"
    }


@router.get("/commitments/{user_id}")
async def get_ai_commitments(user_id: str):
    """Get active AI commitments"""
    
    responsible_ai = ResponsibleAI(user_id)
    commitments = await responsible_ai.get_active_commitments()
    
    return {"commitments": commitments}


# =============================================================================
# EMAIL READING ENDPOINTS
# =============================================================================

@router.get("/email/recent/{user_id}")
async def get_recent_emails(user_id: str, max_results: int = 10):
    """
    Get recent emails from the AI's inbox.
    
    Useful for checking verification emails, OTPs, etc.
    """
    try:
        gmail_reader = get_gmail_reader()
        emails = await gmail_reader.fetch_recent_emails(max_results=max_results)
        
        return {
            "success": True,
            "emails": [
                {
                    "id": e.id,
                    "subject": e.subject,
                    "sender": e.sender,
                    "date": e.date.isoformat(),
                    "snippet": e.snippet
                }
                for e in emails
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")


@router.post("/email/wait-verification")
async def wait_for_verification_email(service_name: str, timeout: int = 120):
    """
    Wait for a verification email from a service.
    
    Returns the verification code/link when found.
    """
    try:
        gmail_reader = get_gmail_reader()
        verification = await gmail_reader.wait_for_verification_email(
            from_service=service_name,
            timeout_seconds=timeout
        )
        
        if verification:
            return {
                "success": True,
                "code": verification.code,
                "link": verification.link,
                "otp": verification.otp
            }
        else:
            return {
                "success": False,
                "message": f"No verification email received from {service_name} within {timeout}s"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# =============================================================================
# SERVICE REGISTRY ENDPOINTS
# =============================================================================

@router.get("/registry/services")
async def list_available_services():
    """List all known services in the registry"""
    
    services = []
    for name, info in ServiceRegistry.SERVICES.items():
        services.append({
            "name": name,
            "category": info.get("category"),
            "free_tier": info.get("free_tier", False),
            "blocked": info.get("blocked", False),
            "blocked_reason": info.get("blocked_reason"),
            "capabilities": info.get("capabilities", [])
        })
    
    return {"services": services}


@router.get("/registry/blocked")
async def list_blocked_services():
    """List services that are blocked (need verification)"""
    
    blocked = []
    for name, info in ServiceRegistry.SERVICES.items():
        if info.get("blocked", False):
            blocked.append({
                "name": name,
                "reason": info.get("blocked_reason"),
                "category": info.get("category")
            })
    
    return {"blocked_services": blocked}


@router.get("/registry/for-task/{task_type}")
async def get_services_for_task(task_type: str):
    """Get recommended services for a specific task type"""
    
    services = ServiceRegistry.get_service_for_task(task_type)
    
    return {
        "task_type": task_type,
        "recommended_services": services
    }
