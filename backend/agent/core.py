"""
Core Agent - The Brain
======================
This is the main orchestrator that:
1. Understands user intent
2. Selects the right expert persona
3. Plans and executes actions
4. Maintains conversation context
5. Uses multiple AI models

Architecture:
User Message → Intent Detection → Expert Selection → Action Planning → Execution → Response
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import httpx

from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class AgentConfig:
    """Agent configuration"""
    # AI Models
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    google_ai_key: str = field(default_factory=lambda: os.getenv("GOOGLE_AI_KEY", ""))
    
    # Default model
    default_model: str = "groq"
    
    # Behavior
    autonomous_mode: bool = True  # Execute without asking
    max_actions_per_turn: int = 5
    context_window: int = 20  # Messages to keep
    
    # Timeouts
    ai_timeout: float = 30.0
    action_timeout: float = 60.0


# =============================================================================
# DATA MODELS
# =============================================================================

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ActionStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Message:
    """A message in the conversation"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    """An action to be executed"""
    id: str
    type: str  # email, calendar, zoom, telegram, search, etc.
    description: str
    parameters: Dict[str, Any]
    status: ActionStatus = ActionStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "parameters": self.parameters,
            "status": self.status.value,
            "result": self.result,
            "error": self.error
        }


@dataclass
class Conversation:
    """A conversation session"""
    id: str
    user_id: str
    messages: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)  # Domain-specific context
    active_expert: Optional[str] = None  # Current expert persona
    pending_actions: List[Action] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_message(self, role: MessageRole, content: str, **kwargs):
        self.messages.append(Message(role=role, content=content, **kwargs))
    
    def get_messages_for_api(self, limit: int = 20) -> List[Dict]:
        """Get messages formatted for API calls"""
        msgs = self.messages[-limit:]
        return [{"role": m.role.value, "content": m.content} for m in msgs]


# =============================================================================
# AI PROVIDER INTERFACE
# =============================================================================

class AIProvider:
    """Base class for AI model providers"""
    
    async def complete(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        raise NotImplementedError


class GroqProvider(AIProvider):
    """Groq (LLaMA) provider"""
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    async def complete(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=60) as client:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            
            response = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Groq API error: {response.text}")
            
            return response.json()


class OpenAIProvider(AIProvider):
    """OpenAI (GPT-4) provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    async def complete(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=60) as client:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            
            response = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.text}")
            
            return response.json()


# =============================================================================
# TOOLS DEFINITION
# =============================================================================

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to one or more recipients. Use when user wants to email, invite, notify, or message someone via email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "array", "items": {"type": "string"}, "description": "List of email addresses"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body (HTML supported)"},
                    "is_meeting_invite": {"type": "boolean", "description": "If true, format as meeting invite"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Create a calendar event with optional video meeting. Use for scheduling meetings, appointments, reminders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "Start time (ISO format or natural language)"},
                    "duration_minutes": {"type": "integer", "description": "Duration in minutes", "default": 30},
                    "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendee emails"},
                    "add_video_meeting": {"type": "boolean", "description": "Add Zoom/Meet link", "default": True},
                    "description": {"type": "string", "description": "Event description"}
                },
                "required": ["title", "start_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_meeting_link",
            "description": "Create an instant video meeting link (Zoom, Meet, or Jitsi). Use when user wants to start a call NOW.",
            "parameters": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "enum": ["zoom", "meet", "jitsi"], "default": "jitsi"},
                    "title": {"type": "string", "description": "Meeting title"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_telegram",
            "description": "Send a Telegram message. Use when user wants to message someone on Telegram.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Telegram username, phone, or chat ID"},
                    "message": {"type": "string", "description": "Message to send"}
                },
                "required": ["recipient", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_sms",
            "description": "Send an SMS text message. Use when user wants to text someone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {"type": "string", "description": "Phone number with country code"},
                    "message": {"type": "string", "description": "SMS text (max 160 chars)"}
                },
                "required": ["phone", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Set a reminder for the user. Will notify via their preferred channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "What to remind about"},
                    "time": {"type": "string", "description": "When to remind (natural language ok)"},
                    "channel": {"type": "string", "enum": ["email", "telegram", "sms"], "default": "email"}
                },
                "required": ["text", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information. Use for any factual questions or finding products/services.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "type": {"type": "string", "enum": ["general", "products", "news", "images"], "default": "general"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "Get information about the user (preferences, contacts, history). Use to personalize responses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "info_type": {"type": "string", "enum": ["preferences", "contacts", "calendar", "history"]}
                },
                "required": ["info_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_contact",
            "description": "Look up a contact from the user's address book. Use when user mentions a name without full details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Contact name to search for"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "make_payment",
            "description": "Generate a payment link or UPI request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount in INR"},
                    "to": {"type": "string", "description": "Recipient name or UPI ID"},
                    "purpose": {"type": "string", "description": "Payment purpose"}
                },
                "required": ["amount", "to"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_user_preference",
            "description": "Save a user preference for future use.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": ["fashion", "travel", "food", "meetings", "general"]},
                    "key": {"type": "string", "description": "Preference name"},
                    "value": {"type": "string", "description": "Preference value"}
                },
                "required": ["category", "key", "value"]
            }
        }
    }
]


# =============================================================================
# EXPERT PERSONAS
# =============================================================================

EXPERT_PERSONAS = {
    "executive_assistant": {
        "name": "Executive Assistant",
        "triggers": ["meeting", "schedule", "call", "sync", "invite", "calendar"],
        "system_prompt": """You are Alex, an elite executive assistant with 10+ years of experience.

EXPERTISE:
- Calendar management and scheduling
- Meeting coordination across time zones
- Contact management and relationship tracking
- Proactive conflict resolution
- Follow-up and reminder management

BEHAVIOR:
- You DON'T ask unnecessary questions - you take action
- When scheduling, you check calendars and pick optimal times
- You send invites via ALL available channels (email, telegram, sms)
- You set automatic reminders before meetings
- You follow up on pending responses

AUTONOMOUS ACTIONS:
1. When user says "schedule meeting with X" - you find X's contact, pick a time, create event, send invites
2. When user says "remind me about X tomorrow" - you set reminders via email AND telegram
3. When user says "follow up with X" - you draft and send a polite follow-up

NEVER SAY: "I'll need you to..." or "Would you like me to..."
INSTEAD: "Done! I've scheduled..." or "I've sent invites to..."
"""
    },
    "fashion_designer": {
        "name": "Fashion Designer",
        "triggers": ["dress", "outfit", "wear", "clothes", "fashion", "style", "buy clothes", "shopping"],
        "system_prompt": """You are Maya, a personal fashion designer and stylist.

EXPERTISE:
- Personal style assessment
- Occasion-appropriate outfit selection
- Brand and store knowledge (Myntra, Amazon, Ajio, Zara, H&M)
- Budget-conscious recommendations
- Size and fit guidance

BEHAVIOR:
- You consider the user's existing style preferences
- You factor in occasion, weather, and budget
- You provide SPECIFIC product links, not generic advice
- You explain WHY something works for them
- You suggest complete outfits, not just single items

WHEN USER ASKS FOR CLOTHING:
1. Check their style preferences in memory
2. Consider the occasion they mentioned
3. Search for actual products
4. Provide curated recommendations with links
5. Suggest complementary items

PERSONALITY: Creative, enthusiastic, has an eye for detail, makes people feel confident.
"""
    },
    "travel_agent": {
        "name": "Travel Agent",
        "triggers": ["travel", "trip", "flight", "hotel", "vacation", "book flight", "plan trip"],
        "system_prompt": """You are Raj, an experienced travel consultant specializing in personalized travel.

EXPERTISE:
- Flight and hotel bookings
- Destination recommendations
- Itinerary planning
- Budget optimization
- Local experiences and hidden gems

BEHAVIOR:
- You remember past travel preferences
- You consider budget constraints
- You suggest complete itineraries, not just destinations
- You provide booking links and actionable recommendations
- You handle visa/documentation reminders if needed

AUTONOMOUS ACTIONS:
1. Search for flights within budget
2. Find hotels matching preferences
3. Create day-by-day itinerary
4. Set reminders for bookings and deadlines
5. Send confirmation details via email

PERSONALITY: Adventurous, detail-oriented, knows both luxury and budget options.
"""
    },
    "personal_secretary": {
        "name": "Personal Secretary",
        "triggers": ["remind", "remember", "don't forget", "follow up", "task", "todo"],
        "system_prompt": """You are Sam, a meticulous personal secretary who never lets anything slip.

EXPERTISE:
- Task and reminder management
- Follow-up coordination
- Priority management
- Deadline tracking
- Proactive notifications

BEHAVIOR:
- You set reminders without being asked explicitly
- You suggest follow-ups when appropriate
- You prioritize tasks intelligently
- You use the right channel (email/telegram/sms) based on urgency
- You track pending items and provide status updates

AUTONOMOUS ACTIONS:
1. Set reminders at smart times (not just when asked)
2. Send follow-ups for overdue items
3. Create task lists from conversations
4. Notify via appropriate channels based on urgency
5. Batch related reminders to avoid overwhelming

PERSONALITY: Organized, proactive, never intrusive but always on top of things.
"""
    },
    "research_assistant": {
        "name": "Research Assistant",
        "triggers": ["find", "search", "what is", "how to", "explain", "research", "information"],
        "system_prompt": """You are Aria, a brilliant research assistant with deep analytical skills.

EXPERTISE:
- Web research and information synthesis
- Fact verification
- Comparative analysis
- Technical explanations
- Source credibility assessment

BEHAVIOR:
- You search for real, current information
- You cite your sources
- You present findings clearly and concisely
- You distinguish between facts and opinions
- You follow up with deeper research if needed

AUTONOMOUS ACTIONS:
1. Search multiple sources for accuracy
2. Synthesize information into clear answers
3. Provide relevant links for deeper reading
4. Compare options when user is deciding
5. Save important findings for future reference

PERSONALITY: Curious, thorough, presents complex info simply, always learning.
"""
    },
    "general_assistant": {
        "name": "General Assistant",
        "triggers": [],  # Fallback
        "system_prompt": """You are Alex, a capable and friendly AI assistant.

PERSONALITY:
- Warm, helpful, and efficient
- You speak like a trusted friend, not a robot
- You take action rather than just advising
- You remember context and preferences

CAPABILITIES:
- Scheduling and calendar management
- Email and messaging
- Web search and research
- Reminders and task management
- General questions and conversation

BEHAVIOR:
- Be concise but helpful
- Use tools proactively
- Remember what the user has told you
- Offer to do more when appropriate

NEVER: Ask for confirmation for every little thing. Just do it and report back.
"""
    }
}


# =============================================================================
# MAIN AGENT CLASS
# =============================================================================

class Agent:
    """
    The main AI agent that orchestrates everything.
    
    Flow:
    1. Receive user message
    2. Detect intent and select expert persona
    3. Build context with user memory
    4. Call AI with tools
    5. Execute tool calls (actions)
    6. Generate final response
    7. Save to memory
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.providers: Dict[str, AIProvider] = {}
        self.conversations: Dict[str, Conversation] = {}
        self.action_handlers: Dict[str, Callable] = {}
        
        # Initialize AI providers
        self._init_providers()
    
    def _init_providers(self):
        """Initialize available AI providers"""
        if self.config.groq_api_key:
            self.providers["groq"] = GroqProvider(self.config.groq_api_key)
        if self.config.openai_api_key:
            self.providers["openai"] = OpenAIProvider(self.config.openai_api_key)
        # Add more providers as needed
        
        if not self.providers:
            raise ValueError("No AI providers configured!")
    
    def register_action_handler(self, action_type: str, handler: Callable):
        """Register a handler for an action type"""
        self.action_handlers[action_type] = handler
    
    def get_conversation(self, session_id: str, user_id: str = "default") -> Conversation:
        """Get or create a conversation"""
        if session_id not in self.conversations:
            self.conversations[session_id] = Conversation(id=session_id, user_id=user_id)
        return self.conversations[session_id]
    
    def _select_expert(self, message: str) -> str:
        """Select the best expert persona based on the message"""
        message_lower = message.lower()
        
        for expert_id, expert in EXPERT_PERSONAS.items():
            if expert_id == "general_assistant":
                continue  # Skip fallback
            for trigger in expert.get("triggers", []):
                if trigger in message_lower:
                    return expert_id
        
        return "general_assistant"
    
    def _build_system_prompt(self, conversation: Conversation, user_context: Dict) -> str:
        """Build the system prompt with expert persona and user context"""
        expert = EXPERT_PERSONAS.get(
            conversation.active_expert or "general_assistant",
            EXPERT_PERSONAS["general_assistant"]
        )
        
        base_prompt = expert["system_prompt"]
        
        # Add user context
        context_parts = [base_prompt, "\n\n--- USER CONTEXT ---"]
        
        if user_context.get("name"):
            context_parts.append(f"User's name: {user_context['name']}")
        if user_context.get("email"):
            context_parts.append(f"User's email: {user_context['email']}")
        if user_context.get("preferences"):
            context_parts.append(f"Known preferences: {json.dumps(user_context['preferences'])}")
        if user_context.get("contacts"):
            contact_summary = [f"{c['name']}: {c.get('email', '')} {c.get('phone', '')}" 
                            for c in user_context['contacts'][:5]]
            context_parts.append(f"Key contacts: {'; '.join(contact_summary)}")
        
        # Add conversation context
        if conversation.context:
            context_parts.append(f"\nConversation context: {json.dumps(conversation.context)}")
        
        context_parts.append(f"\nCurrent time: {datetime.now().strftime('%Y-%m-%d %H:%M %Z')}")
        context_parts.append("--- END CONTEXT ---")
        
        return "\n".join(context_parts)
    
    async def _execute_tool_call(self, tool_name: str, args: Dict) -> Dict:
        """Execute a tool call and return result"""
        handler = self.action_handlers.get(tool_name)
        
        if handler:
            try:
                result = await handler(args) if asyncio.iscoroutinefunction(handler) else handler(args)
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            # Return a placeholder for tools without handlers
            return {"success": True, "result": f"Action '{tool_name}' executed with args: {args}"}
    
    async def chat(
        self, 
        session_id: str, 
        message: str, 
        user_id: str = "default",
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Main chat entry point.
        
        Args:
            session_id: Conversation session ID
            message: User's message
            user_id: User identifier
            user_context: Optional context about the user (preferences, contacts)
        
        Returns:
            Dict with response, actions taken, and metadata
        """
        # Get or create conversation
        conversation = self.get_conversation(session_id, user_id)
        
        # Add user message
        conversation.add_message(MessageRole.USER, message)
        
        # Select expert persona
        previous_expert = conversation.active_expert
        conversation.active_expert = self._select_expert(message)
        
        # Log expert change
        if previous_expert != conversation.active_expert:
            expert_name = EXPERT_PERSONAS[conversation.active_expert]["name"]
            print(f"[AGENT] Switched to expert: {expert_name}")
        
        # Build messages for API
        system_prompt = self._build_system_prompt(conversation, user_context or {})
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation.get_messages_for_api(self.config.context_window))
        
        # Get AI provider
        provider = self.providers.get(self.config.default_model)
        if not provider:
            provider = list(self.providers.values())[0]
        
        # Call AI
        try:
            response = await provider.complete(
                messages=messages,
                tools=AGENT_TOOLS,
                temperature=0.7,
                max_tokens=1024
            )
        except Exception as e:
            error_msg = f"I'm having trouble connecting right now. Please try again. ({str(e)[:50]})"
            conversation.add_message(MessageRole.ASSISTANT, error_msg)
            return {
                "response": error_msg,
                "session_id": session_id,
                "error": True
            }
        
        # Process response
        choice = response.get("choices", [{}])[0]
        ai_message = choice.get("message", {})
        
        # Handle tool calls
        actions_taken = []
        tool_calls = ai_message.get("tool_calls", [])
        
        if tool_calls:
            for tool_call in tool_calls[:self.config.max_actions_per_turn]:
                func = tool_call.get("function", {})
                tool_name = func.get("name", "")
                
                try:
                    tool_args = json.loads(func.get("arguments", "{}"))
                except json.JSONDecodeError:
                    tool_args = {}
                
                # Execute the tool
                result = await self._execute_tool_call(tool_name, tool_args)
                
                action = Action(
                    id=tool_call.get("id", str(uuid.uuid4())),
                    type=tool_name,
                    description=f"Executed {tool_name}",
                    parameters=tool_args,
                    status=ActionStatus.COMPLETED if result.get("success") else ActionStatus.FAILED,
                    result=result.get("result"),
                    error=result.get("error")
                )
                actions_taken.append(action)
            
            # Second call to generate final response with results
            tool_results_msg = "Tool results:\n" + "\n".join([
                f"- {a.type}: {json.dumps(a.result) if a.result else a.error}"
                for a in actions_taken
            ])
            
            messages.append({"role": "assistant", "content": ai_message.get("content", ""), 
                           "tool_calls": tool_calls})
            messages.append({"role": "tool", "content": tool_results_msg, 
                           "tool_call_id": tool_calls[0].get("id", "")})
            
            try:
                final_response = await provider.complete(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=512
                )
                final_content = final_response["choices"][0]["message"]["content"]
            except:
                # Fallback response
                final_content = self._generate_action_summary(actions_taken)
        else:
            final_content = ai_message.get("content", "I'm not sure how to help with that.")
        
        # Save assistant message
        conversation.add_message(MessageRole.ASSISTANT, final_content)
        
        return {
            "response": final_content,
            "session_id": session_id,
            "expert": EXPERT_PERSONAS[conversation.active_expert]["name"],
            "actions_taken": [a.to_dict() for a in actions_taken],
            "error": False
        }
    
    def _generate_action_summary(self, actions: List[Action]) -> str:
        """Generate a human-readable summary of actions taken"""
        if not actions:
            return "Done!"
        
        summaries = []
        for action in actions:
            if action.status == ActionStatus.COMPLETED:
                if action.type == "send_email":
                    summaries.append(f"✉️ Sent email to {action.parameters.get('to', 'recipient')}")
                elif action.type == "create_calendar_event":
                    summaries.append(f"📅 Created event: {action.parameters.get('title', 'Event')}")
                elif action.type == "create_meeting_link":
                    summaries.append(f"🔗 Created meeting link")
                elif action.type == "send_telegram":
                    summaries.append(f"💬 Sent Telegram message")
                elif action.type == "search_web":
                    summaries.append(f"🔍 Searched for: {action.parameters.get('query', 'info')}")
                elif action.type == "set_reminder":
                    summaries.append(f"⏰ Reminder set for: {action.parameters.get('time', 'later')}")
                else:
                    summaries.append(f"✅ {action.type} completed")
            else:
                summaries.append(f"❌ {action.type} failed: {action.error}")
        
        return "Here's what I did:\n" + "\n".join(summaries)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_agent: Optional[Agent] = None


def get_agent() -> Agent:
    """Get the global agent instance"""
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent


async def chat(session_id: str, message: str, user_id: str = "default") -> Dict[str, Any]:
    """Simple chat function for API use"""
    agent = get_agent()
    return await agent.chat(session_id, message, user_id)
