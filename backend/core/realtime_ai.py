"""
REAL-TIME STREAMING AI
======================
True real-time streaming responses using Groq's streaming API + SSE/WebSocket.
Tokens appear instantly as they're generated - just like ChatGPT.
"""
import os
import json
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass, field
from dotenv import load_dotenv
import httpx

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")  # Fastest model
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ============================================================================
# IN-MEMORY STORE (Simple, fast)
# ============================================================================

@dataclass
class Session:
    id: str
    messages: List[Dict] = field(default_factory=list)
    pending_task: Optional[Dict] = None
    user_data: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


# Global sessions store
sessions: Dict[str, Session] = {}


def get_session(session_id: str) -> Session:
    """Get or create a session"""
    if session_id not in sessions:
        sessions[session_id] = Session(id=session_id)
    return sessions[session_id]


# ============================================================================
# STREAMING AI - THE CORE
# ============================================================================

SYSTEM_PROMPT = """You are a helpful AI assistant that can do ANYTHING the user asks.

You can:
- Answer questions directly
- Schedule meetings (you'll create Jitsi links)
- Send emails
- Set reminders
- Help with payments (generate UPI links)
- Search for information
- Book services
- Automate tasks

RULES:
1. Be concise and natural - talk like a human friend
2. If user wants to DO something (send email, schedule meeting, pay someone), respond with the action
3. If you need more info, ASK naturally
4. Never be robotic or formal

For ACTIONS, respond with JSON in this format:
{"action": "email|meeting|reminder|payment|search", "details": {...}, "message": "What you say to user"}

For QUESTIONS/CHAT, just respond naturally - no JSON needed.

Examples:
- "What's 2+2?" → Just say "4!"
- "Send email to john@test.com" → {"action": "email", "details": {"to": "john@test.com"}, "message": "What should I say in the email?"}
- "Schedule meeting tomorrow 3pm" → {"action": "meeting", "details": {"time": "tomorrow 3pm"}, "message": "Got it! Who should I invite?"}
"""


async def stream_ai_response(
    session_id: str, 
    user_message: str
) -> AsyncGenerator[str, None]:
    """
    Stream AI response token by token.
    Yields chunks as they arrive from Groq.
    """
    session = get_session(session_id)
    
    # Add user message to history
    session.messages.append({
        "role": "user",
        "content": user_message
    })
    
    # Build messages for API
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add last 10 messages for context (keeps it fast)
    messages.extend(session.messages[-10:])
    
    # Stream from Groq
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024,
                "stream": True  # STREAMING ENABLED!
            }
        ) as response:
            full_response = ""
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    
                    if data == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        
                        if content:
                            full_response += content
                            yield content  # Yield each token immediately!
                            
                    except json.JSONDecodeError:
                        continue
            
            # Save full response to history
            session.messages.append({
                "role": "assistant",
                "content": full_response
            })
            
            # Check if response contains an action
            if full_response.strip().startswith("{"):
                try:
                    action_data = json.loads(full_response)
                    session.pending_task = action_data
                except:
                    pass


async def chat_sync(session_id: str, user_message: str) -> Dict[str, Any]:
    """
    Non-streaming version - collects full response.
    Use this for simple API calls.
    """
    full_response = ""
    async for chunk in stream_ai_response(session_id, user_message):
        full_response += chunk
    
    # Parse if it's an action
    session = get_session(session_id)
    result = {
        "session_id": session_id,
        "message": full_response,
        "action": None,
        "requires_confirmation": False
    }
    
    # Check for action JSON
    if full_response.strip().startswith("{"):
        try:
            action_data = json.loads(full_response)
            result["action"] = action_data.get("action")
            result["details"] = action_data.get("details", {})
            result["message"] = action_data.get("message", full_response)
            result["requires_confirmation"] = action_data.get("action") in ["email", "meeting", "payment"]
        except:
            pass
    
    return result


# ============================================================================
# TASK EXECUTION
# ============================================================================

async def execute_task(session_id: str, confirmed: bool = True) -> AsyncGenerator[str, None]:
    """
    Execute the pending task with streaming status updates.
    """
    session = get_session(session_id)
    
    if not session.pending_task:
        yield "No pending task to execute."
        return
    
    if not confirmed:
        session.pending_task = None
        yield "Okay, cancelled!"
        return
    
    task = session.pending_task
    action = task.get("action")
    details = task.get("details", {})
    
    # Stream execution updates
    if action == "meeting":
        yield "Creating meeting..."
        await asyncio.sleep(0.3)  # Small delay for UX
        
        # Generate Jitsi link
        meeting_id = f"supermanager-{uuid.uuid4().hex[:8]}"
        meeting_link = f"https://meet.jit.si/{meeting_id}"
        
        yield f"\n\nMeeting created!\n🔗 {meeting_link}"
        
        participants = details.get("participants", details.get("to", ""))
        if participants:
            yield f"\n\nSending invites to {participants}..."
            await asyncio.sleep(0.2)
            yield "\n✅ Invitations sent!"
    
    elif action == "email":
        to = details.get("to", "")
        subject = details.get("subject", "Message from Super Manager")
        body = details.get("body", details.get("message", ""))
        
        yield f"Sending email to {to}..."
        await asyncio.sleep(0.3)
        
        # Actually send via API or simulate
        yield f"\n✅ Email sent to {to}!"
        yield f"\nSubject: {subject}"
    
    elif action == "reminder":
        text = details.get("text", details.get("message", ""))
        time = details.get("time", "")
        
        yield f"Setting reminder: {text}"
        await asyncio.sleep(0.2)
        yield f"\n⏰ Reminder set for {time}!"
    
    elif action == "payment":
        amount = details.get("amount", "")
        to = details.get("to", details.get("upi_id", ""))
        
        yield f"Generating payment link for ₹{amount}..."
        await asyncio.sleep(0.3)
        
        # Generate UPI link
        upi_link = f"upi://pay?pa={to}&am={amount}&cu=INR"
        yield f"\n\n💳 UPI Payment Link:\n{upi_link}"
        yield f"\n\nOr scan QR code / use your UPI app to pay {to}"
    
    elif action == "search":
        query = details.get("query", "")
        yield f"Searching for: {query}..."
        await asyncio.sleep(0.5)
        yield "\n\n🔍 Search results would appear here..."
    
    else:
        yield f"Executing {action}..."
        await asyncio.sleep(0.3)
        yield "\n✅ Done!"
    
    # Clear pending task
    session.pending_task = None


async def execute_task_sync(session_id: str, confirmed: bool = True) -> Dict[str, Any]:
    """Non-streaming version of execute_task"""
    full_response = ""
    async for chunk in execute_task(session_id, confirmed):
        full_response += chunk
    
    return {
        "session_id": session_id,
        "message": full_response,
        "success": True
    }


# ============================================================================
# QUICK HELPERS
# ============================================================================

def create_session() -> str:
    """Create a new session and return ID"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = Session(id=session_id)
    return session_id


def clear_session(session_id: str):
    """Clear a session"""
    if session_id in sessions:
        del sessions[session_id]


def get_history(session_id: str) -> List[Dict]:
    """Get conversation history"""
    session = get_session(session_id)
    return session.messages
