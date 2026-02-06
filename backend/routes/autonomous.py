"""
AUTONOMOUS AI API
=================
The main API endpoint for the autonomous AI manager.
This AI can do ANYTHING - no predefined tasks, just AI + execution.
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import json
import asyncio

from ..core.autonomous_ai import (
    chat, 
    provide_info, 
    confirm_action,
    get_data_store,
    save_user_info,
    get_user_info
)

router = APIRouter(prefix="/api/ai", tags=["autonomous-ai"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class InfoRequest(BaseModel):
    session_id: str
    info: Dict[str, Any]


class ConfirmRequest(BaseModel):
    session_id: str
    confirmed: bool


class UserInfoRequest(BaseModel):
    identifier: str  # email or phone
    info: Dict[str, Any]  # name, upi_id, phone, etc.


# ============================================================================
# MAIN CHAT ENDPOINT
# ============================================================================

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint - send any message, AI handles everything!
    
    The AI will:
    1. Understand your request
    2. Plan how to accomplish it
    3. Ask for missing information if needed
    4. Execute the task (with confirmation for sensitive actions)
    5. Return results
    
    Example messages:
    - "Schedule a meeting with john@test.com tomorrow at 2pm"
    - "Remind me to call mom at 5pm"
    - "Send an email to boss@company.com about the project update"
    - "Pay ₹500 to friend@upi"
    - "Book a flight to Delhi for next Friday"
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        result = await chat(session_id, request.message)
        return {
            "session_id": session_id,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/provide-info")
async def provide_info_endpoint(request: InfoRequest):
    """
    Provide missing information that the AI asked for.
    
    When the AI responds with action="ask_info", use this endpoint
    to provide the requested information.
    """
    try:
        result = await provide_info(request.session_id, request.info)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm")
async def confirm_endpoint(request: ConfirmRequest):
    """
    Confirm or cancel a pending action.
    
    When the AI responds with action="confirm", call this to
    either approve (confirmed=true) or cancel (confirmed=false).
    """
    try:
        result = await confirm_action(request.session_id, request.confirmed)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# USER DATA ENDPOINTS
# ============================================================================

@router.post("/user-info")
async def save_user_info_endpoint(request: UserInfoRequest):
    """
    Save information about a person (their UPI ID, phone, etc.)
    
    This helps the AI complete tasks without asking every time.
    
    Example:
    {
        "identifier": "john@test.com",
        "info": {
            "name": "John Doe",
            "phone": "+919876543210",
            "upi_id": "john@okaxis"
        }
    }
    """
    try:
        await save_user_info(request.identifier, request.info)
        return {"status": "saved", "identifier": request.identifier}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-info/{identifier}")
async def get_user_info_endpoint(identifier: str):
    """Get stored information about a person"""
    try:
        info = await get_user_info(identifier)
        if info:
            return {"identifier": identifier, "info": info}
        return {"identifier": identifier, "info": None, "message": "No data found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONVERSATION HISTORY
# ============================================================================

@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history for a session"""
    store = get_data_store()
    messages = store.get_conversation(session_id)
    return {
        "session_id": session_id,
        "messages": messages
    }


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Clear conversation history"""
    store = get_data_store()
    if session_id in store.conversations:
        del store.conversations[session_id]
    return {"status": "cleared"}


# ============================================================================
# TASK STATUS
# ============================================================================

@router.get("/tasks")
async def get_all_tasks():
    """Get all tasks"""
    store = get_data_store()
    return {"tasks": list(store.tasks.values())}


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a specific task"""
    store = get_data_store()
    task = store.tasks.get(task_id)
    if task:
        return task
    raise HTTPException(status_code=404, detail="Task not found")


# ============================================================================
# WEBSOCKET FOR REAL-TIME UPDATES
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_update(self, session_id: str, data: Dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(data)


ws_manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket for real-time task updates.
    
    Connect to receive:
    - Task progress updates
    - Execution status
    - Real-time responses
    """
    await ws_manager.connect(session_id, websocket)
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            # Process with AI
            result = await chat(session_id, message)
            
            # Send response
            await websocket.send_json(result)
            
            # If executing, send progress updates
            if result.get("action") == "executed":
                await websocket.send_json({
                    "type": "task_complete",
                    "task_id": result.get("task_id"),
                    "success": result.get("success")
                })
                
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)


# ============================================================================
# QUICK ACTIONS (Shortcuts)
# ============================================================================

@router.post("/quick/email")
async def quick_email(to: str, subject: str, body: str, session_id: Optional[str] = None):
    """Quick endpoint to send an email"""
    session_id = session_id or str(uuid.uuid4())
    message = f"Send an email to {to} with subject '{subject}' and message: {body}"
    
    # First call to set up
    result = await chat(session_id, message)
    
    # Auto-confirm if it's asking for confirmation
    if result.get("action") == "confirm" or result.get("requires_confirmation"):
        result = await confirm_action(session_id, True)
    
    return result


@router.post("/quick/meeting")
async def quick_meeting(
    title: str, 
    participants: List[str], 
    time: str,
    session_id: Optional[str] = None
):
    """Quick endpoint to schedule a meeting"""
    session_id = session_id or str(uuid.uuid4())
    participants_str = ", ".join(participants)
    message = f"Schedule a meeting called '{title}' with {participants_str} at {time}"
    
    result = await chat(session_id, message)
    
    if result.get("action") == "confirm" or result.get("requires_confirmation"):
        result = await confirm_action(session_id, True)
    
    return result


@router.post("/quick/reminder")
async def quick_reminder(
    text: str,
    time: str,
    method: str = "email",
    recipient: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Quick endpoint to set a reminder"""
    session_id = session_id or str(uuid.uuid4())
    
    if recipient:
        message = f"Remind {recipient} about '{text}' at {time} via {method}"
    else:
        message = f"Remind me about '{text}' at {time}"
    
    result = await chat(session_id, message)
    
    if result.get("action") == "confirm" or result.get("requires_confirmation"):
        result = await confirm_action(session_id, True)
    
    return result
