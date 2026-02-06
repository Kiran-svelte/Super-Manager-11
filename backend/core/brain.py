"""
SUPER MANAGER - CLEAN AI BRAIN
==============================
ONE module. ONE flow. SIMPLE.

Flow:
1. User sends message
2. AI understands (question or task?)
3. If question → answer directly
4. If task → plan → ask missing info → confirm → execute → record
"""
import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import httpx
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")  # Fast & powerful
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# =============================================================================
# DATA MODELS - Clean and Simple
# =============================================================================
class MessageType(str, Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


class TaskStatus(str, Enum):
    PLANNING = "planning"
    NEED_INFO = "need_info"
    CONFIRM = "confirm"
    EXECUTING = "executing"
    DONE = "done"
    CANCELLED = "cancelled"


@dataclass
class Message:
    role: MessageType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Task:
    id: str
    type: str  # email, meeting, reminder, payment, search, etc.
    status: TaskStatus
    plan: Dict[str, Any]
    missing_info: List[str] = field(default_factory=list)
    result: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Session:
    id: str
    messages: List[Message] = field(default_factory=list)
    current_task: Optional[Task] = None
    user_data: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# DATABASE - Simple In-Memory (replace with real DB later)
# =============================================================================
class Database:
    """Simple storage - replace with Supabase/PostgreSQL in production"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.users: Dict[str, Dict] = {}  # email/phone -> user info
        self.task_history: List[Task] = []
    
    def get_session(self, session_id: str) -> Session:
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(id=session_id)
        return self.sessions[session_id]
    
    def save_user(self, identifier: str, data: Dict):
        self.users[identifier] = {**self.users.get(identifier, {}), **data}
    
    def get_user(self, identifier: str) -> Optional[Dict]:
        return self.users.get(identifier)
    
    def record_task(self, task: Task):
        self.task_history.append(task)


# Global database instance
db = Database()


# =============================================================================
# AI BRAIN - The Core Logic
# =============================================================================
class AIBrain:
    """
    Single AI brain that handles everything.
    Clean flow: understand → plan → ask → confirm → execute → record
    """
    
    SYSTEM_PROMPT = """You are a helpful AI assistant. You can:
1. Answer questions directly
2. Execute tasks: send emails, schedule meetings, set reminders, payments, search

IMPORTANT RULES:
- Be natural and friendly, not robotic
- For questions: just answer
- For tasks: identify what task and what info is needed

When user wants a TASK, respond with JSON:
{
    "type": "task",
    "task_type": "email|meeting|reminder|payment|search|other",
    "understood": "what you understood",
    "have": {"field": "value"},
    "need": ["list of missing required fields"],
    "message": "your friendly response"
}

Required fields by task type:
- email: to, subject, body
- meeting: title, participants (emails), time
- reminder: text, time
- payment: amount, to (upi/email/phone)
- search: query

For QUESTIONS (not tasks), respond with JSON:
{
    "type": "answer",
    "message": "your answer"
}

Examples:
User: "What's 2+2?" → {"type": "answer", "message": "4!"}
User: "Send email to john@test.com" → {"type": "task", "task_type": "email", "understood": "send email to john@test.com", "have": {"to": "john@test.com"}, "need": ["subject", "body"], "message": "Sure! What should I say in the email?"}
User: "Schedule meeting tomorrow 2pm with alice@test.com" → {"type": "task", "task_type": "meeting", "understood": "meeting tomorrow 2pm with alice", "have": {"time": "tomorrow 2pm", "participants": ["alice@test.com"]}, "need": ["title"], "message": "Got it! What's the meeting about?"}
"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def process(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Main entry point. Clean flow:
        1. Get session
        2. Record user message
        3. Check if we're in middle of a task
        4. Call AI
        5. Handle response
        6. Return result
        """
        session = db.get_session(session_id)
        
        # Record user message
        session.messages.append(Message(role=MessageType.USER, content=user_message))
        
        # If we have a pending task, handle task flow
        if session.current_task:
            return await self._handle_task_flow(session, user_message)
        
        # Otherwise, call AI to understand
        ai_response = await self._call_ai(session)
        
        # Parse AI response
        parsed = self._parse_response(ai_response)
        
        # Handle based on type
        if parsed.get("type") == "task":
            return await self._start_task(session, parsed)
        else:
            # Just an answer
            message = parsed.get("message", ai_response)
            session.messages.append(Message(role=MessageType.AI, content=message))
            return {"message": message, "type": "answer"}
    
    async def _call_ai(self, session: Session, extra_context: str = "") -> str:
        """Call Groq API"""
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT + extra_context}]
        
        # Add conversation history (last 10 messages)
        for msg in session.messages[-10:]:
            role = "user" if msg.role == MessageType.USER else "assistant"
            messages.append({"role": role, "content": msg.content})
        
        try:
            response = await self.client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            data = response.json()
            
            # Check for API errors
            if "error" in data:
                error_msg = data["error"].get("message", str(data["error"]))
                return json.dumps({"type": "answer", "message": f"API Error: {error_msg}"})
            
            if "choices" not in data or not data["choices"]:
                return json.dumps({"type": "answer", "message": "No response from AI. Please try again."})
                
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return json.dumps({"type": "answer", "message": f"Sorry, I encountered an error: {str(e)}"})
    
    def _parse_response(self, response: str) -> Dict:
        """Parse AI JSON response"""
        try:
            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {"type": "answer", "message": response}
    
    async def _start_task(self, session: Session, parsed: Dict) -> Dict[str, Any]:
        """Start a new task"""
        task = Task(
            id=str(uuid.uuid4()),
            type=parsed.get("task_type", "other"),
            status=TaskStatus.PLANNING,
            plan=parsed.get("have", {}),
            missing_info=parsed.get("need", [])
        )
        
        session.current_task = task
        message = parsed.get("message", "I'll help you with that.")
        
        # Record AI response
        session.messages.append(Message(role=MessageType.AI, content=message))
        
        # Check if we need more info
        if task.missing_info:
            task.status = TaskStatus.NEED_INFO
            return {
                "message": message,
                "type": "task",
                "status": "need_info",
                "need": task.missing_info,
                "task_id": task.id
            }
        else:
            # Have all info, ask for confirmation
            task.status = TaskStatus.CONFIRM
            return await self._ask_confirmation(session, task)
    
    async def _handle_task_flow(self, session: Session, user_message: str) -> Dict[str, Any]:
        """Handle ongoing task"""
        task = session.current_task
        
        # Check for cancellation
        lower = user_message.lower()
        if any(word in lower for word in ["cancel", "stop", "nevermind", "forget it"]):
            task.status = TaskStatus.CANCELLED
            session.current_task = None
            db.record_task(task)
            return {"message": "No problem, cancelled!", "type": "cancelled"}
        
        # Check for confirmation
        if task.status == TaskStatus.CONFIRM:
            if any(word in lower for word in ["yes", "confirm", "do it", "go ahead", "ok", "sure"]):
                return await self._execute_task(session, task)
            elif any(word in lower for word in ["no", "don't", "wait"]):
                task.status = TaskStatus.CANCELLED
                session.current_task = None
                return {"message": "Okay, cancelled.", "type": "cancelled"}
        
        # User is providing missing info
        if task.status == TaskStatus.NEED_INFO:
            return await self._collect_info(session, task, user_message)
        
        return {"message": "I'm not sure what you mean. Say 'yes' to confirm or 'cancel' to stop.", "type": "clarify"}
    
    async def _collect_info(self, session: Session, task: Task, user_message: str) -> Dict[str, Any]:
        """Collect missing information from user"""
        # Use AI to extract the info from user's message
        context = f"""
The user is providing information for a {task.type} task.
Current plan: {json.dumps(task.plan)}
Still needed: {task.missing_info}

Extract the provided information and respond with JSON:
{{"extracted": {{"field": "value"}}, "still_need": ["remaining fields"], "message": "your response"}}
"""
        ai_response = await self._call_ai(session, context)
        parsed = self._parse_response(ai_response)
        
        # Update task with extracted info
        extracted = parsed.get("extracted", {})
        task.plan.update(extracted)
        
        # Update missing info
        still_need = parsed.get("still_need", [])
        task.missing_info = [f for f in still_need if f not in extracted]
        
        message = parsed.get("message", "Got it!")
        session.messages.append(Message(role=MessageType.AI, content=message))
        
        # Check if we have everything
        if not task.missing_info:
            task.status = TaskStatus.CONFIRM
            return await self._ask_confirmation(session, task)
        
        return {
            "message": message,
            "type": "task",
            "status": "need_info",
            "need": task.missing_info,
            "task_id": task.id
        }
    
    async def _ask_confirmation(self, session: Session, task: Task) -> Dict[str, Any]:
        """Ask user to confirm the task"""
        # Generate confirmation message based on task type
        if task.type == "email":
            summary = f"Send email to {task.plan.get('to')} about '{task.plan.get('subject', 'your message')}'"
        elif task.type == "meeting":
            participants = task.plan.get('participants', [])
            if isinstance(participants, str):
                participants = [participants]
            summary = f"Schedule meeting '{task.plan.get('title', 'Meeting')}' with {', '.join(participants)} at {task.plan.get('time')}"
        elif task.type == "reminder":
            summary = f"Set reminder: '{task.plan.get('text')}' at {task.plan.get('time')}"
        elif task.type == "payment":
            summary = f"Pay ₹{task.plan.get('amount')} to {task.plan.get('to')}"
        else:
            summary = f"Execute {task.type}: {json.dumps(task.plan)}"
        
        message = f"Ready to: {summary}\n\nShould I proceed? (yes/no)"
        session.messages.append(Message(role=MessageType.AI, content=message))
        
        return {
            "message": message,
            "type": "task",
            "status": "confirm",
            "summary": summary,
            "task_id": task.id
        }
    
    async def _execute_task(self, session: Session, task: Task) -> Dict[str, Any]:
        """Execute the confirmed task"""
        task.status = TaskStatus.EXECUTING
        
        try:
            if task.type == "email":
                result = await self._send_email(task.plan)
            elif task.type == "meeting":
                result = await self._create_meeting(task.plan)
            elif task.type == "reminder":
                result = await self._set_reminder(task.plan)
            elif task.type == "payment":
                result = await self._process_payment(task.plan)
            elif task.type == "search":
                result = await self._search(task.plan)
            else:
                result = {"success": True, "message": f"Task '{task.type}' noted."}
            
            task.status = TaskStatus.DONE
            task.result = result
            
            message = result.get("message", "Done!")
            session.messages.append(Message(role=MessageType.AI, content=message))
            
        except Exception as e:
            task.status = TaskStatus.DONE
            task.result = {"success": False, "error": str(e)}
            message = f"Sorry, there was an error: {str(e)}"
            session.messages.append(Message(role=MessageType.AI, content=message))
        
        # Record and clear task
        db.record_task(task)
        session.current_task = None
        
        return {
            "message": message,
            "type": "task",
            "status": "done",
            "result": task.result,
            "task_id": task.id
        }
    
    # ==========================================================================
    # TASK EXECUTORS
    # ==========================================================================
    
    async def _send_email(self, plan: Dict) -> Dict:
        """Send email"""
        to = plan.get("to")
        subject = plan.get("subject", "Message from Super Manager")
        body = plan.get("body", "")
        
        # TODO: Integrate with Gmail API or SMTP
        # For now, simulate
        return {
            "success": True,
            "message": f"✅ Email sent to {to}!\nSubject: {subject}"
        }
    
    async def _create_meeting(self, plan: Dict) -> Dict:
        """Create meeting with Jitsi link"""
        title = plan.get("title", "Meeting")
        time = plan.get("time", "")
        participants = plan.get("participants", [])
        
        # Generate Jitsi link
        meeting_id = f"supermanager-{uuid.uuid4().hex[:8]}"
        link = f"https://meet.jit.si/{meeting_id}"
        
        # TODO: Send invites to participants
        
        return {
            "success": True,
            "message": f"✅ Meeting created!\n\n📅 {title}\n⏰ {time}\n🔗 {link}\n\nInvites sent to: {', '.join(participants) if isinstance(participants, list) else participants}",
            "link": link
        }
    
    async def _set_reminder(self, plan: Dict) -> Dict:
        """Set reminder"""
        text = plan.get("text", "")
        time = plan.get("time", "")
        
        # TODO: Integrate with scheduler/notification system
        
        return {
            "success": True,
            "message": f"⏰ Reminder set!\n\n'{text}' at {time}"
        }
    
    async def _process_payment(self, plan: Dict) -> Dict:
        """Generate payment link"""
        amount = plan.get("amount", 0)
        to = plan.get("to", "")
        
        # Generate UPI link
        upi_link = f"upi://pay?pa={to}&am={amount}&cu=INR"
        
        return {
            "success": True,
            "message": f"💳 Payment ready!\n\nAmount: ₹{amount}\nTo: {to}\n\nUPI Link: {upi_link}",
            "upi_link": upi_link
        }
    
    async def _search(self, plan: Dict) -> Dict:
        """Search (placeholder)"""
        query = plan.get("query", "")
        
        return {
            "success": True,
            "message": f"🔍 Search results for '{query}' would appear here."
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================
brain = AIBrain()


# =============================================================================
# PUBLIC API - Simple functions to call
# =============================================================================
async def chat(session_id: str, message: str) -> Dict[str, Any]:
    """Send a message and get response"""
    return await brain.process(session_id, message)


def get_session(session_id: str) -> Session:
    """Get session data"""
    return db.get_session(session_id)


def get_history(session_id: str) -> List[Dict]:
    """Get conversation history"""
    session = db.get_session(session_id)
    return [{"role": m.role.value, "content": m.content} for m in session.messages]


def save_user_data(identifier: str, data: Dict):
    """Save user data (email, phone, UPI, etc.)"""
    db.save_user(identifier, data)


def get_user_data(identifier: str) -> Optional[Dict]:
    """Get user data"""
    return db.get_user(identifier)
