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
    "session_id": "xxx",
    "ui_components": {...}  # Interactive UI elements
}

POST /api/chat/action
{
    "action": "confirm_yes|select_offer|...",
    "button_id": "btn_id",
    "metadata": {...},
    "session_id": "xxx"
}
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import uuid
import time
import json
import logging

# Primary brain - brain.py (ReAct agent with streaming)
from ..core.brain import chat, get_history, save_user_data, get_user_data, brain

# Optional: unified brain for capabilities endpoint
try:
    from ..core.unified_brain import get_brain as get_unified_brain
    UNIFIED_BRAIN_AVAILABLE = True
except ImportError:
    UNIFIED_BRAIN_AVAILABLE = False
    get_unified_brain = None
from ..core.validation import (
    ChatRequest as ValidatedChatRequest,
    validate_request,
    ValidationError,
    chat_rate_limiter,
    sanitize_html,
    validate_session_id
)

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = Field(None, max_length=100)
    user_id: Optional[str] = Field(None, max_length=100)  # User ID for identity lookup
    
    @validator('message')
    def clean_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()
    
    @validator('session_id')
    def clean_session_id(cls, v):
        if v and not validate_session_id(v):
            raise ValueError('Invalid session ID')
        return v


class ChatResponse(BaseModel):
    message: str
    type: str  # answer, task, cancelled, clarify
    status: Optional[str] = None  # need_info, confirm, done
    session_id: str
    need: Optional[List[str]] = None  # missing info fields
    summary: Optional[str] = None  # task summary for confirmation
    result: Optional[Dict] = None  # task result
    proof: Optional[Dict] = None  # proof of execution
    ui_components: Optional[Dict] = None  # interactive UI components
    task_id: Optional[str] = None  # active task ID
    steps: Optional[List[Dict]] = None  # agent thinking/tool steps
    response_time_ms: Optional[float] = None


class ButtonActionRequest(BaseModel):
    action: str = Field(..., min_length=1, max_length=100)
    button_id: str = Field(..., min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    session_id: str = Field(..., min_length=1, max_length=100)
    user_id: Optional[str] = Field(None, max_length=100)


class UserDataRequest(BaseModel):
    identifier: str = Field(..., min_length=1, max_length=254)
    data: Dict[str, Any]
    
    @validator('identifier')
    def clean_identifier(cls, v):
        return sanitize_html(v.strip().lower())


class ErrorResponse(BaseModel):
    error: str
    code: str
    field: Optional[str] = None
    retry_after: Optional[int] = None


class FeedbackRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    user_id: Optional[str] = Field(None, max_length=100)
    message_index: int = Field(..., ge=0)
    rating: str = Field(..., pattern=r"^(positive|negative)$")
    comment: Optional[str] = Field(None, max_length=500)
    answer_preview: Optional[str] = Field(None, max_length=300)
    task_type: Optional[str] = Field(None, max_length=100)  # For learning loop


# =============================================================================
# Rate Limiting Dependency
# =============================================================================

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    # Check common headers for real IP (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


async def check_rate_limit(request: Request):
    """Rate limiting dependency"""
    client_ip = get_client_ip(request)
    allowed, remaining, retry_after = chat_rate_limiter.check(client_ip)
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too many requests. Please slow down.",
                "code": "rate_limit_exceeded",
                "retry_after": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )
    
    # Add rate limit info to response headers
    request.state.rate_limit_remaining = remaining


# =============================================================================
# MAIN CHAT ENDPOINT
# =============================================================================

@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    raw_request: Request,
    _: None = Depends(check_rate_limit)
):
    """
    Main chat endpoint. Handles everything:
    - Questions → Direct answers
    - Tasks → Plan → Ask info → Confirm → Execute
    
    Returns interactive UI components for buttons, cards, forms, etc.
    
    Rate Limited: 30 requests per minute per IP
    """
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id or "default"
    
    try:
        # Log the request (without full message for privacy)
        logger.info(f"Chat request - session: {session_id[:8]}..., user: {user_id}, length: {len(request.message)}")

        # Use brain.py - has full task flow (plan -> collect info -> confirm -> execute)
        # brain.py now delegates execution to engine.py for proof generation
        result = await chat(session_id, request.message, user_id)

        raw_message = result.get("message")
        if raw_message is None:
            raw_message = result.get("response") or result.get("content") or ""
        message_text = str(raw_message) if raw_message is not None else ""

        if not message_text.strip():
            # Never return an empty assistant message to the UI.
            message_text = "I produced an empty response due to an internal issue. Please try again."
            if result.get("status") in (None, "", "done", "success"):
                result["status"] = "error"
            if not result.get("type"):
                result["type"] = "answer"
        
        response_time = (time.time() - start_time) * 1000
        
        response = ChatResponse(
            message=message_text,
            type=result.get("type", "answer"),
            status=result.get("status"),
            session_id=session_id,
            need=result.get("need") or result.get("missing_fields"),
            summary=result.get("summary"),
            result=result.get("result"),
            proof=result.get("proof"),
            ui_components=result.get("ui_components"),
            task_id=result.get("task_id"),
            steps=result.get("steps"),
            response_time_ms=round(response_time, 2)
        )
        
        logger.info(f"Chat response - session: {session_id[:8]}..., status: {response.status}, time: {response_time:.0f}ms")
        return response
        
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "An unexpected error occurred. Please try again.",
                "code": "internal_error"
            }
        )


# =============================================================================
# SSE STREAMING ENDPOINT
# =============================================================================

@router.post("/api/chat/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    raw_request: Request,
    _: None = Depends(check_rate_limit)
):
    """
    Streaming chat endpoint using Server-Sent Events.
    Yields real-time agent events: thinking, tool_call, tool_result, answer.
    """
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id or "default"

    async def generate():
        try:
            async for event in brain.process_stream(session_id, request.message, user_id):
                event_data = event.to_dict()
                yield f"data: {json.dumps(event_data)}\n\n"

            # Send done event with session_id
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': 'An error occurred during processing.'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# =============================================================================
# HISTORY ENDPOINT
# =============================================================================

@router.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get conversation history for a session"""
    if not validate_session_id(session_id):
        raise HTTPException(
            status_code=400, 
            detail={"error": "Invalid session ID", "code": "invalid_session"}
        )
    
    try:
        history = get_history(session_id)
        return {"session_id": session_id, "messages": history, "count": len(history)}
    except Exception as e:
        logger.error(f"History error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


# =============================================================================
# USER DATA ENDPOINTS
# =============================================================================

@router.post("/api/users")
async def save_user(request: UserDataRequest):
    """
    Save user data for future use.
    Example: Save someone's UPI ID so AI can use it for payments.
    """
    try:
        save_user_data(request.identifier, request.data)
        return {"status": "saved", "identifier": request.identifier}
    except Exception as e:
        logger.error(f"Save user error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save user data")


@router.get("/api/users/{identifier}")
async def get_user(identifier: str):
    """Get saved user data"""
    identifier = sanitize_html(identifier.strip().lower())
    
    try:
        data = get_user_data(identifier)
        return {"identifier": identifier, "data": data}
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user data")


# =============================================================================
# BUTTON ACTION ENDPOINT
# =============================================================================

@router.post("/api/chat/action")
async def button_action_endpoint(
    request: ButtonActionRequest,
    raw_request: Request,
    _: None = Depends(check_rate_limit)
):
    """
    Handle button/UI component actions.
    Called when user clicks a button instead of typing.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Button action - session: {request.session_id[:8]}..., action: {request.action}")

        # Convert button action to a chat message and run through brain
        action_messages = {
            "confirm_yes": "yes",
            "confirm_no": "no",
        }
        message = action_messages.get(request.action, request.action)
        result = await chat(request.session_id, message, request.user_id or "default")
        
        response_time = (time.time() - start_time) * 1000
        
        # Check if it's a redirect action
        if result.get("action") == "redirect":
            return {
                "action": "redirect",
                "url": result.get("url"),
                "session_id": request.session_id
            }
        
        return ChatResponse(
            message=result.get("message", ""),
            type=result.get("type", "answer"),
            status=result.get("status"),
            session_id=request.session_id,
            need=result.get("need") or result.get("missing_fields"),
            summary=result.get("summary"),
            result=result.get("result"),
            proof=result.get("proof"),
            ui_components=result.get("ui_components"),
            task_id=result.get("task_id"),
            steps=result.get("steps"),
            response_time_ms=round(response_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Button action error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to process action. Please try again.",
                "code": "action_error"
            }
        )


# =============================================================================
# CAPABILITIES ENDPOINT
# =============================================================================

@router.get("/api/capabilities")
async def get_capabilities():
    """
    Get current AI capabilities and their status.
    Helps frontend show what's available.
    """
    try:
        if UNIFIED_BRAIN_AVAILABLE and get_unified_brain:
            brain = get_unified_brain()
            capabilities = brain.get_capabilities()
            return {
                "status": "operational",
                "brain": "unified",
                "capabilities": capabilities
            }
        else:
            # Build capabilities from engine Config
            from ..core.engine import Config
            services = Config.get_available_services()
            return {
                "status": "operational",
                "brain": "primary",
                "capabilities": {
                    "chat": {"available": True, "description": "Full conversational AI with task execution"},
                    "email": {"available": services.get("email_smtp") or services.get("email_sendgrid"), "description": "Send real emails"},
                    "image_generation": {"available": True, "description": "Generate images (Pollinations AI free)"},
                    "web_search": {"available": True, "description": "Search the web (DuckDuckGo)"},
                    "meetings": {"available": True, "description": "Create Jitsi meeting links"},
                    "payments": {"available": services.get("payments"), "description": "Payment links (Razorpay/UPI)"},
                }
            }
    except Exception as e:
        logger.error(f"Capabilities error: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


# =============================================================================
# FEEDBACK ENDPOINT
# =============================================================================

@router.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback (positive/negative) for an AI response.
    This feedback influences future AI behavior through the Learning Loop.
    """
    try:
        user_id = request.user_id or "default"
        result = brain.submit_feedback(
            session_id=request.session_id,
            user_id=user_id,
            message_index=request.message_index,
            rating=request.rating,
            comment=request.comment,
            answer_preview=request.answer_preview or "",
            task_type=request.task_type,  # For learning loop
        )
        return result
    except Exception as e:
        logger.error(f"Feedback error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to record feedback.", "code": "feedback_error"}
        )


@router.get("/api/learning/stats")
async def get_learning_stats():
    """
    Get learning loop statistics - strategy confidence, success rates, etc.
    """
    try:
        from backend.core.strategy_store import StrategyStore
        strategies = StrategyStore()
        return {
            "status": "ok",
            "stats": strategies.get_statistics()
        }
    except Exception as e:
        logger.error(f"Learning stats error: {str(e)}", exc_info=True)
        return {"status": "error", "stats": {}}
