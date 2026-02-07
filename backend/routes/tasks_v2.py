"""
Task Orchestration API Routes
=============================
Real-time task tracking with progress updates.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from ..agent.orchestrator import get_orchestrator, TaskStatus
from ..agent.scheduler import get_scheduler, start_scheduler

router = APIRouter(prefix="/api/v2/tasks", tags=["tasks"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class CreateTaskRequest(BaseModel):
    """Create a new orchestrated task"""
    task_type: str = Field(..., description="Type of task: schedule_meeting, send_email, set_reminder, research")
    params: Dict[str, Any] = Field(..., description="Task parameters")
    meeting_start_time: Optional[str] = None  # ISO format for meeting tasks


class TaskResponse(BaseModel):
    """Task with progress tracking"""
    id: str
    title: str
    task_type: str
    status: str
    progress_percent: int
    substeps: List[Dict]
    estimated_completion: Optional[str]
    needs_user_input: bool
    input_prompt: Optional[str]
    created_at: str


class UpdateSubstepRequest(BaseModel):
    """Update a substep (for webhooks, manual completion)"""
    status: str  # completed, failed, skipped
    result: Optional[Dict] = None


class UserInputRequest(BaseModel):
    """Provide user input for a task"""
    input_value: Any
    continue_task: bool = True


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("", response_model=TaskResponse)
async def create_task(request: CreateTaskRequest, user_email: str = "default@user.com"):
    """
    Create a new orchestrated task.
    
    Task types:
    - schedule_meeting: Schedule a meeting with participants
    - send_email: Compose and send an email
    - set_reminder: Set a reminder for later
    - research: Research a topic
    
    Returns the task with substeps and progress tracking.
    """
    try:
        orchestrator = get_orchestrator()
        
        # Parse meeting start time if provided
        meeting_start_time = None
        if request.meeting_start_time:
            meeting_start_time = datetime.fromisoformat(request.meeting_start_time)
        
        # Create the task
        task = await orchestrator.create_task(
            user_id=user_email,
            task_type=request.task_type,
            params=request.params,
            meeting_start_time=meeting_start_time
        )
        
        # Execute immediate steps
        task = await orchestrator.execute_task(task.id)
        
        return TaskResponse(
            id=task.id,
            title=task.title,
            task_type=task.task_type,
            status=task.status.value,
            progress_percent=task.progress_percent,
            substeps=[s.to_dict() for s in task.substeps],
            estimated_completion=task.estimated_completion.isoformat() if task.estimated_completion else None,
            needs_user_input=task.needs_user_input,
            input_prompt=task.input_prompt,
            created_at=task.created_at.isoformat()
        )
        
    except Exception as e:
        print(f"[TASK API] Error creating task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[Dict])
async def get_user_tasks(
    user_email: str = "default@user.com",
    status: Optional[str] = None
):
    """
    Get all tasks for a user.
    
    Filter by status: pending, in_progress, waiting_input, completed, failed, cancelled
    """
    try:
        orchestrator = get_orchestrator()
        tasks = await orchestrator.get_user_tasks(user_email, status)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get a specific task with all substeps"""
    try:
        orchestrator = get_orchestrator()
        task = await orchestrator.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{task_id}/substeps/{substep_id}")
async def update_substep(task_id: str, substep_id: str, request: UpdateSubstepRequest):
    """
    Update a substep status (for webhooks or manual completion).
    
    Used when:
    - Webhook confirms participant joined meeting
    - User manually marks step as complete
    - External event completes a step
    """
    try:
        orchestrator = get_orchestrator()
        
        task = await orchestrator.complete_substep(
            task_id=task_id,
            substep_id=substep_id,
            result=request.result or {}
        )
        
        return task.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/input")
async def provide_user_input(task_id: str, request: UserInputRequest):
    """
    Provide user input for a task that requires it.
    
    Some tasks may pause and ask for user confirmation or choice.
    This endpoint provides that input and continues the task.
    """
    try:
        orchestrator = get_orchestrator()
        task = await orchestrator.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Store the input
        task.user_input_received = request.input_value
        task.needs_user_input = False
        
        if request.continue_task:
            # Continue executing the task
            task = await orchestrator.execute_task(task_id)
        
        return task.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a task and all pending substeps"""
    try:
        orchestrator = get_orchestrator()
        task = await orchestrator.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.status = TaskStatus.CANCELLED
        
        # Save to database
        if orchestrator.client:
            orchestrator.client.table("orchestrated_tasks").update({
                "status": "cancelled"
            }).eq("id", task_id).execute()
        
        return {"status": "cancelled", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# JITSI WEBHOOK ENDPOINT
# =============================================================================

@router.post("/webhooks/jitsi")
async def jitsi_webhook(payload: Dict[str, Any]):
    """
    Webhook endpoint for Jitsi events.
    
    Events:
    - PARTICIPANT_JOINED: A participant joined the meeting
    - PARTICIPANT_LEFT: A participant left the meeting
    - CONFERENCE_ENDED: The meeting ended
    """
    try:
        event_type = payload.get("eventType") or payload.get("event")
        room_name = payload.get("roomName") or payload.get("room")
        participant = payload.get("participant", {})
        
        print(f"[JITSI WEBHOOK] Event: {event_type}, Room: {room_name}")
        
        orchestrator = get_orchestrator()
        
        if orchestrator.client:
            # Find meeting by room name (meeting link contains room)
            result = orchestrator.client.table("meetings").select("*").ilike(
                "meeting_link", f"%{room_name}%"
            ).execute()
            
            if result.data:
                meeting = result.data[0]
                meeting_id = meeting["id"]
                
                if event_type in ["PARTICIPANT_JOINED", "participant_joined"]:
                    # Update participant status
                    orchestrator.client.table("meeting_participants").update({
                        "joined": True,
                        "joined_at": datetime.utcnow().isoformat()
                    }).eq("meeting_id", meeting_id).eq(
                        "participant_name", participant.get("name", "")
                    ).execute()
                    
                    # Find and complete the "participant joins" substep
                    task_result = orchestrator.client.table("orchestrated_tasks").select("*").eq(
                        "meeting_id", meeting_id
                    ).execute()
                    
                    if task_result.data:
                        task = task_result.data[0]
                        substeps = orchestrator.client.table("task_substeps").select("*").eq(
                            "task_id", task["id"]
                        ).eq("action_type", "detect_join").execute()
                        
                        if substeps.data:
                            await orchestrator.complete_substep(
                                task["id"],
                                substeps.data[0]["id"],
                                {"participant": participant}
                            )
                
                elif event_type in ["CONFERENCE_ENDED", "conference_ended"]:
                    # Complete the meeting
                    orchestrator.client.table("meetings").update({
                        "status": "completed",
                        "end_time": datetime.utcnow().isoformat()
                    }).eq("id", meeting_id).execute()
                    
                    # Find and complete the "meeting completes" substep
                    task_result = orchestrator.client.table("orchestrated_tasks").select("*").eq(
                        "meeting_id", meeting_id
                    ).execute()
                    
                    if task_result.data:
                        task = task_result.data[0]
                        substeps = orchestrator.client.table("task_substeps").select("*").eq(
                            "task_id", task["id"]
                        ).eq("action_type", "detect_completion").execute()
                        
                        if substeps.data:
                            await orchestrator.complete_substep(
                                task["id"],
                                substeps.data[0]["id"],
                                {"ended_at": datetime.utcnow().isoformat()}
                            )
        
        return {"status": "received"}
        
    except Exception as e:
        print(f"[JITSI WEBHOOK] Error: {e}")
        return {"status": "error", "message": str(e)}


# =============================================================================
# NOTIFICATIONS
# =============================================================================

@router.get("/notifications")
async def get_notifications(user_email: str, unread_only: bool = True):
    """Get notifications for a user"""
    try:
        orchestrator = get_orchestrator()
        
        if orchestrator.client:
            query = orchestrator.client.table("notifications").select("*").eq("user_id", user_email)
            if unread_only:
                query = query.eq("is_read", False)
            
            result = query.order("created_at", desc=True).limit(50).execute()
            return result.data or []
        
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    try:
        orchestrator = get_orchestrator()
        
        if orchestrator.client:
            orchestrator.client.table("notifications").update({
                "is_read": True,
                "read_at": datetime.utcnow().isoformat()
            }).eq("id", notification_id).execute()
        
        return {"status": "marked_read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SCHEDULER CONTROL
# =============================================================================

@router.post("/scheduler/start")
async def start_scheduler_endpoint():
    """Start the background job scheduler"""
    try:
        start_scheduler()
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler/status")
async def scheduler_status():
    """Get scheduler status"""
    scheduler = get_scheduler()
    return {
        "running": scheduler.is_running,
        "jobs": len(scheduler.scheduler.get_jobs()) if scheduler.scheduler else 0
    }
