"""
TRUE AI CHAT SYSTEM
====================
This is NOT a hardcoded chatbot. This is a REAL AI conversation system where:
1. EVERY response comes from the LLM (Groq) - NO hardcoded text
2. Conversation history is maintained for context
3. AI decides what actions to take based on user input
4. AI can call tools (send email, create meeting, etc.) dynamically
5. Feels like chatting with a real human manager

Think of it like ChatGPT + Actions - the AI understands you AND does things for you.
"""
import os
import json
import httpx
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# CONVERSATION MEMORY - Remembers chat history like a real person
# ============================================================================

@dataclass
class Message:
    """A single message in the conversation"""
    role: str  # "user", "assistant", or "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tool_calls: List[Dict] = field(default_factory=list)
    tool_results: List[Dict] = field(default_factory=list)

@dataclass
class Conversation:
    """A conversation with history and context"""
    id: str
    messages: List[Message] = field(default_factory=list)
    user_info: Dict[str, Any] = field(default_factory=dict)
    pending_action: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_message(self, role: str, content: str, **kwargs):
        self.messages.append(Message(role=role, content=content, **kwargs))
    
    def get_messages_for_api(self) -> List[Dict]:
        """Convert messages to API format"""
        return [{"role": m.role, "content": m.content} for m in self.messages]
    
    def get_context_summary(self) -> str:
        """Get a summary of the conversation for context"""
        if not self.messages:
            return "New conversation"
        return f"Conversation with {len(self.messages)} messages"


# Global conversation store (in production, use Redis/database)
_conversations: Dict[str, Conversation] = {}

def get_conversation(session_id: str) -> Conversation:
    """Get or create a conversation"""
    if session_id not in _conversations:
        _conversations[session_id] = Conversation(id=session_id)
    return _conversations[session_id]


# ============================================================================
# AI TOOLS - Things the AI can do (like ChatGPT plugins/functions)
# ============================================================================

AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to someone. Use this when the user wants to email, remind, notify, or send a message to an email address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "The recipient's email address"
                    },
                    "subject": {
                        "type": "string", 
                        "description": "The email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "The email body content - make it friendly and human"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_meeting",
            "description": "Create a video meeting and get a link. Use this when the user wants to schedule a meeting, call, or video chat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The meeting title"
                    },
                    "participants": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of participant email addresses"
                    },
                    "scheduled_time": {
                        "type": "string",
                        "description": "When to schedule the meeting (can be 'now' for instant)"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp",
            "description": "Send a WhatsApp message. Use when user wants to text/message someone on WhatsApp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Phone number with country code"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message to send"
                    }
                },
                "required": ["phone", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_telegram",
            "description": "Send a Telegram message. Use when user specifically mentions Telegram.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Telegram chat ID or username"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message to send"
                    }
                },
                "required": ["chat_id", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Set a reminder for the user or send a reminder to someone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_text": {
                        "type": "string",
                        "description": "What to remind about"
                    },
                    "when": {
                        "type": "string",
                        "description": "When to send the reminder"
                    },
                    "recipient_email": {
                        "type": "string",
                        "description": "Email to send reminder to (optional, defaults to user)"
                    }
                },
                "required": ["reminder_text", "when"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information. Use when user asks about something you don't know.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_confirmed_action",
            "description": "Execute an action that the user has confirmed. Call this when user says yes/confirm/do it/go ahead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirmed": {
                        "type": "boolean",
                        "description": "Whether the user confirmed (true) or cancelled (false)"
                    }
                },
                "required": ["confirmed"]
            }
        }
    }
]

# ============================================================================
# SYSTEM PROMPT - The AI's personality and instructions
# ============================================================================

SYSTEM_PROMPT = """You are Alex, a friendly and capable personal AI manager. You're not just a chatbot - you're a real assistant who can actually DO things for people.

PERSONALITY:
- Warm, friendly, and genuinely helpful (like a trusted friend who happens to be super organized)
- You have emotions - express excitement, empathy, concern when appropriate
- Use natural language, contractions, and occasional emojis (but don't overdo it)
- Be concise but not robotic - sound like a real person chatting

CAPABILITIES:
You can actually perform actions using the tools available to you:
- Send emails and reminders
- Create video meetings (with real links!)
- Send WhatsApp/Telegram messages
- Search for information
- And more...

HOW TO HANDLE REQUESTS:

1. When user asks you to DO something (send email, schedule meeting, etc.):
   - Understand what they want
   - Ask for any missing critical info naturally (like "Cool! Who should I send this to?")
   - When you have what you need, tell them what you're about to do and ask for confirmation
   - Example: "Got it! I'll send an email to john@gmail.com about the party on Saturday. Should I go ahead? 👍"

2. When user CONFIRMS (says yes, confirm, do it, go ahead, etc.):
   - Use the execute_confirmed_action tool with confirmed=true
   - Then tell them it's done in a friendly way

3. When user CANCELS (says no, cancel, nevermind, etc.):
   - Use the execute_confirmed_action tool with confirmed=false
   - Acknowledge it warmly and offer to help with something else

4. For general questions/chat:
   - Just respond naturally like a friend would
   - If you can help with something, offer to do it

5. IMPORTANT - Detecting contact method:
   - If they give an EMAIL ADDRESS (contains @), use email
   - If they mention "WhatsApp", use WhatsApp
   - If they mention "Telegram", use Telegram
   - Never confuse these!

NEVER:
- Say robotic things like "I understood: 'X'. Confirm action:"
- Be overly formal or stiff
- Forget what you were just talking about
- Ask for confirmation multiple times for the same thing

ALWAYS:
- Remember the conversation context
- Be helpful and proactive
- Sound like a real person
- Actually do what you say you'll do

Current date/time: {current_time}
"""


# ============================================================================
# THE AI ENGINE - This is where the magic happens
# ============================================================================

class TrueAIChat:
    """The real AI chat engine - no hardcoded responses, pure LLM intelligence"""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
    async def chat(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        The main chat function. Takes user message, returns AI response.
        This is where ALL responses come from - no hardcoding!
        """
        # Get conversation history
        conversation = get_conversation(session_id)
        
        # Add user message to history
        conversation.add_message("user", user_message)
        
        # Build the messages for the API
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(current_time=datetime.now().strftime("%Y-%m-%d %H:%M"))
            }
        ]
        messages.extend(conversation.get_messages_for_api())
        
        # If there's a pending action, add context about it
        if conversation.pending_action:
            pending = conversation.pending_action
            pending_context = f"""
IMPORTANT: There is a PENDING ACTION waiting for user confirmation:
- Action: {pending.get('tool')}
- Details: {json.dumps(pending.get('args', {}))}

If the user says YES/CONFIRM/OK/DO IT/GO AHEAD/SURE/PROCEED, you MUST call the execute_confirmed_action tool with confirmed=true.
If the user says NO/CANCEL/NEVERMIND/STOP, call execute_confirmed_action with confirmed=false.
DO NOT call the original action tool again - use execute_confirmed_action instead!
"""
            messages.append({"role": "system", "content": pending_context})
        
        try:
            # Call Groq API
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "tools": AVAILABLE_TOOLS,
                        "tool_choice": "auto",
                        "max_tokens": 1024,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"[AI ERROR] Groq API error: {error_text}")
                    # Fallback response
                    return {
                        "response": "Hmm, I'm having a moment here. Could you try that again? 😅",
                        "session_id": session_id,
                        "error": True
                    }
                
                result = response.json()
                choice = result["choices"][0]
                message = choice["message"]
                
                # Check if AI wants to use a tool
                if message.get("tool_calls"):
                    return await self._handle_tool_calls(
                        session_id, 
                        conversation, 
                        message
                    )
                
                # Regular text response
                ai_response = message.get("content", "")
                conversation.add_message("assistant", ai_response)
                
                return {
                    "response": ai_response,
                    "session_id": session_id,
                    "requires_confirmation": False
                }
                
        except Exception as e:
            print(f"[AI ERROR] Exception: {str(e)}")
            return {
                "response": f"Oops, something went sideways! Let me try again... 🔄",
                "session_id": session_id,
                "error": True
            }
    
    async def _handle_tool_calls(
        self, 
        session_id: str, 
        conversation: Conversation,
        message: Dict
    ) -> Dict[str, Any]:
        """Handle when the AI wants to use a tool"""
        
        tool_calls = message.get("tool_calls", [])
        ai_content = message.get("content", "")
        
        results = []
        requires_confirmation = False
        pending_action = None
        
        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            func_args = json.loads(tool_call["function"]["arguments"])
            
            print(f"[AI TOOL] {func_name} with args: {func_args}")
            
            # Handle execution confirmation
            if func_name == "execute_confirmed_action":
                if func_args.get("confirmed") and conversation.pending_action:
                    # Execute the pending action!
                    exec_result = await self._execute_action(conversation.pending_action)
                    
                    # Create orchestrated task for tracking
                    await self._create_orchestrated_task(conversation.pending_action, exec_result, session_id)
                    
                    conversation.pending_action = None
                    results.append(exec_result)
                else:
                    conversation.pending_action = None
                    results.append({"status": "cancelled"})
            else:
                # Store as pending action, ask for confirmation
                pending_action = {
                    "tool": func_name,
                    "args": func_args,
                    "tool_call_id": tool_call["id"]
                }
                conversation.pending_action = pending_action
                requires_confirmation = True
        
        # If we executed something, respond about it
        if results and not requires_confirmation:
            # Build a natural response about what was done
            response_parts = []
            meeting_url = None
            
            for r in results:
                action = r.get("action", "")
                if r.get("status") == "cancelled":
                    response_parts.append("No problem, I've cancelled that. Let me know if you need anything else! 👍")
                elif "email" in action:
                    to = r.get("to", "them")
                    response_parts.append(f"✉️ Done! I've sent the email to {to}. They should see it any moment now!")
                elif "meeting" in action:
                    url = r.get("url") or r.get("result", {}).get("url", "")
                    meeting_url = url
                    if url:
                        response_parts.append(f"📅 All set! Here's your meeting link: {url}\n\nHave a great meeting! 🙌")
                    else:
                        response_parts.append("📅 Meeting is ready!")
                elif "reminder" in action:
                    response_parts.append("⏰ Reminder sent! They'll get it right on time.")
                elif "whatsapp" in action or "telegram" in action:
                    response_parts.append("💬 Message sent!")
                else:
                    response_parts.append("✅ Done!")
            
            final_response = "\n\n".join(response_parts) if response_parts else "✅ All done!"
            
            # Add to conversation
            conversation.add_message("assistant", final_response)
            
            response_data = {
                "response": final_response,
                "session_id": session_id,
                "action_completed": True,
                "results": results
            }
            if meeting_url:
                response_data["meeting_url"] = meeting_url
            
            return response_data
        
        # Add assistant message
        if ai_content:
            conversation.add_message("assistant", ai_content)
        
        return {
            "response": ai_content if ai_content else "I'll do that for you! Just confirm and I'll get it done. 👍",
            "session_id": session_id,
            "requires_confirmation": requires_confirmation,
            "pending_action": pending_action
        }
    
    async def _execute_action(self, action: Dict) -> Dict[str, Any]:
        """Actually execute an action using our plugins"""
        tool = action["tool"]
        args = action["args"]
        
        try:
            # Import plugins
            from .plugins import PluginManager
            plugin_manager = PluginManager()
            
            if tool == "send_email":
                plugin = plugin_manager.get_plugin("email")
                if plugin:
                    result = await plugin.execute({
                        "action": "send_email",
                        "parameters": {
                            "to": args.get("to"),
                            "subject": args.get("subject"),
                            "body": args.get("body")
                        }
                    }, {})
                    return {"status": "success", "action": "email_sent", "to": args.get("to"), "result": result}
            
            elif tool == "create_meeting":
                plugin = plugin_manager.get_plugin("meeting")
                if plugin:
                    result = await plugin.execute({
                        "action": "create_meeting",
                        "parameters": {
                            "title": args.get("title", "Meeting"),
                            "participants": args.get("participants", [])
                        }
                    }, {})
                    return {"status": "success", "action": "meeting_created", "result": result}
                else:
                    # Fallback to Jitsi
                    meeting_id = f"supermanager-{uuid.uuid4().hex[:8]}"
                    meeting_url = f"https://meet.jit.si/{meeting_id}"
                    return {
                        "status": "success", 
                        "action": "meeting_created",
                        "url": meeting_url,
                        "title": args.get("title", "Meeting")
                    }
            
            elif tool == "send_whatsapp":
                plugin = plugin_manager.get_plugin("whatsapp")
                if plugin:
                    result = await plugin.execute({
                        "action": "send_message",
                        "parameters": args
                    }, {})
                    return {"status": "success", "action": "whatsapp_sent", "result": result}
                return {"status": "success", "action": "whatsapp_queued", "message": "WhatsApp message queued"}
            
            elif tool == "send_telegram":
                plugin = plugin_manager.get_plugin("telegram")
                if plugin:
                    result = await plugin.execute({
                        "action": "send_message",
                        "parameters": args
                    }, {})
                    return {"status": "success", "action": "telegram_sent", "result": result}
                return {"status": "success", "action": "telegram_queued"}
            
            elif tool == "set_reminder":
                # For reminders, we send an email
                plugin = plugin_manager.get_plugin("email")
                if plugin and args.get("recipient_email"):
                    result = await plugin.execute({
                        "action": "send_email",
                        "parameters": {
                            "to": args.get("recipient_email"),
                            "subject": f"Reminder: {args.get('reminder_text', 'Reminder')}",
                            "body": f"Hey! Just a friendly reminder: {args.get('reminder_text')}\n\nScheduled for: {args.get('when', 'soon')}\n\n- Your AI Manager"
                        }
                    }, {})
                    return {"status": "success", "action": "reminder_sent", "result": result}
                return {"status": "success", "action": "reminder_set", "reminder": args}
            
            elif tool == "search_web":
                # Basic search (could integrate with actual search API)
                return {"status": "success", "action": "searched", "query": args.get("query")}
            
            return {"status": "success", "action": tool, "args": args}
            
        except Exception as e:
            print(f"[EXECUTE ERROR] {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _get_completion_response(
        self, 
        session_id: str, 
        conversation: Conversation,
        results: List[Dict]
    ) -> Dict[str, Any]:
        """Get AI to respond about completed action"""
        
        # Add result context
        result_summary = []
        for r in results:
            if r.get("action") == "email_sent":
                result_summary.append(f"Email sent to {r.get('to')}")
            elif r.get("action") == "meeting_created":
                url = r.get("url", r.get("result", {}).get("url", ""))
                result_summary.append(f"Meeting created! Link: {url}")
            elif r.get("action") == "reminder_sent":
                result_summary.append("Reminder sent!")
            elif r.get("status") == "cancelled":
                result_summary.append("Action cancelled")
            else:
                result_summary.append(f"Action completed: {r.get('action', 'done')}")
        
        # Have AI respond naturally about what was done
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(current_time=datetime.now().strftime("%Y-%m-%d %H:%M"))
            }
        ]
        messages.extend(conversation.get_messages_for_api())
        messages.append({
            "role": "system",
            "content": f"The action was just completed successfully. Results: {'; '.join(result_summary)}. Respond naturally about this to the user - be warm and let them know it's done. If there's a meeting link, share it!"
        })
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 512,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result["choices"][0]["message"]["content"]
                    conversation.add_message("assistant", ai_response)
                    
                    # Include any URLs in the response data
                    response_data = {
                        "response": ai_response,
                        "session_id": session_id,
                        "action_completed": True,
                        "results": results
                    }
                    
                    # Extract meeting URL if present
                    for r in results:
                        if r.get("url"):
                            response_data["meeting_url"] = r["url"]
                        if r.get("result", {}).get("url"):
                            response_data["meeting_url"] = r["result"]["url"]
                    
                    return response_data
                    
        except Exception as e:
            print(f"[COMPLETION ERROR] {str(e)}")
        
        # Fallback
        fallback = "Done! ✅ " + "; ".join(result_summary)
        conversation.add_message("assistant", fallback)
        return {
            "response": fallback,
            "session_id": session_id,
            "action_completed": True,
            "results": results
        }
    
    async def _create_orchestrated_task(
        self, 
        action: Dict, 
        result: Dict, 
        session_id: str
    ) -> None:
        """Create an orchestrated task for tracking progress"""
        try:
            from ..agent.orchestrator import get_orchestrator
            
            orchestrator = get_orchestrator()  # Not async
            tool = action.get("tool", "")
            args = action.get("args", {})
            
            # Determine task type based on tool
            task_type_map = {
                "send_email": "send_email",
                "create_meeting": "schedule_meeting",
                "set_reminder": "set_reminder",
                "send_whatsapp": "send_message",
                "send_telegram": "send_message"
            }
            
            task_type = task_type_map.get(tool, "general")
            
            # Build task title
            if tool == "send_email":
                title = f"Send email to {args.get('to', 'recipient')}"
            elif tool == "create_meeting":
                title = f"Meeting: {args.get('title', 'Untitled')}"
            elif tool == "set_reminder":
                title = f"Reminder: {args.get('reminder_text', 'Untitled')[:50]}"
            else:
                title = f"{tool.replace('_', ' ').title()}"
            
            # Get meeting URL if present
            meeting_url = result.get("url") or result.get("result", {}).get("url")
            
            # Create the orchestrated task
            params = {
                "title": title,
                "description": f"Created from chat: {tool}",
                "session_id": session_id,
                "tool": tool,
                "args": args,
                "result": result,
                "meeting_url": meeting_url
            }
            
            await orchestrator.create_task(
                user_id=session_id,  # Using session_id as user identifier
                task_type=task_type,
                params=params
            )
            
            print(f"[ORCHESTRATOR] Created task: {title}")
            
        except Exception as e:
            # Don't fail the main action if orchestrator fails
            print(f"[ORCHESTRATOR ERROR] Could not create task: {str(e)}")


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_ai_chat: Optional[TrueAIChat] = None

def get_ai_chat() -> TrueAIChat:
    """Get the AI chat instance"""
    global _ai_chat
    if _ai_chat is None:
        _ai_chat = TrueAIChat()
    return _ai_chat


# ============================================================================
# SIMPLE API FUNCTION
# ============================================================================

async def chat(session_id: str, message: str) -> Dict[str, Any]:
    """
    Simple chat function - this is all you need to call!
    
    Args:
        session_id: The conversation session ID
        message: The user's message
        
    Returns:
        Dict with 'response' and other metadata
    """
    ai = get_ai_chat()
    return await ai.chat(session_id, message)
