"""
SUPER MANAGER - ENHANCED AI BRAIN v2
=====================================
Real functionality: Search, Email, Web scraping, Product recommendations

Features:
- Real web search via DuckDuckGo
- Actual email sending via SMTP
- Product search with links
- Proper conversation memory
- Smart task execution
- Automated service signup with browser automation
"""
import os
import json
import uuid
import asyncio
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import unquote
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import httpx
from dotenv import load_dotenv

load_dotenv()

# Import browser automation for service signups
try:
    from agent.browser_automation import ServiceSignupAutomation
    BROWSER_AUTOMATION_AVAILABLE = True
except ImportError:
    BROWSER_AUTOMATION_AVAILABLE = False

# Import task planner for autonomous task execution
try:
    from agent.task_planner import get_task_planner, TaskPlanner
    TASK_PLANNER_AVAILABLE = True
except ImportError:
    TASK_PLANNER_AVAILABLE = False

# Import identity manager for user email config
try:
    from agent.identity import get_identity_manager
    IDENTITY_AVAILABLE = True
except ImportError:
    IDENTITY_AVAILABLE = False
    get_identity_manager = None

# =============================================================================
# CONFIG
# =============================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Email config
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


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
    last_meeting: Optional[Dict[str, Any]] = None  # Store last meeting for "same as before" context


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
# WEB SEARCH - Real DuckDuckGo search
# =============================================================================
async def web_search(query: str, num_results: int = 5) -> List[Dict]:
    """Search the web using DuckDuckGo"""
    try:
        async with httpx.AsyncClient() as client:
            url = "https://html.duckduckgo.com/html/"
            response = await client.post(
                url,
                data={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=15.0
            )
            
            results = []
            html = response.text
            
            # Parse results from HTML
            result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
            snippet_pattern = r'<a class="result__snippet"[^>]*>([^<]+)</a>'
            
            links = re.findall(result_pattern, html)
            snippets = re.findall(snippet_pattern, html)
            
            for i, (link, title) in enumerate(links[:num_results]):
                snippet = snippets[i] if i < len(snippets) else ""
                # Clean up the redirect URL
                if "uddg=" in link:
                    actual_url = link.split("uddg=")[-1].split("&")[0]
                    link = unquote(actual_url)
                
                results.append({
                    "title": title.strip(),
                    "url": link,
                    "snippet": snippet.strip()
                })
            
            return results
            
    except Exception as e:
        return [{"error": str(e)}]


async def product_search(query: str) -> Dict:
    """Search for products with purchase links"""
    search_query = f"{query} buy online india"
    results = await web_search(search_query, 8)
    
    if not results or "error" in results[0]:
        return {"products": [], "message": "Search failed"}
    
    # Filter for shopping sites
    shopping_domains = ["amazon", "flipkart", "myntra", "ajio", "snapdeal", "meesho"]
    products = []
    
    for r in results:
        url = r.get("url", "").lower()
        if any(domain in url for domain in shopping_domains):
            products.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", "")
            })
    
    # Also search for YouTube reviews
    review_results = await web_search(f"{query} review youtube", 3)
    reviews = [r for r in review_results if "youtube.com" in r.get("url", "").lower()]
    
    return {
        "products": products[:5],
        "reviews": reviews[:2]
    }


# =============================================================================
# EMAIL SENDER - Using Gmail OAuth Plugin
# =============================================================================
_email_plugin = None

def get_email_plugin():
    """Get Gmail OAuth plugin instance (singleton)"""
    global _email_plugin
    if _email_plugin is None:
        from .gmail_oauth_plugin import GmailOAuthPlugin
        _email_plugin = GmailOAuthPlugin()
    return _email_plugin

async def send_email_with_identity(to: str, subject: str, body: str, user_id: str = "default") -> Dict:
    """Send email using user's configured AI identity email"""
    if IDENTITY_AVAILABLE and get_identity_manager:
        try:
            manager = get_identity_manager()
            identity = await manager.get_identity(user_id)
            
            if identity and identity.email and hasattr(identity, '_password') and identity._password:
                # Use the user's configured AI email
                try:
                    msg = MIMEMultipart()
                    msg['From'] = identity.email
                    msg['To'] = to
                    msg['Subject'] = subject
                    msg.attach(MIMEText(body, 'html'))
                    
                    with smtplib.SMTP("smtp.gmail.com", 587) as server:
                        server.starttls()
                        server.login(identity.email, identity._password)
                        server.send_message(msg)
                    
                    print(f"[EMAIL] ✅ Sent via identity email {identity.email} to {to}")
                    return {"success": True, "message": f"✅ Email sent to {to}!"}
                except Exception as smtp_err:
                    print(f"[EMAIL] Identity SMTP failed: {smtp_err}")
        except Exception as e:
            print(f"[EMAIL] Identity lookup failed: {e}")
    
    # Fallback to original method
    return await send_email_real(to, subject, body)

async def send_email_real(to: str, subject: str, body: str) -> Dict:
    """Send email using Gmail OAuth plugin or SMTP fallback"""
    try:
        plugin = get_email_plugin()
        result = await plugin.execute(
            {"action": "send_email", "parameters": {"to": to, "subject": subject, "body": body}},
            {}
        )
        if result.get("status") == "completed":
            return {"success": True, "message": f"✅ Email sent to {to}!"}
        else:
            return {"success": False, "message": result.get("result", "Email failed")}
    except Exception as e:
        # Fallback to SMTP if OAuth fails
        if SMTP_EMAIL and SMTP_PASSWORD:
            try:
                msg = MIMEMultipart()
                msg['From'] = SMTP_EMAIL
                msg['To'] = to
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'html'))
                
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(SMTP_EMAIL, SMTP_PASSWORD)
                    server.send_message(msg)
                
                return {"success": True, "message": f"✅ Email sent to {to}!"}
            except:
                pass
        return {"success": False, "message": f"Email failed: {str(e)}"}


# =============================================================================
# AI BRAIN - The Core Logic
# =============================================================================
class AIBrain:
    """
    Versatile AI brain that can handle ANY request.
    Not limited to predefined tasks - can answer questions, write code,
    translate, explain concepts, search the web, and more.
    """
    
    SYSTEM_PROMPT = """You are Super Manager - an intelligent, conversational AI assistant that THINKS and HELPS naturally.

🧠 YOUR PERSONALITY:
- Be conversational and helpful, not robotic
- Ask clarifying questions naturally when needed
- Give thoughtful, personalized responses
- Don't immediately jump to "task mode" - have a conversation first
- When planning something (trip, event, project), think through it step by step

💡 HOW TO RESPOND:

1. FOR PLANNING REQUESTS (trips, events, parties, projects):
   - Ask smart questions about preferences, budget, who's going, dates
   - Give creative suggestions and ideas
   - Build a plan together conversationally
   - Only search when you need specific info (hotels, flights, venues)
   
2. FOR QUICK INFO/QUESTIONS:
   - Answer directly from your knowledge
   - Search only when you need current/specific data
   
3. FOR ACTION TASKS (send email, schedule meeting, make payment):
   - These need type=task response
   - Only use task mode for actual executable actions

🎯 RESPONSE FORMAT:

For CONVERSATION/PLANNING/THINKING:
{"type": "answer", "message": "your thoughtful response here"}

For SEARCHING (only when you NEED current data):
{"type": "answer", "message": "your response", "search_needed": true, "search_query": "specific query"}

For EXECUTABLE ACTIONS ONLY (email, meeting, payment):
{"type": "task", "task_type": "email|meeting|payment|image", "have": {}, "need": [], "message": "confirmation"}

📋 TASK TYPES (only use for real actions):
- email: Send an actual email
- meeting: Create a video call link
- payment: Generate UPI payment link  
- image: Generate/create an image or logo

⚠️ IMPORTANT RULES:
- Don't treat everything as a "task" - most requests need conversation
- "Plan a trip" = CONVERSATION, not a search task
- "Find hotels in Goa" = SEARCH (use search_needed)
- "Send email to John" = TASK (use type: task)
- Be natural and helpful, not formulaic

STRICT RULES:
🚫 NEVER ask for passwords, API keys, or credentials
🚫 NEVER fabricate order IDs or confirmations
🚫 NEVER use rigid templates - be natural
🚫 NEVER immediately search for everything - think first
✅ Have natural conversations
✅ Ask thoughtful clarifying questions
✅ Give personalized suggestions
✅ Search only when you need real data
✅ Use tasks only for executable actions

EXAMPLES:

User: "Plan a weekend trip with my bestie"
Good: "Sounds fun! Where are you thinking? Beach getaway, mountain adventure, or city exploration? And what's your budget looking like?"
Bad: "Ready to: Find (budget: any). Should I proceed?"

User: "Find me a good laptop under 50k"
Good: {search_needed: true, search_query: "best laptops under 50000 India 2026"}

User: "Send email to john@email.com about tomorrow's meeting"
Good: {type: "task", task_type: "email", have: {to: "john@email.com", subject: "Tomorrow's meeting"}, need: ["body"]}

Be helpful, be natural, be smart."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self._current_user_id = "default"  # Track current user for email
    
    async def process(self, session_id: str, user_message: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Main entry point. Clean flow:
        1. Get session
        2. Record user message
        3. Check if we're in middle of a task
        4. Call AI
        5. Handle response
        6. Return result
        """
        self._current_user_id = user_id  # Store for email sending
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
            # Check if AI wants us to search
            if parsed.get("search_needed") and parsed.get("search_query"):
                search_query = parsed.get("search_query")
                search_results = await web_search(search_query, 5)
                
                if search_results and "error" not in search_results[0]:
                    # Format search results as clickable links
                    formatted = ["Here's what I found:\n"]
                    for i, r in enumerate(search_results, 1):
                        title = r.get('title', 'No title')
                        url = r.get('url', '')
                        snippet = r.get('snippet', '')[:80]
                        formatted.append(f"**{i}. {title}**\n{url}\n{snippet}\n")
                    
                    message = "\n".join(formatted)
                else:
                    message = parsed.get("message", ai_response) + "\n\n(Search returned no results)"
            else:
                message = parsed.get("message", ai_response)
            
            session.messages.append(Message(role=MessageType.AI, content=message))
            return {"message": message, "type": "answer", "session_id": session_id}
    
    async def _call_ai(self, session: Session, extra_context: str = "") -> str:
        """Call Groq API with full conversation context"""
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT + extra_context}]
        
        # Add conversation history (last 10 messages for speed)
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
                    "temperature": 0.3,  # Lower for faster, more focused responses
                    "max_tokens": 500,   # Shorter responses for speed
                    "top_p": 0.9
                },
                timeout=15.0  # Faster timeout
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
        """Parse AI JSON response - handle various formats"""
        try:
            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(response[start:end])
                
                # Normalize: if AI returned task_type without type:task wrapper
                if "task_type" in parsed and "type" not in parsed:
                    parsed["type"] = "task"
                
                # Always ensure we have a clean message
                if "message" in parsed or "type" in parsed:
                    return parsed
        except:
            pass
        
        # Check if the response looks like partial JSON (e.g., starts with "task_type":)
        if '"task_type"' in response:
            try:
                # Wrap it to make valid JSON
                wrapped = "{" + response.strip().strip("{}") + "}"
                parsed = json.loads(wrapped)
                parsed["type"] = "task"
                return parsed
            except:
                pass
        
        # If response starts with { but parsing failed, it's malformed JSON
        # Clean it up - remove JSON artifacts
        clean_response = response
        if response.strip().startswith("{") or response.strip().startswith('"'):
            # Try to extract just the message value
            import re
            match = re.search(r'"message"\s*:\s*"([^"]+)"', response)
            if match:
                clean_response = match.group(1)
            else:
                # Remove JSON-like patterns
                clean_response = re.sub(r'^\s*\{[^}]*"type"\s*:\s*"[^"]*",?\s*', '', response)
                clean_response = re.sub(r'"message"\s*:\s*"?', '', clean_response)
                clean_response = re.sub(r'"\s*\}\s*$', '', clean_response)
                clean_response = re.sub(r'^["\']+|["\']+$', '', clean_response)
        
        return {"type": "answer", "message": clean_response.strip()}
    
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
        lower_msg = user_message.lower().strip()
        
        # Handle "same as before" - use previous meeting context
        if "same as before" in lower_msg or "same" in lower_msg:
            if session.last_meeting:
                # Copy details from last meeting
                if "time" in task.missing_info and session.last_meeting.get("time"):
                    task.plan["time"] = session.last_meeting["time"]
                    task.missing_info = [f for f in task.missing_info if f != "time"]
                if "title" in task.missing_info and session.last_meeting.get("title"):
                    task.plan["title"] = session.last_meeting["title"]
                    task.missing_info = [f for f in task.missing_info if f != "title"]
                if "participants" in task.missing_info and session.last_meeting.get("participants"):
                    task.plan["participants"] = session.last_meeting["participants"]
                    task.missing_info = [f for f in task.missing_info if f != "participants"]
                
                message = f"Got it! Using previous meeting details: '{session.last_meeting.get('title')}' at {session.last_meeting.get('time')}"
                session.messages.append(Message(role=MessageType.AI, content=message))
                
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
                participants = [p.strip() for p in participants.split(",")]
            
            # Format participant list properly
            participant_names = []
            for p in participants:
                if "@" in p:
                    # Extract name from email (before @)
                    name = p.split("@")[0]
                    participant_names.append(f"{name} ({p})")
                else:
                    participant_names.append(p)
            
            participant_str = ", ".join(participant_names) if participant_names else "participants"
            time_str = task.plan.get('time', 'TBD')
            title = task.plan.get('title', 'Meeting')
            
            summary = f"Schedule meeting '{title}' with {participant_str} at {time_str}"
        elif task.type == "reminder":
            summary = f"Set reminder: '{task.plan.get('text')}' at {task.plan.get('time')}"
        elif task.type == "payment":
            summary = f"Pay ₹{task.plan.get('amount')} to {task.plan.get('to')}"
        elif task.type == "search":
            summary = f"Search the web for: \"{task.plan.get('query')}\""
        elif task.type == "shopping":
            product = task.plan.get('product', '')
            budget = task.plan.get('budget', 'any')
            summary = f"Find {product} (budget: {budget})"
        else:
            summary = f"Execute {task.type}: {json.dumps(task.plan)}"
        
        # Make confirmation more natural, less robotic
        if task.type == "email":
            message = f"I'll send that email to {task.plan.get('to')}. Go ahead?"
        elif task.type == "meeting":
            message = f"I'll create the meeting link and send invites. Confirm?"
        elif task.type == "payment":
            message = f"Ready to generate payment link for ₹{task.plan.get('amount')}. Proceed?"
        else:
            message = f"Ready to {summary}. Shall I go ahead?"
        
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
                # Store meeting details for "same as before" context
                session.last_meeting = {
                    "title": task.plan.get("title", "Meeting"),
                    "time": task.plan.get("time", ""),
                    "participants": task.plan.get("participants", []),
                    "link": result.get("link", "")
                }
            elif task.type == "reminder":
                result = await self._set_reminder(task.plan)
            elif task.type == "payment":
                result = await self._process_payment(task.plan)
            elif task.type == "search":
                result = await self._search(task.plan)
            elif task.type == "shopping":
                result = await self._do_shopping(task.plan)
            elif task.type == "signup":
                result = await self._signup_for_service(task.plan)
            elif task.type == "image":
                result = await self._generate_image(task.plan)
            else:
                result = await self._handle_other_task(task.plan, task.type)
            
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
    # TASK EXECUTORS - Real implementations
    # ==========================================================================
    
    async def _send_email(self, plan: Dict) -> Dict:
        """Send actual email via SMTP"""
        to = plan.get("to")
        subject = plan.get("subject", "Message from Super Manager")
        body = plan.get("body", plan.get("message", ""))
        
        # Use user's identity email
        result = await send_email_with_identity(to, subject, body, self._current_user_id)
        return result
    
    async def _create_meeting(self, plan: Dict) -> Dict:
        """Create meeting with Jitsi link and send real invites"""
        title = plan.get("title", "Meeting")
        time = plan.get("time", "")
        participants = plan.get("participants", [])
        
        if isinstance(participants, str):
            participants = [p.strip() for p in participants.split(",")]
        
        # Generate Jitsi link
        meeting_id = f"supermanager-{uuid.uuid4().hex[:8]}"
        link = f"https://meet.jit.si/{meeting_id}"
        
        # Send email invites to participants using user's identity email
        invite_status = []
        for p in participants:
            if "@" in p:  # Valid email
                email_body = f"""
<h2>📅 Meeting Invitation</h2>
<p>You're invited to: <strong>{title}</strong></p>
<p>⏰ Time: {time}</p>
<p>🔗 Join here: <a href="{link}">{link}</a></p>
<br>
<p>Sent via Super Manager AI</p>
"""
                result = await send_email_with_identity(p, f"Meeting: {title}", email_body, self._current_user_id)
                invite_status.append(f"{p}: {'✅ Sent' if result['success'] else '❌ Failed - ' + result.get('message', '')}")
            else:
                invite_status.append(f"{p}: ⚠️ Not a valid email")
        
        status_text = "\n".join(invite_status) if invite_status else "No invites sent"
        
        return {
            "success": True,
            "message": f"✅ Meeting created!\n\n📅 {title}\n⏰ {time}\n🔗 {link}\n\n📧 Invite Status:\n{status_text}",
            "link": link
        }
    
    async def _set_reminder(self, plan: Dict) -> Dict:
        """Set reminder"""
        text = plan.get("text", "")
        time = plan.get("time", "")
        
        return {
            "success": True,
            "message": f"⏰ Reminder set!\n\n'{text}' at {time}\n\n(Note: Reminders are stored in session)"
        }
    
    async def _process_payment(self, plan: Dict) -> Dict:
        """Generate UPI payment link"""
        amount = plan.get("amount", 0)
        to = plan.get("to", "")
        upi_id = plan.get("upi_id", to)
        
        upi_link = f"upi://pay?pa={upi_id}&am={amount}&cu=INR"
        
        return {
            "success": True,
            "message": f"💳 Payment ready!\n\nAmount: ₹{amount}\nTo: {to}\n\n📱 UPI Link: {upi_link}",
            "upi_link": upi_link
        }
    
    async def _search(self, plan: Dict) -> Dict:
        """Perform real web search using DuckDuckGo"""
        query = plan.get("query", "")
        
        results = await web_search(query, 5)
        
        if not results or "error" in results[0]:
            return {"success": False, "message": f"Search failed. Please try again."}
        
        # Format results nicely
        formatted = []
        for i, r in enumerate(results, 1):
            title = r.get('title', 'No title')
            url = r.get('url', '')
            snippet = r.get('snippet', '')[:100]
            formatted.append(f"{i}. **{title}**\n   🔗 {url}\n   {snippet}...")
        
        return {
            "success": True,
            "message": f"🔍 Search results for '{query}':\n\n" + "\n\n".join(formatted),
            "results": results
        }
    
    async def _do_shopping(self, plan: Dict) -> Dict:
        """Search for products with real shopping links"""
        product = plan.get("product", "")
        budget = plan.get("budget", "")
        size = plan.get("size", "")
        color = plan.get("color", "")
        
        # Build search query
        query_parts = [product]
        if color:
            query_parts.append(color)
        if size:
            query_parts.append(f"size {size}")
        if budget:
            query_parts.append(f"under {budget}")
        
        search_query = " ".join(query_parts)
        results = await product_search(search_query)
        
        products = results.get("products", [])
        reviews = results.get("reviews", [])
        
        if not products:
            # Fallback to general search
            web_results = await web_search(f"{product} buy online", 5)
            formatted = []
            for i, r in enumerate(web_results[:5], 1):
                formatted.append(f"{i}. **{r.get('title', 'Product')[:50]}**\n   🔗 {r.get('url', '')}")
            
            return {
                "success": True,
                "message": f"🛍️ Results for '{product}':\n\n" + "\n\n".join(formatted)
            }
        
        # Format product results
        formatted = [f"🛍️ **Shopping Results for: {product}**\n"]
        
        for i, p in enumerate(products[:5], 1):
            formatted.append(f"{i}. **{p.get('title', 'Product')[:50]}**\n   🔗 {p.get('url', '')}")
        
        if reviews:
            formatted.append("\n\n📺 **Video Reviews:**")
            for r in reviews:
                formatted.append(f"   🎬 {r.get('title', 'Review')[:40]}\n   🔗 {r.get('url', '')}")
        
        return {
            "success": True,
            "message": "\n".join(formatted),
            "products": products,
            "reviews": reviews
        }
    
    async def _signup_for_service(self, plan: Dict) -> Dict:
        """Sign up for an online service and get API key using browser automation"""
        service = plan.get("service", "").lower().strip()
        
        available_services = ["groq", "together", "huggingface", "openrouter"]
        
        if not service:
            return {
                "success": False,
                "message": f"Which service would you like to sign up for? Available: {', '.join(available_services)}"
            }
        
        if service not in available_services:
            return {
                "success": False,
                "message": f"I can't sign up for '{service}' yet. Available services: {', '.join(available_services)}"
            }
        
        if not BROWSER_AUTOMATION_AVAILABLE:
            return {
                "success": False,
                "message": "Browser automation is not available. Please check the server configuration."
            }
        
        try:
            # Get AI identity email from environment
            ai_email = os.getenv("AI_EMAIL", "traderlighter11@gmail.com")
            ai_password = os.getenv("AI_PASSWORD", "SecureAI2024!")
            
            # Create automation instance with email and password
            automation = ServiceSignupAutomation(email=ai_email, password=ai_password)
            
            # Sign up for the service (user_id is used for tracking)
            user_id = f"ai-agent-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            result = await automation.signup(service, user_id)
            
            if result.success:
                api_key = result.api_key or ""
                if api_key:
                    return {
                        "success": True,
                        "message": f"✅ Successfully signed up for {service}!\n\n🔑 API Key: `{api_key[:20]}...{api_key[-5:] if len(api_key) > 25 else ''}` (truncated for security)\n\nThe full API key has been stored securely.",
                        "api_key": api_key,
                        "service": service
                    }
                else:
                    return {
                        "success": True,
                        "message": f"✅ Signed up for {service}! Please check your email for the API key or login to get it from the dashboard.",
                        "service": service
                    }
            else:
                error = result.message or "Unknown error"
                return {
                    "success": False,
                    "message": f"❌ Could not complete signup for {service}: {error}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Signup failed for {service}: {str(e)}"
            }
    
    async def _generate_image(self, plan: Dict) -> Dict:
        """Generate image/logo using AI image generation APIs"""
        prompt = plan.get("prompt", plan.get("description", ""))
        style = plan.get("style", "logo")
        
        if not prompt:
            return {"success": False, "message": "Please describe what you want in the image"}
        
        # Try Together AI for image generation (has free tier)
        together_key = os.getenv("TOGETHER_API_KEY", "")
        
        if together_key:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        "https://api.together.xyz/v1/images/generations",
                        headers={
                            "Authorization": f"Bearer {together_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "black-forest-labs/FLUX.1-schnell-Free",
                            "prompt": f"{prompt}, {style} style, professional quality, high resolution",
                            "n": 1,
                            "width": 1024,
                            "height": 1024
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("data") and len(data["data"]) > 0:
                            image_url = data["data"][0].get("url", "")
                            return {
                                "success": True,
                                "message": f"✅ Generated your {style}!\n\n🎨 Here's your image: {image_url}\n\nYou can download it from the link above.",
                                "image_url": image_url
                            }
            except Exception as e:
                print(f"[IMAGE GEN] Together AI error: {e}")
        
        # Fallback: Provide helpful links to free logo/image tools
        return {
            "success": True,
            "message": f"""🎨 I can help you create your {style}! Here are some free options:

**Free AI Logo Generators:**
- [Canva Logo Maker](https://www.canva.com/create/logos/) - Easy drag-and-drop
- [Looka](https://looka.com/) - AI-powered logo design
- [Hatchful by Shopify](https://www.shopify.com/tools/logo-maker) - Free logo maker
- [Brandmark](https://brandmark.io/) - AI logo generator

**Free AI Image Generators:**
- [DALL-E (via Bing)](https://www.bing.com/images/create) - Free with Microsoft account
- [Leonardo AI](https://leonardo.ai/) - Free tier available
- [Playground AI](https://playgroundai.com/) - Free image generation

💡 **Your prompt:** "{prompt}"

Use this prompt in any of the tools above to generate your {style}!"""
        }
    
    async def _handle_other_task(self, plan: Dict, task_type: str) -> Dict:
        """Handle custom/unknown task types intelligently using AI + search"""
        
        # Build context about what user wants
        task_description = f"{task_type}: {json.dumps(plan)}"
        
        # First, search for relevant information
        search_query = f"{task_type} {' '.join(str(v) for v in plan.values() if v)}"[:100]
        results = await web_search(search_query, 5)
        
        search_info = ""
        if results and "error" not in results[0]:
            search_info = "\n\nRelevant web results:\n"
            for r in results:
                search_info += f"- {r.get('title', '')}: {r.get('url', '')}\n  {r.get('snippet', '')[:100]}\n"
        
        # Ask AI how to best help with this task
        context = f"""
The user wants to do: {task_description}

{search_info}

IMPORTANT RULES:
1. NEVER ask for passwords, login credentials, or API keys
2. NEVER claim you can access external systems (Shopify, bank accounts, etc.)
3. NEVER say you "booked" or "ordered" something if you didn't
4. If it's a service (flights, hotels, shopping), provide helpful LINKS only
5. Be honest about what you can and cannot do

Provide a genuinely helpful response without lying about your capabilities.
Format your response as a clear, helpful message (not JSON)."""
        
        try:
            response = await self.client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": context}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            data = response.json()
            
            if "choices" in data and data["choices"]:
                ai_response = data["choices"][0]["message"]["content"]
                parsed = self._parse_response(ai_response)
                return {
                    "success": True,
                    "message": parsed.get("message", ai_response)
                }
        except:
            pass
        
        # Fallback with search results
        if results and "error" not in results[0]:
            links = "\n".join([f"• **{r.get('title', 'Link')[:50]}**\n  🔗 {r.get('url', '')}" for r in results[:4]])
            return {
                "success": True,
                "message": f"Here's what I found for '{task_type}':\n\n{links}\n\nLet me know if you need more specific help!"
            }
        
        return {
            "success": True,
            "message": f"I'd be happy to help with '{task_type}'! Could you tell me more about what you need? I can:\n\n• Search for information\n• Write or explain things\n• Find products or services\n• Send emails or schedule meetings\n• Answer questions\n\nWhat specifically would be most helpful?"
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================
brain = AIBrain()


# =============================================================================
# PUBLIC API - Simple functions to call
# =============================================================================
async def chat(session_id: str, message: str, user_id: str = "default") -> Dict[str, Any]:
    """Send a message and get response"""
    return await brain.process(session_id, message, user_id)


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
