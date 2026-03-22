"""
Automation API Routes
=======================
Endpoints for running automation flows:
- Meeting booking
- Service signup
- Email campaigns
- Appointment scheduling
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/automation", tags=["Automation"])

# Import automation flows
try:
    from ..core.automation_flows import (
        run_automation_flow,
        FlowRegistry,
        FlowStatus,
    )
    AUTOMATION_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import automation flows: {e}")
    AUTOMATION_AVAILABLE = False


# =============================================================================
# Request/Response Models
# =============================================================================

class MeetingBookingRequest(BaseModel):
    """Request to book a meeting"""
    user_id: str = Field(..., description="User identifier")
    title: str = Field(..., description="Meeting title")
    participants: List[str] = Field(..., description="List of participant emails")
    datetime: str = Field(..., description="Meeting datetime (ISO format)")
    duration: int = Field(default=30, description="Duration in minutes")
    meeting_type: str = Field(default="jitsi", description="Meeting type: jitsi, zoom, google_meet")


class ServiceSignupRequest(BaseModel):
    """Request to sign up for a service"""
    user_id: str
    service_name: str = Field(..., description="Name of the service")
    service_url: str = Field(..., description="URL of the signup page")
    user_details: Dict[str, str] = Field(..., description="User details for signup form")


class EmailCampaignRequest(BaseModel):
    """Request to run an email campaign"""
    user_id: str
    subject: str = Field(..., description="Email subject (use {name} for personalization)")
    body: str = Field(..., description="Email body template (use {name} for personalization)")
    recipients: List[Dict[str, str]] = Field(..., description="List of recipients [{email, name}]")
    batch_size: int = Field(default=10, description="Emails per batch")
    delay_seconds: int = Field(default=5, description="Delay between batches")


class AppointmentRequest(BaseModel):
    """Request to schedule an appointment"""
    user_id: str
    title: str = Field(..., description="Appointment title")
    with_email: str = Field(..., alias="with", description="Email of person to meet")
    preferred_times: List[str] = Field(..., description="List of preferred datetime strings")
    duration: int = Field(default=30, description="Duration in minutes")


class GenericFlowRequest(BaseModel):
    """Generic flow request"""
    user_id: str
    flow_name: str = Field(..., description="Name of the flow to run")
    parameters: Dict[str, Any] = Field(default={}, description="Flow parameters")


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/status")
async def get_automation_status():
    """Get automation module status"""
    return {
        "available": AUTOMATION_AVAILABLE,
        "flows": FlowRegistry.list_flows() if AUTOMATION_AVAILABLE else [],
    }


@router.get("/flows")
async def list_available_flows():
    """List all available automation flows"""
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Automation not available")
    
    flows = FlowRegistry.list_flows()
    
    flow_descriptions = {
        "meeting_booking": {
            "name": "Meeting Booking",
            "description": "Book and schedule meetings with automatic invitations",
            "parameters": ["title", "participants", "datetime", "duration", "meeting_type"],
        },
        "service_signup": {
            "name": "Service Signup",
            "description": "Automate signing up for online services",
            "parameters": ["service_name", "service_url", "user_details"],
        },
        "email_campaign": {
            "name": "Email Campaign",
            "description": "Send personalized email campaigns to multiple recipients",
            "parameters": ["subject", "body", "recipients", "batch_size"],
        },
        "appointment": {
            "name": "Appointment Scheduling",
            "description": "Schedule appointments with availability checking",
            "parameters": ["title", "with", "preferred_times", "duration"],
        },
    }
    
    return {
        "flows": [
            {"id": f, **flow_descriptions.get(f, {"name": f, "description": ""})}
            for f in flows
        ]
    }


@router.post("/book-meeting")
async def book_meeting(request: MeetingBookingRequest):
    """
    Book a meeting with all the bells and whistles:
    - Creates meeting room (Jitsi/Zoom)
    - Sends email invitations
    - Sets up reminders
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Automation not available")
    
    result = await run_automation_flow(
        flow_name="meeting_booking",
        user_id=request.user_id,
        parameters={
            "title": request.title,
            "participants": request.participants,
            "datetime": request.datetime,
            "duration": request.duration,
            "meeting_type": request.meeting_type,
        }
    )
    
    if result.success:
        return {
            "status": "success",
            "message": "Meeting booked successfully",
            "meeting": {
                "title": request.title,
                "url": result.data.get("meeting_url"),
                "datetime": request.datetime,
                "participants": request.participants,
                "invitations_sent": result.data.get("total_sent", 0),
            },
            "details": result.data,
        }
    else:
        raise HTTPException(
            status_code=400,
            detail={
                "message": result.message,
                "error": result.error,
                "steps_completed": result.steps_completed,
            }
        )


@router.post("/signup")
async def service_signup(request: ServiceSignupRequest):
    """
    Sign up for a service automatically:
    - Navigates to signup page
    - Fills out forms
    - Handles email verification
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Automation not available")
    
    result = await run_automation_flow(
        flow_name="service_signup",
        user_id=request.user_id,
        parameters={
            "service_name": request.service_name,
            "service_url": request.service_url,
            "user_details": request.user_details,
        }
    )
    
    return {
        "status": "success" if result.success else "partial",
        "message": result.message,
        "service": request.service_name,
        "steps_completed": result.steps_completed,
        "details": result.data,
    }


@router.post("/email-campaign")
async def run_email_campaign(
    request: EmailCampaignRequest,
    background_tasks: BackgroundTasks
):
    """
    Run an email campaign:
    - Personalizes emails for each recipient
    - Sends in batches with rate limiting
    - Tracks delivery status
    
    For large campaigns, runs in background.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Automation not available")
    
    # For small campaigns, run synchronously
    if len(request.recipients) <= 20:
        result = await run_automation_flow(
            flow_name="email_campaign",
            user_id=request.user_id,
            parameters={
                "subject": request.subject,
                "body": request.body,
                "recipients": request.recipients,
                "batch_size": request.batch_size,
                "delay_seconds": request.delay_seconds,
            }
        )
        
        return {
            "status": "success" if result.success else "partial",
            "message": result.message,
            "emails_sent": result.data.get("total_sent", 0),
            "emails_failed": result.data.get("total_failed", 0),
            "completion_rate": result.data.get("completion_rate", 0),
            "details": result.data,
        }
    
    # For large campaigns, run in background
    campaign_id = f"campaign_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    async def run_campaign():
        await run_automation_flow(
            flow_name="email_campaign",
            user_id=request.user_id,
            parameters={
                "subject": request.subject,
                "body": request.body,
                "recipients": request.recipients,
            }
        )
    
    background_tasks.add_task(run_campaign)
    
    return {
        "status": "started",
        "campaign_id": campaign_id,
        "message": f"Campaign started in background for {len(request.recipients)} recipients",
        "total_recipients": len(request.recipients),
    }


@router.post("/schedule-appointment")
async def schedule_appointment(request: AppointmentRequest):
    """
    Schedule an appointment:
    - Checks calendar availability
    - Creates appointment
    - Sends confirmation emails
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Automation not available")
    
    result = await run_automation_flow(
        flow_name="appointment",
        user_id=request.user_id,
        parameters={
            "title": request.title,
            "with": request.with_email,
            "preferred_times": request.preferred_times,
            "duration": request.duration,
        }
    )
    
    if result.success:
        return {
            "status": "success",
            "message": "Appointment scheduled",
            "appointment": {
                "title": request.title,
                "with": request.with_email,
                "time": result.data.get("appointment_time"),
                "duration": request.duration,
                "confirmation_sent": result.data.get("confirmation_sent", False),
            },
        }
    else:
        raise HTTPException(
            status_code=400,
            detail={
                "message": result.message,
                "error": result.error,
            }
        )


@router.post("/run")
async def run_generic_flow(request: GenericFlowRequest):
    """
    Run any automation flow by name.
    
    This is a generic endpoint for running any registered flow.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Automation not available")
    
    available_flows = FlowRegistry.list_flows()
    
    if request.flow_name not in available_flows:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown flow: {request.flow_name}. Available: {available_flows}"
        )
    
    result = await run_automation_flow(
        flow_name=request.flow_name,
        user_id=request.user_id,
        parameters=request.parameters,
    )
    
    return {
        "status": result.status.value,
        "success": result.success,
        "message": result.message,
        "data": result.data,
        "steps_completed": result.steps_completed,
        "duration_ms": result.duration_ms,
        "error": result.error,
    }


# =============================================================================
# Quick Actions (Simplified endpoints)
# =============================================================================

@router.post("/quick/meeting")
async def quick_meeting(
    user_id: str,
    title: str,
    participants: str,  # Comma-separated emails
    when: str = "now",
):
    """
    Quick meeting creation with minimal parameters.
    
    Args:
        user_id: Your user ID
        title: Meeting title
        participants: Comma-separated list of participant emails
        when: When to meet (default: now)
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Automation not available")
    
    participant_list = [p.strip() for p in participants.split(",") if p.strip()]
    
    result = await run_automation_flow(
        flow_name="meeting_booking",
        user_id=user_id,
        parameters={
            "title": title,
            "participants": participant_list,
            "datetime": when,
            "meeting_type": "jitsi",
        }
    )
    
    if result.success:
        return {
            "status": "success",
            "meeting_url": result.data.get("meeting_url"),
            "title": title,
            "invitations_sent": result.data.get("total_sent", 0),
        }
    else:
        return {
            "status": "failed",
            "error": result.error,
            "message": result.message,
        }


@router.post("/quick/email")
async def quick_email(
    user_id: str,
    to: str,
    subject: str,
    body: str,
):
    """
    Quick email sending using user's AI identity.
    """
    if not AUTOMATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Automation not available")
    
    try:
        from ..core.identity_email_service import get_identity_email_service
        
        service = get_identity_email_service()
        result = await service.send_email_for_user(
            user_id=user_id,
            to=to,
            subject=subject,
            body=body,
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
