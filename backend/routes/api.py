"""
SUPER MANAGER - CLEAN API
=========================
ONE endpoint. SIMPLE flow.

POST /api/chat
{
    "message": "user message",
    "session_id": "optional"
}

Response:
{
    "message": "AI response",
    "type": "answer|task",
    "status": "need_info|confirm|done" (if task),
    "session_id": "xxx"
}
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid

from ..core.brain import chat, get_history, save_user_data, get_user_data

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    type: str  # answer, task, cancelled, clarify
    status: Optional[str] = None  # need_info, confirm, done
    session_id: str
    need: Optional[List[str]] = None  # missing info fields
    summary: Optional[str] = None  # task summary for confirmation
    result: Optional[Dict] = None  # task result


class UserDataRequest(BaseModel):
    identifier: str  # email or phone
    data: Dict[str, Any]  # name, upi_id, etc.


# =============================================================================
# MAIN CHAT ENDPOINT
# =============================================================================

@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint. Handles everything:
    - Questions → Direct answers
    - Tasks → Plan → Ask info → Confirm → Execute
    
    Just send a message, get a response. Simple.
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        result = await chat(session_id, request.message)
        
        return ChatResponse(
            message=result.get("message", ""),
            type=result.get("type", "answer"),
            status=result.get("status"),
            session_id=session_id,
            need=result.get("need"),
            summary=result.get("summary"),
            result=result.get("result")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HISTORY ENDPOINT
# =============================================================================

@router.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get conversation history for a session"""
    history = get_history(session_id)
    return {"session_id": session_id, "messages": history}


# =============================================================================
# USER DATA ENDPOINTS
# =============================================================================

@router.post("/api/users")
async def save_user(request: UserDataRequest):
    """
    Save user data for future use.
    Example: Save someone's UPI ID so AI can use it for payments.
    """
    save_user_data(request.identifier, request.data)
    return {"status": "saved", "identifier": request.identifier}


@router.get("/api/users/{identifier}")
async def get_user(identifier: str):
    """Get saved user data"""
    data = get_user_data(identifier)
    if data:
        return {"identifier": identifier, "data": data}
    return {"identifier": identifier, "data": None}
