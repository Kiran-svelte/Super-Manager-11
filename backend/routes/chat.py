"""
TRUE AI CHAT API
================
This is the NEW primary chat endpoint. 
ALL responses come from the LLM - no hardcoded text!
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid

from ..core.true_ai_chat import chat, get_conversation

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str
    requires_confirmation: bool = False
    action_completed: bool = False
    meeting_url: Optional[str] = None
    results: Optional[list] = None
    error: bool = False


@router.post("/", response_model=ChatResponse)
@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    The main chat endpoint.
    
    Send any message, get an intelligent response.
    The AI will:
    - Understand your request
    - Ask for clarification if needed
    - Propose actions and ask for confirmation
    - Execute actions when confirmed
    - Remember the conversation context
    
    This is a TRUE AI chat - no hardcoded responses!
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        # Chat with the AI
        result = await chat(session_id, request.message)
        
        return ChatResponse(
            response=result.get("response", ""),
            session_id=result.get("session_id", session_id),
            requires_confirmation=result.get("requires_confirmation", False),
            action_completed=result.get("action_completed", False),
            meeting_url=result.get("meeting_url"),
            results=result.get("results"),
            error=result.get("error", False)
        )
        
    except Exception as e:
        print(f"[CHAT API ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get conversation history for a session"""
    try:
        conversation = get_conversation(session_id)
        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in conversation.messages
            ],
            "has_pending_action": conversation.pending_action is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{session_id}")  
async def clear_chat_history(session_id: str):
    """Clear conversation history (start fresh)"""
    from ..core.true_ai_chat import _conversations
    if session_id in _conversations:
        del _conversations[session_id]
    return {"status": "cleared", "session_id": session_id}
