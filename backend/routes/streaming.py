"""
REAL-TIME STREAMING API
=======================
Server-Sent Events (SSE) + WebSocket for true real-time streaming.
Tokens appear instantly - just like ChatGPT!
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import json
import asyncio

from ..core.realtime_ai import (
    stream_ai_response,
    chat_sync,
    execute_task,
    execute_task_sync,
    get_session,
    create_session,
    clear_session,
    get_history
)

router = APIRouter(prefix="/api/stream", tags=["realtime-ai"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ConfirmRequest(BaseModel):
    session_id: str
    confirmed: bool


# ============================================================================
# SSE STREAMING ENDPOINT - THE REAL-TIME MAGIC!
# ============================================================================

@router.post("/chat")
async def stream_chat(request: ChatRequest):
    """
    Stream AI response in real-time using Server-Sent Events.
    
    Each token is sent immediately as it's generated.
    Frontend receives chunks progressively - just like ChatGPT!
    
    Response format (SSE):
    data: {"type": "token", "content": "Hello"}
    data: {"type": "token", "content": " there"}
    data: {"type": "done", "session_id": "xxx", "has_action": true}
    """
    session_id = request.session_id or create_session()
    
    async def generate():
        full_response = ""
        
        async for chunk in stream_ai_response(session_id, request.message):
            full_response += chunk
            # Send each token immediately
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
        
        # Check if there's a pending action
        session = get_session(session_id)
        has_action = session.pending_task is not None
        action_type = session.pending_task.get("action") if has_action else None
        
        # Send completion signal
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'has_action': has_action, 'action_type': action_type})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/chat/sync")
async def chat_endpoint(request: ChatRequest):
    """
    Non-streaming chat - returns full response at once.
    Use this for simple integrations that don't need streaming.
    """
    session_id = request.session_id or create_session()
    result = await chat_sync(session_id, request.message)
    return result


# ============================================================================
# TASK EXECUTION WITH STREAMING
# ============================================================================

@router.post("/execute")
async def stream_execute(request: ConfirmRequest):
    """
    Execute pending task with streaming status updates.
    
    Response format (SSE):
    data: {"type": "status", "content": "Creating meeting..."}
    data: {"type": "status", "content": "\n\nMeeting created!"}
    data: {"type": "done", "success": true}
    """
    async def generate():
        async for chunk in execute_task(request.session_id, request.confirmed):
            yield f"data: {json.dumps({'type': 'status', 'content': chunk})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done', 'success': True})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/execute/sync")
async def execute_endpoint(request: ConfirmRequest):
    """Non-streaming execute"""
    result = await execute_task_sync(request.session_id, request.confirmed)
    return result


# ============================================================================
# WEBSOCKET - BIDIRECTIONAL REAL-TIME
# ============================================================================

@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    Full bidirectional WebSocket for real-time chat.
    
    Send: {"message": "Hello"}
    Receive: {"type": "token", "content": "Hi"} ... {"type": "done"}
    
    Send: {"action": "confirm", "confirmed": true}
    Receive: {"type": "status", "content": "..."} ... {"type": "done"}
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            if "message" in data:
                # Chat message - stream response
                async for chunk in stream_ai_response(session_id, data["message"]):
                    await websocket.send_json({"type": "token", "content": chunk})
                
                # Check for pending action
                session = get_session(session_id)
                has_action = session.pending_task is not None
                
                await websocket.send_json({
                    "type": "done",
                    "has_action": has_action,
                    "action_type": session.pending_task.get("action") if has_action else None
                })
            
            elif data.get("action") == "confirm":
                # Execute task
                async for chunk in execute_task(session_id, data.get("confirmed", True)):
                    await websocket.send_json({"type": "status", "content": chunk})
                
                await websocket.send_json({"type": "done", "success": True})
            
            elif data.get("action") == "cancel":
                # Cancel pending task
                async for chunk in execute_task(session_id, False):
                    await websocket.send_json({"type": "status", "content": chunk})
                
                await websocket.send_json({"type": "done", "cancelled": True})
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@router.post("/session")
async def create_new_session():
    """Create a new chat session"""
    session_id = create_session()
    return {"session_id": session_id}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    clear_session(session_id)
    return {"status": "deleted"}


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get conversation history"""
    history = get_history(session_id)
    return {"session_id": session_id, "messages": history}
