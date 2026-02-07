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
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import uuid
import time
import logging

from ..core.brain import chat, get_history, save_user_data, get_user_data
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
    response_time_ms: Optional[float] = None


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
    
    Just send a message, get a response. Simple.
    
    Rate Limited: 30 requests per minute per IP
    """
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Log the request (without full message for privacy)
        logger.info(f"Chat request - session: {session_id[:8]}..., length: {len(request.message)}")
        
        result = await chat(session_id, request.message)
        
        response_time = (time.time() - start_time) * 1000
        
        response = ChatResponse(
            message=result.get("message", ""),
            type=result.get("type", "answer"),
            status=result.get("status"),
            session_id=session_id,
            need=result.get("need"),
            summary=result.get("summary"),
            result=result.get("result"),
            response_time_ms=round(response_time, 2)
        )
        
        logger.info(f"Chat response - session: {session_id[:8]}..., time: {response_time:.0f}ms")
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
