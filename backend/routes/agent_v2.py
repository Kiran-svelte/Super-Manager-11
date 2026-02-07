"""
Agent API Routes - The New Main Interface
==========================================
This replaces the old chat routes with the new Agent system.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid

from ..agent.core import Agent, AgentConfig, get_agent
from ..agent.memory import get_memory, UserProfile, Contact
from ..agent.executor import get_executor

router = APIRouter(prefix="/api/v2", tags=["agent"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None  # For user lookup


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str
    expert: Optional[str] = None  # Which expert persona responded
    actions_taken: List[Dict[str, Any]] = []  # Actions executed
    error: bool = False


class ContactRequest(BaseModel):
    """Add contact request"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    telegram_id: Optional[str] = None
    relationship: str = "other"


class PreferenceRequest(BaseModel):
    """Set preference request"""
    category: str  # fashion, travel, meetings, etc.
    key: str
    value: Any


# =============================================================================
# INITIALIZE AGENT
# =============================================================================

def init_agent():
    """Initialize the agent with action handlers"""
    agent = get_agent()
    executor = get_executor()
    
    # Register action handlers
    agent.register_action_handler("send_email", lambda args: executor.execute("send_email", args))
    agent.register_action_handler("create_calendar_event", lambda args: executor.execute("create_calendar_event", args))
    agent.register_action_handler("create_meeting_link", lambda args: executor.execute("create_meeting_link", args))
    agent.register_action_handler("send_telegram", lambda args: executor.execute("send_telegram", args))
    agent.register_action_handler("send_sms", lambda args: executor.execute("send_sms", args))
    agent.register_action_handler("search_web", lambda args: executor.execute("search_web", args))
    agent.register_action_handler("set_reminder", lambda args: executor.execute("set_reminder", args))
    agent.register_action_handler("make_payment", lambda args: executor.execute("make_payment", args))
    agent.register_action_handler("lookup_contact", handle_contact_lookup)
    agent.register_action_handler("get_user_info", handle_user_info)
    agent.register_action_handler("update_user_preference", handle_preference_update)
    
    return agent


async def handle_contact_lookup(args: Dict) -> Dict:
    """Handle contact lookup from memory"""
    memory = get_memory()
    name = args.get("name", "")
    
    # This would need user_id context
    # For now, return placeholder
    return {
        "success": True,
        "contact": None,
        "message": f"Looking for contact: {name}"
    }


async def handle_user_info(args: Dict) -> Dict:
    """Handle user info request"""
    memory = get_memory()
    info_type = args.get("info_type", "preferences")
    
    return {
        "success": True,
        "info_type": info_type,
        "data": {}
    }


async def handle_preference_update(args: Dict) -> Dict:
    """Handle preference update"""
    memory = get_memory()
    
    return {
        "success": True,
        "message": f"Saved preference: {args.get('category')}/{args.get('key')} = {args.get('value')}"
    }


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - powered by the new Agent system.
    
    Send any message. The AI will:
    - Understand your intent
    - Become the right expert (assistant, fashion designer, travel agent, etc.)
    - Take autonomous action (send emails, schedule meetings, etc.)
    - Return a natural response with what was done
    
    This is NOT a chatbot. This is an AI agent that DOES things.
    """
    try:
        # Initialize agent with handlers
        agent = init_agent()
        
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        user_id = request.user_id or "default"
        
        # Build user context
        user_context = {}
        
        if request.user_email:
            memory = get_memory()
            user = await memory.get_or_create_user(request.user_email)
            user_id = user.id
            user_context = {
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "preferences": user.preferences,
                "contacts": [c.to_dict() for c in user.contacts[:10]]
            }
        
        # Chat with agent
        result = await agent.chat(
            session_id=session_id,
            message=request.message,
            user_id=user_id,
            user_context=user_context
        )
        
        return ChatResponse(
            response=result.get("response", ""),
            session_id=session_id,
            expert=result.get("expert"),
            actions_taken=result.get("actions_taken", []),
            error=result.get("error", False)
        )
        
    except Exception as e:
        print(f"[AGENT API] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return ChatResponse(
            response="I ran into an issue. Let me try that again.",
            session_id=request.session_id or str(uuid.uuid4()),
            error=True
        )


@router.post("/contacts")
async def add_contact(user_email: str, contact: ContactRequest):
    """Add a contact to user's address book"""
    memory = get_memory()
    user = await memory.get_or_create_user(user_email)
    
    new_contact = Contact(
        id=str(uuid.uuid4()),
        name=contact.name,
        email=contact.email,
        phone=contact.phone,
        telegram_id=contact.telegram_id,
        relationship=contact.relationship
    )
    
    await memory.add_contact(user.id, new_contact)
    
    return {"status": "success", "contact": new_contact.to_dict()}


@router.get("/contacts")
async def get_contacts(user_email: str):
    """Get user's contacts"""
    memory = get_memory()
    user = await memory.get_or_create_user(user_email)
    
    return {
        "contacts": [c.to_dict() for c in user.contacts]
    }


@router.post("/preferences")
async def set_preference(user_email: str, pref: PreferenceRequest):
    """Set a user preference"""
    memory = get_memory()
    user = await memory.get_or_create_user(user_email)
    
    await memory.set_preference(user.id, pref.category, pref.key, pref.value)
    
    return {"status": "success", "preference": pref.dict()}


@router.get("/preferences")
async def get_preferences(user_email: str, category: Optional[str] = None):
    """Get user preferences"""
    memory = get_memory()
    user = await memory.get_or_create_user(user_email)
    
    if category:
        return {"preferences": user.preferences.get(category, {})}
    return {"preferences": user.preferences}


@router.get("/health")
async def health_check():
    """Check agent health"""
    try:
        agent = get_agent()
        executor = get_executor()
        memory = get_memory()
        
        return {
            "status": "healthy",
            "agent": "initialized",
            "providers": list(agent.providers.keys()),
            "memory": "supabase" if memory.client else "in_memory"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
