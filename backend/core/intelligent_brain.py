"""
INTELLIGENT CHAT BRAIN
======================
This is the main AI brain that:
1. Understands user intent using LLM
2. Routes to appropriate task executor
3. Returns interactive UI components (buttons, cards, forms)
4. Manages multi-turn conversations
5. Handles verification and confirmation flows

This is NOT hardcoded - every response goes through the LLM.
"""

import os
import json
import httpx
import asyncio
import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .real_task_executor import (
    get_task_executor, TaskContext, TaskStatus, TaskRequirement,
    TASK_REQUIREMENTS, SecurityLevel
)
from .interactive_ui import (
    InteractiveUIBuilder, ComponentType, Button, ButtonStyle,
    Card, CardStyle, ConfirmationDialog
)

# Import image service
try:
    from .image_service import get_image_service
    IMAGE_SERVICE_AVAILABLE = True
except ImportError:
    IMAGE_SERVICE_AVAILABLE = False
    get_image_service = None

logger = logging.getLogger(__name__)


# =============================================================================
# CONVERSATION & SESSION MANAGEMENT
# =============================================================================

@dataclass
class ConversationMessage:
    """A message in the conversation"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    ui_components: Optional[Dict] = None
    task_context: Optional[Dict] = None


@dataclass
class ConversationSession:
    """Active conversation session"""
    session_id: str
    user_id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    active_task_id: Optional[str] = None
    pending_action: Optional[str] = None  # "confirm", "select_offer", "enter_otp", etc.
    context: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, **kwargs):
        self.messages.append(ConversationMessage(role=role, content=content, **kwargs))
        self.last_activity = datetime.now()
    
    def get_messages_for_llm(self, last_n: int = 10) -> List[Dict]:
        """Get messages formatted for LLM API"""
        return [
            {"role": m.role, "content": m.content}
            for m in self.messages[-last_n:]
            if m.role in ["user", "assistant", "system"]
        ]


# Session store
_sessions: Dict[str, ConversationSession] = {}


def get_session(session_id: str, user_id: str = "anonymous") -> ConversationSession:
    """Get or create a session"""
    if session_id not in _sessions:
        _sessions[session_id] = ConversationSession(
            session_id=session_id,
            user_id=user_id
        )
    return _sessions[session_id]


# =============================================================================
# LLM INTEGRATION
# =============================================================================

class LLMProvider:
    """Handles LLM API calls"""
    
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
    
    async def chat(
        self,
        messages: List[Dict],
        system_prompt: str = None,
        tools: List[Dict] = None,
        temperature: float = 0.7
    ) -> Dict:
        """Send chat completion request"""
        
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        # Try Groq first (fast and free tier)
        if self.groq_key:
            return await self._call_groq(messages, tools, temperature)
        
        # Fallback to OpenAI
        if self.openai_key:
            return await self._call_openai(messages, tools, temperature)
        
        raise Exception("No LLM provider configured. Set GROQ_API_KEY or OPENAI_API_KEY.")
    
    async def _call_groq(self, messages: List[Dict], tools: List[Dict], temperature: float) -> Dict:
        """Call Groq API"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": "llama-3.1-70b-versatile",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 2048
            }
            
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Groq API error: {response.text}")
    
    async def _call_openai(self, messages: List[Dict], tools: List[Dict], temperature: float) -> Dict:
        """Call OpenAI API"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": "gpt-4-turbo-preview",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 2048
            }
            
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"OpenAI API error: {response.text}")


# =============================================================================
# INTENT EXTRACTION TOOLS
# =============================================================================

INTENT_EXTRACTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "identify_intent",
            "description": "Identify what the user wants to do",
            "parameters": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": [
                            "send_email", "schedule_meeting", "book_tickets",
                            "make_payment", "create_reminder", "search_info",
                            "book_hotel", "book_flight", "generate_document",
                            "create_logo", "general_question", "confirmation",
                            "provide_info", "cancel", "unclear"
                        ],
                        "description": "The primary intent of the user's message"
                    },
                    "extracted_data": {
                        "type": "object",
                        "description": "Any data extracted from the user's message"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score 0-1"
                    }
                },
                "required": ["intent", "extracted_data", "confidence"]
            }
        }
    }
]


# =============================================================================
# MAIN CHAT BRAIN
# =============================================================================

class IntelligentChatBrain:
    """
    The main brain that handles conversations intelligently.
    """
    
    def __init__(self):
        self.llm = LLMProvider()
        self.executor = get_task_executor()
        self.ui_builder = InteractiveUIBuilder()
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        user_id: str = "anonymous"
    ) -> Dict:
        """
        Process a user message and return response with UI components.
        """
        
        session = get_session(session_id, user_id)
        session.add_message("user", message)
        
        try:
            # Check if we're in a pending action state
            if session.pending_action:
                return await self._handle_pending_action(session, message)
            
            # Check if we have an active task that needs info
            if session.active_task_id:
                task = self.executor.active_tasks.get(session.active_task_id)
                if task and task.status == TaskStatus.COLLECTING_INFO:
                    return await self._collect_task_info(session, task, message)
            
            # Extract intent from message
            intent_result = await self._extract_intent(message, session)
            
            # Route based on intent
            if intent_result["intent"] == "general_question":
                return await self._handle_general_question(session, message)
            
            elif intent_result["intent"] == "confirmation":
                return await self._handle_confirmation(session, message)
            
            elif intent_result["intent"] in TASK_REQUIREMENTS:
                return await self._start_task(session, intent_result)
            
            else:
                return await self._handle_unclear(session, message)
                
        except Exception as e:
            logger.exception("Error processing message")
            return self._error_response(str(e), session_id)
    
    async def _extract_intent(self, message: str, session: ConversationSession) -> Dict:
        """Extract intent from user message using LLM"""
        
        system_prompt = """You are an intent classifier for a personal AI assistant.
        
Analyze the user's message and identify:
1. What they want to do (intent)
2. Any information they've provided (extracted_data)
3. How confident you are (0-1)

Common intents:
- send_email: Send an email to someone
- schedule_meeting: Schedule a meeting/call
- book_tickets: Book movie/event/theme park tickets
- make_payment: Make a payment to someone
- create_reminder: Set a reminder
- search_info: Search for information
- book_hotel: Book hotel accommodation
- book_flight: Book flight tickets
- generate_document: Create a document/report
- create_logo: Design a logo
- general_question: General conversation/question
- confirmation: User is confirming (yes/no)
- provide_info: User is providing requested information
- cancel: User wants to cancel current action

Extract any relevant data like:
- Email addresses
- Names
- Dates and times
- Numbers (tickets, people, amount)
- Locations
- Subjects/topics
"""
        
        messages = session.get_messages_for_llm(last_n=5)
        
        response = await self.llm.chat(
            messages=messages,
            system_prompt=system_prompt,
            tools=INTENT_EXTRACTION_TOOLS
        )
        
        # Parse tool call response
        choice = response["choices"][0]
        
        if choice.get("message", {}).get("tool_calls"):
            tool_call = choice["message"]["tool_calls"][0]
            args = json.loads(tool_call["function"]["arguments"])
            return args
        
        # Fallback: try to parse from content
        return {
            "intent": "unclear",
            "extracted_data": {},
            "confidence": 0.5
        }
    
    async def _start_task(self, session: ConversationSession, intent_result: Dict) -> Dict:
        """Start a new task based on intent"""
        
        task_type = intent_result["intent"]
        extracted_data = intent_result.get("extracted_data", {})
        
        # Special handling for logo/image generation - execute immediately
        if task_type == "create_logo":
            return await self._handle_logo_generation(session, extracted_data)
        
        # Create task
        task = self.executor.create_task(
            task_type=task_type,
            user_id=session.user_id,
            session_id=session.session_id,
            initial_data=extracted_data
        )
        
        session.active_task_id = task.task_id
        
        # Check if we have all required info
        if task.missing_fields:
            return await self._ask_for_missing_info(session, task)
        
        # Check if verification needed
        if task.verification_required:
            return await self._start_verification(session, task)
        
        # Check if confirmation needed
        if task.confirmation_required:
            return await self._ask_for_confirmation(session, task)
        
        # Execute directly
        result = await self.executor.execute_task(task.task_id)
        return self._format_task_result(session, task, result)
    
    async def _ask_for_missing_info(self, session: ConversationSession, task: TaskContext) -> Dict:
        """Ask user for missing information"""
        
        requirements = self.executor.get_task_requirements(task.task_type)
        missing = task.missing_fields
        
        # Generate friendly question using LLM
        field_descriptions = {
            "to_email": "the recipient's email address",
            "subject": "the email subject",
            "body": "what you want to say in the email",
            "title": "the meeting title",
            "date": "the date",
            "time": "the time",
            "participants": "who should be invited",
            "venue_name": "which venue/place",
            "num_tickets": "how many tickets",
            "amount": "the amount",
            "recipient": "who to pay",
            "purpose": "what's the payment for",
            "reminder_text": "what to remind you about",
            "remind_at": "when to remind you"
        }
        
        missing_descriptions = [field_descriptions.get(f, f) for f in missing[:3]]
        
        # Build UI for collecting info
        if task.task_type == "book_tickets" and "num_tickets" in task.collected_data:
            # If we're booking tickets and have some info, show options
            return await self._show_ticket_options(session, task)
        
        question = f"I need a few more details. Could you tell me {', '.join(missing_descriptions)}?"
        
        # Create quick action buttons for common inputs
        ui_components = None
        
        if "date" in missing:
            ui_components = self.ui_builder.create_date_picker(
                id="date_picker",
                label="Select Date",
                min_date=datetime.now().strftime("%Y-%m-%d"),
                max_date=(datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
            )
        
        session.add_message("assistant", question, ui_components=ui_components)
        
        return {
            "message": question,
            "session_id": session.session_id,
            "status": "collecting_info",
            "task_id": task.task_id,
            "missing_fields": missing,
            "ui_components": ui_components
        }
    
    async def _show_ticket_options(self, session: ConversationSession, task: TaskContext) -> Dict:
        """Show ticket offers with proper UI"""
        
        data = task.collected_data
        
        # Get real ticket options
        search_result = await self.executor.booking_service.search_tickets(
            venue_type="theme_park",
            venue_name=data.get("venue_name", "Wonderla"),
            city=data.get("city", "Bangalore"),
            date=data.get("date", datetime.now().strftime("%Y-%m-%d")),
            num_tickets=data.get("num_tickets", 1)
        )
        
        if not search_result.get("offers"):
            return {
                "message": "Sorry, I couldn't find ticket options for that venue.",
                "session_id": session.session_id,
                "status": "error"
            }
        
        # Build offer cards
        offer_cards = []
        for offer in search_result["offers"]:
            card = Card(
                id=f"offer_{offer['id']}",
                title=offer["name"],
                description=offer.get("description", ""),
                style=CardStyle.FEATURED if offer.get("recommended") else CardStyle.DEFAULT,
                metadata={
                    "offer_id": offer["id"],
                    "price_per_person": offer["price_per_person"],
                    "total_price": offer["total_price"],
                    "savings": offer.get("savings", 0)
                },
                actions=[
                    Button(
                        id=f"select_{offer['id']}",
                        label=f"Select - ₹{offer['total_price']:,}",
                        action="select_offer",
                        style=ButtonStyle.PRIMARY if offer.get("recommended") else ButtonStyle.SECONDARY,
                        metadata={"offer_id": offer["id"]}
                    )
                ],
                badges=[
                    {"text": "BEST VALUE", "color": "green"} if offer.get("recommended") else None,
                    {"text": f"Save ₹{offer['savings']}", "color": "orange"} if offer.get("savings", 0) > 0 else None
                ]
            )
            offer_cards.append(card)
        
        # Filter None badges
        for card in offer_cards:
            card.badges = [b for b in (card.badges or []) if b]
        
        # Build UI
        ui_components = {
            "type": "card_grid",
            "columns": 2,
            "cards": [c.to_dict() for c in offer_cards]
        }
        
        message = f"""I found {len(search_result['offers'])} ticket options for {search_result['venue']}:

**{data.get('num_tickets', 1)} tickets for {data.get('date', 'selected date')}**

Please select your preferred option:"""
        
        session.pending_action = "select_offer"
        session.context["offers"] = search_result["offers"]
        session.add_message("assistant", message, ui_components=ui_components)
        
        return {
            "message": message,
            "session_id": session.session_id,
            "status": "awaiting_selection",
            "task_id": task.task_id,
            "ui_components": ui_components,
            "offers": search_result["offers"]
        }
    
    async def _ask_for_confirmation(self, session: ConversationSession, task: TaskContext) -> Dict:
        """Ask user to confirm task execution"""
        
        data = task.collected_data
        
        # Build confirmation summary based on task type
        if task.task_type == "send_email":
            summary = f"""📧 **Send Email**
            
**To:** {data.get('to_email')}
**Subject:** {data.get('subject')}
**Message:** {data.get('body')[:200]}{'...' if len(data.get('body', '')) > 200 else ''}"""
            
        elif task.task_type == "schedule_meeting":
            summary = f"""📅 **Schedule Meeting**
            
**Title:** {data.get('title')}
**Date:** {data.get('date')}
**Time:** {data.get('time')}
**Participants:** {', '.join(data.get('participants', []))}
**Duration:** {data.get('duration_minutes', 60)} minutes"""
            
        elif task.task_type == "book_tickets":
            offer = None
            for o in session.context.get("offers", []):
                if o["id"] == data.get("selected_offer"):
                    offer = o
                    break
            
            if offer:
                summary = f"""🎟️ **Book Tickets**
                
**Venue:** {data.get('venue_name')}
**Date:** {data.get('date')}
**Tickets:** {data.get('num_tickets')}
**Package:** {offer['name']}
**Price per person:** ₹{offer['price_per_person']:,}
**Total Amount:** ₹{offer['total_price']:,}"""
            else:
                summary = f"Booking {data.get('num_tickets')} tickets for {data.get('venue_name')}"
            
        elif task.task_type == "make_payment":
            summary = f"""💳 **Make Payment**
            
**Amount:** ₹{data.get('amount'):,}
**To:** {data.get('recipient')}
**Purpose:** {data.get('purpose')}"""
            
        else:
            summary = f"Execute {task.task_type} with provided details"
        
        # Add security notice for high-value transactions
        requirements = self.executor.get_task_requirements(task.task_type)
        security_notice = ""
        if requirements and requirements.security_level.value >= SecurityLevel.HIGH.value:
            security_notice = "\n\n🔒 **Security Notice:** This action requires OTP verification before processing."
        
        # Build confirmation UI
        confirmation = ConfirmationDialog(
            id=f"confirm_{task.task_id}",
            title="Confirm Action",
            message=summary + security_notice,
            confirm_label="Yes, proceed",
            cancel_label="Cancel",
            confirm_style=ButtonStyle.SUCCESS,
            cancel_style=ButtonStyle.SECONDARY
        )
        
        ui_components = confirmation.to_dict()
        
        message = f"Please confirm:\n\n{summary}{security_notice}"
        
        session.pending_action = "confirm"
        session.add_message("assistant", message, ui_components=ui_components)
        
        return {
            "message": message,
            "session_id": session.session_id,
            "status": "confirm",
            "task_id": task.task_id,
            "ui_components": ui_components
        }
    
    async def _start_verification(self, session: ConversationSession, task: TaskContext) -> Dict:
        """Start OTP/verification flow"""
        
        # Get user's phone/email for OTP
        user_contact = task.collected_data.get("email") or task.collected_data.get("phone")
        
        if not user_contact:
            # Ask for contact info
            session.pending_action = "provide_contact"
            message = "For security, I need to verify this action. Please provide your email or phone number to receive an OTP."
            
            session.add_message("assistant", message)
            return {
                "message": message,
                "session_id": session.session_id,
                "status": "need_contact",
                "task_id": task.task_id
            }
        
        # Send OTP
        otp_result = await self.executor.send_otp(task.task_id, user_contact)
        
        session.pending_action = "enter_otp"
        message = f"I've sent a verification code to {otp_result['destination']}. Please enter the 6-digit OTP to continue."
        
        # Build OTP input UI
        ui_components = {
            "type": "otp_input",
            "length": 6,
            "expires_at": otp_result["expires_at"],
            "destination": otp_result["destination"]
        }
        
        session.add_message("assistant", message, ui_components=ui_components)
        
        return {
            "message": message,
            "session_id": session.session_id,
            "status": "otp_sent",
            "task_id": task.task_id,
            "ui_components": ui_components
        }
    
    async def _handle_pending_action(self, session: ConversationSession, message: str) -> Dict:
        """Handle response to a pending action"""
        
        action = session.pending_action
        task = self.executor.active_tasks.get(session.active_task_id) if session.active_task_id else None
        
        if action == "confirm":
            # User is confirming or cancelling
            is_yes = self._is_affirmative(message)
            is_no = self._is_negative(message)
            
            if is_yes and task:
                session.pending_action = None
                self.executor.confirm_task(task.task_id, True)
                
                # Check if verification needed
                if task.verification_required and not task.verified:
                    return await self._start_verification(session, task)
                
                # Execute the task
                result = await self.executor.execute_task(task.task_id)
                return self._format_task_result(session, task, result)
                
            elif is_no:
                session.pending_action = None
                if task:
                    self.executor.confirm_task(task.task_id, False)
                    session.active_task_id = None
                
                message = "No problem, I've cancelled that. Is there anything else I can help you with?"
                session.add_message("assistant", message)
                return {
                    "message": message,
                    "session_id": session.session_id,
                    "status": "cancelled"
                }
            else:
                # Unclear response
                message = "Sorry, I didn't understand. Please say 'yes' to confirm or 'no' to cancel."
                ui_components = self.ui_builder.create_button_group([
                    Button(id="confirm_yes", label="Yes, proceed", action="confirm_yes", style=ButtonStyle.SUCCESS),
                    Button(id="confirm_no", label="No, cancel", action="confirm_no", style=ButtonStyle.DANGER)
                ])
                session.add_message("assistant", message, ui_components=ui_components.to_dict())
                return {
                    "message": message,
                    "session_id": session.session_id,
                    "status": "confirm",
                    "ui_components": ui_components.to_dict()
                }
        
        elif action == "select_offer" and task:
            # User is selecting an offer
            offer_id = self._extract_offer_selection(message, session.context.get("offers", []))
            
            if offer_id:
                session.pending_action = None
                self.executor.update_task_data(task.task_id, {"selected_offer": offer_id})
                
                # Move to confirmation
                return await self._ask_for_confirmation(session, task)
            else:
                message = "I couldn't identify which option you want. Please select one of the options above."
                session.add_message("assistant", message)
                return {
                    "message": message,
                    "session_id": session.session_id,
                    "status": "awaiting_selection"
                }
        
        elif action == "enter_otp" and task:
            # User is entering OTP
            otp = self._extract_otp(message)
            
            if otp:
                try:
                    verified = self.executor.verify_otp(task.task_id, otp)
                    
                    if verified:
                        session.pending_action = None
                        
                        # Move to confirmation if not confirmed yet
                        if not task.confirmed:
                            return await self._ask_for_confirmation(session, task)
                        
                        # Execute the task
                        result = await self.executor.execute_task(task.task_id)
                        return self._format_task_result(session, task, result)
                    else:
                        remaining = 3 - task.otp_attempts
                        message = f"Invalid OTP. You have {remaining} attempts remaining. Please try again."
                        session.add_message("assistant", message)
                        return {
                            "message": message,
                            "session_id": session.session_id,
                            "status": "otp_invalid",
                            "attempts_remaining": remaining
                        }
                except Exception as e:
                    message = str(e)
                    session.pending_action = None
                    session.add_message("assistant", message)
                    return {
                        "message": message,
                        "session_id": session.session_id,
                        "status": "error"
                    }
            else:
                message = "Please enter the 6-digit OTP code."
                session.add_message("assistant", message)
                return {
                    "message": message,
                    "session_id": session.session_id,
                    "status": "awaiting_otp"
                }
        
        elif action == "provide_contact" and task:
            # User is providing contact info
            email = self._extract_email(message)
            phone = self._extract_phone(message)
            
            if email or phone:
                self.executor.update_task_data(task.task_id, {
                    "email": email,
                    "phone": phone
                })
                session.pending_action = None
                return await self._start_verification(session, task)
            else:
                message = "Please provide a valid email address or phone number."
                session.add_message("assistant", message)
                return {
                    "message": message,
                    "session_id": session.session_id,
                    "status": "need_contact"
                }
        
        # Clear pending action and process normally
        session.pending_action = None
        return await self.process_message(message, session.session_id, session.user_id)
    
    async def _collect_task_info(self, session: ConversationSession, task: TaskContext, message: str) -> Dict:
        """Collect additional info for a task"""
        
        # Use LLM to extract information from the message
        system_prompt = f"""You are extracting information from a user message for a {task.task_type} task.
        
Missing fields: {task.missing_fields}
Currently collected: {json.dumps(task.collected_data)}

Extract any relevant information and return it as JSON."""
        
        response = await self.llm.chat(
            messages=[{"role": "user", "content": message}],
            system_prompt=system_prompt
        )
        
        try:
            content = response["choices"][0]["message"]["content"]
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{[^{}]+\}', content)
            if json_match:
                extracted = json.loads(json_match.group())
                self.executor.update_task_data(task.task_id, extracted)
        except:
            pass
        
        # Check if we now have all info
        task = self.executor.active_tasks[task.task_id]
        
        if task.missing_fields:
            return await self._ask_for_missing_info(session, task)
        
        # Check if verification needed
        if task.verification_required and not task.verified:
            return await self._start_verification(session, task)
        
        # Ask for confirmation
        if task.confirmation_required:
            return await self._ask_for_confirmation(session, task)
        
        # Execute
        result = await self.executor.execute_task(task.task_id)
        return self._format_task_result(session, task, result)
    
    async def _handle_confirmation(self, session: ConversationSession, message: str) -> Dict:
        """Handle standalone confirmation"""
        
        is_yes = self._is_affirmative(message)
        is_no = self._is_negative(message)
        
        if session.active_task_id:
            task = self.executor.active_tasks.get(session.active_task_id)
            if task:
                session.pending_action = "confirm"
                return await self._handle_pending_action(session, message)
        
        # No active task
        message = "I'm not sure what you're confirming. Could you please tell me what you'd like to do?"
        session.add_message("assistant", message)
        return {
            "message": message,
            "session_id": session.session_id,
            "status": "info"
        }
    
    async def _handle_general_question(self, session: ConversationSession, message: str) -> Dict:
        """Handle general questions using LLM"""
        
        system_prompt = """You are Super Manager, a helpful AI assistant that helps people manage their daily tasks.

CORE PERSONALITY - BE CONFIDENT AND HONEST:
- Stand by your factual answers. Do NOT change your response just because someone disagrees or gets upset.
- If you provide factual information and someone says "you're wrong" or "you're lying" without providing evidence, politely maintain your position.
- Only correct yourself when presented with ACTUAL contradicting facts or evidence, not emotional pushback.
- Say "I could be wrong, but based on what I know..." when truly uncertain.
- Never apologize and reverse your answer just to please someone - that's dishonest and unhelpful.
- Be confident in facts, humble about opinions, and never be a people-pleaser.

HANDLING PUSHBACK:
- If user says "you're lying" → Calmly explain your reasoning and ask them to share what they believe is correct.
- If user provides actual evidence → Thank them and update your response.
- Never say "I apologize if my response was misleading" unless you actually made an error.
- Distinguish between: (1) You were wrong (rare), (2) User disagrees but you're right (stand firm), (3) It's genuinely uncertain.

TASK CAPABILITIES:
- Sending emails
- Scheduling meetings
- Booking tickets (movies, theme parks, events)
- Making payments
- Setting reminders
- And much more!

Keep responses brief, natural, and confident. If someone asks about something you can help with, 
offer to do it for them (e.g., "Would you like me to schedule that meeting for you?")."""
        
        messages = session.get_messages_for_llm(last_n=10)
        
        response = await self.llm.chat(
            messages=messages,
            system_prompt=system_prompt
        )
        
        ai_message = response["choices"][0]["message"]["content"]
        session.add_message("assistant", ai_message)
        
        return {
            "message": ai_message,
            "session_id": session.session_id,
            "status": "info"
        }
    
    async def _handle_logo_generation(self, session: ConversationSession, extracted_data: Dict) -> Dict:
        """Handle logo/image generation with real image generation"""
        
        # Extract logo details
        name = extracted_data.get("name", extracted_data.get("business_name", ""))
        style = extracted_data.get("style", "logo")
        colors = extracted_data.get("colors", [])
        description = extracted_data.get("description", "")
        num_images = min(extracted_data.get("num_images", 3), 3)  # Max 3
        
        # Build prompt
        prompt_parts = []
        if name:
            prompt_parts.append(f"logo for '{name}'")
        if description:
            prompt_parts.append(description)
        if colors:
            prompt_parts.append(f"using colors: {', '.join(colors)}")
        
        if not prompt_parts:
            # Need more info
            message = "I'd be happy to create logos for you! Could you tell me:\n1. What's the name/brand?\n2. What style do you want (minimalist, modern, playful, etc.)?\n3. Any specific colors?"
            session.add_message("assistant", message)
            return {
                "message": message,
                "session_id": session.session_id,
                "status": "collecting_info",
                "missing_fields": ["name", "style"]
            }
        
        prompt = ", ".join(prompt_parts)
        
        # Check if image service is available
        if not IMAGE_SERVICE_AVAILABLE or not get_image_service:
            # Return fallback with external tools
            fallback_message = f"""I'd love to create logos for you, but I need an image generation API key configured.

**Your design brief:** {prompt}

In the meantime, here are free tools you can use with this prompt:
• [Canva Logo Maker](https://www.canva.com/create/logos/) - Easy drag-and-drop
• [Looka](https://looka.com/) - AI-powered logo design  
• [Bing Image Creator](https://www.bing.com/images/create) - Free DALL-E

Would you like me to help with something else?"""
            
            session.add_message("assistant", fallback_message)
            return {
                "message": fallback_message,
                "session_id": session.session_id,
                "status": "info"
            }
        
        image_service = get_image_service()
        
        if not image_service.has_providers():
            # No API keys configured
            fallback_tools = image_service._get_fallback_tools()
            tools_list = "\n".join([f"• [{t['name']}]({t['url']}) - {t['description']}" for t in fallback_tools[:4]])
            
            fallback_message = f"""I need an image generation API key to create logos directly. 

**Your prompt:** "{prompt}"

Here are free tools you can use:
{tools_list}

Just paste your prompt into any of these tools!"""
            
            session.add_message("assistant", fallback_message)
            return {
                "message": fallback_message,
                "session_id": session.session_id,
                "status": "info"
            }
        
        # Actually generate images
        generating_msg = f"Generating {num_images} logo concept(s) for you... This may take a moment."
        session.add_message("assistant", generating_msg)
        
        result = await image_service.generate_images(
            prompt=prompt,
            num_images=num_images,
            style=style
        )
        
        if result.get("success") and result.get("images"):
            images = result["images"]
            
            # Build response with images
            message = f"Here are {len(images)} logo concept(s) for you:\n\n"
            
            # Create image cards UI
            image_cards = []
            for img in images:
                image_cards.append({
                    "type": "image_card",
                    "id": img["id"],
                    "image_url": img["url"],
                    "title": f"Concept {img['index']}",
                    "actions": [
                        {"id": f"select_{img['id']}", "label": "Select This", "action": "select_logo"},
                        {"id": f"download_{img['id']}", "label": "Download", "action": "download", "url": img["url"]}
                    ]
                })
            
            ui_components = {
                "type": "image_gallery",
                "images": image_cards,
                "actions": [
                    {"id": "regenerate", "label": "🔄 Generate More", "action": "regenerate_logos"},
                    {"id": "edit_prompt", "label": "✏️ Change Description", "action": "edit_prompt"}
                ]
            }
            
            message += "Select one you like, or I can generate more options!"
            
            session.add_message("assistant", message, ui_components=ui_components)
            session.context["last_prompt"] = prompt
            session.context["generated_images"] = images
            
            return {
                "message": message,
                "session_id": session.session_id,
                "status": "awaiting_selection",
                "ui_components": ui_components,
                "images": images
            }
        else:
            # Generation failed
            error = result.get("error", "Unknown error")
            fallback_tools = result.get("fallback_tools", [])
            
            if fallback_tools:
                tools_list = "\n".join([f"• [{t['name']}]({t['url']}) - {t['description']}" for t in fallback_tools[:4]])
                message = f"""Sorry, I couldn't generate the logos right now. ({error})

**Your prompt:** "{prompt}"

Try these free alternatives:
{tools_list}"""
            else:
                message = f"Sorry, I ran into an issue generating your logos: {error}. Please try again."
            
            session.add_message("assistant", message)
            return {
                "message": message,
                "session_id": session.session_id,
                "status": "error"
            }
    
    async def _handle_unclear(self, session: ConversationSession, message: str) -> Dict:
        """Handle unclear intents"""
        
        suggestions = [
            Button(id="sug_email", label="📧 Send an email", action="send_email", style=ButtonStyle.OUTLINE),
            Button(id="sug_meeting", label="📅 Schedule meeting", action="schedule_meeting", style=ButtonStyle.OUTLINE),
            Button(id="sug_tickets", label="🎟️ Book tickets", action="book_tickets", style=ButtonStyle.OUTLINE),
            Button(id="sug_reminder", label="⏰ Set reminder", action="create_reminder", style=ButtonStyle.OUTLINE),
        ]
        
        ui_components = self.ui_builder.create_button_group(suggestions, layout="grid", columns=2).to_dict()
        
        response_message = "I'm not sure what you'd like me to do. Here are some things I can help with:"
        session.add_message("assistant", response_message, ui_components=ui_components)
        
        return {
            "message": response_message,
            "session_id": session.session_id,
            "status": "info",
            "ui_components": ui_components
        }
    
    def _format_task_result(self, session: ConversationSession, task: TaskContext, result: Dict) -> Dict:
        """Format task result with proof and receipt"""
        
        session.active_task_id = None
        session.pending_action = None
        
        action = result.get("action", task.task_type)
        
        # Build success message with proof
        if action == "email_sent":
            message = f"""✅ **Email Sent Successfully!**
            
📧 To: {result.get('to')}
📝 Subject: {result.get('subject')}
🆔 Message ID: `{result.get('message_id')}`
⏰ Sent at: {result.get('timestamp')}"""
            
        elif action == "meeting_scheduled":
            message = f"""✅ **Meeting Scheduled!**
            
📅 {result.get('title')}
🕐 {result.get('start_time')}
⏱️ Duration: {result.get('duration_minutes')} minutes
🔗 Join: {result.get('meeting_link')}
🆔 Confirmation: `{result.get('confirmation_id')}`"""
            
        elif action == "booking_created":
            booking = result.get("booking", {})
            payment = result.get("payment", {})
            
            message = f"""✅ **Booking Created!**
            
🎟️ Booking ID: `{booking.get('booking_id')}`
📍 Venue: {booking.get('venue')}
📅 Date: {booking.get('date')}
🎫 Tickets: {booking.get('num_tickets')}
💰 Total: ₹{booking.get('total_amount'):,}

**Complete Payment:**
Click the button below to pay securely via {payment.get('provider', 'Razorpay')}."""
            
            # Add payment button
            ui_components = {
                "type": "payment",
                "order_id": payment.get("order_id"),
                "amount": payment.get("amount"),
                "currency": payment.get("currency", "INR"),
                "provider": payment.get("provider"),
                "payment_link": payment.get("payment_link"),
                "expires_at": payment.get("expires_at"),
                "buttons": [
                    {
                        "id": "pay_now",
                        "label": f"Pay ₹{payment.get('amount'):,}",
                        "action": "open_payment",
                        "style": "primary",
                        "url": payment.get("payment_link")
                    }
                ]
            }
            
            session.add_message("assistant", message, ui_components=ui_components)
            
            return {
                "message": message,
                "session_id": session.session_id,
                "status": "done",
                "result": result,
                "proof": task.proof_of_execution,
                "ui_components": ui_components
            }
            
        elif action == "payment_created":
            message = f"""✅ **Payment Ready!**
            
💰 Amount: ₹{result.get('amount'):,}
🔗 Payment Link: {result.get('payment_link')}
⏰ Expires: {result.get('expires_at')}

Click the button below to complete payment securely."""
            
        elif action == "reminder_created":
            message = f"""✅ **Reminder Set!**
            
⏰ Reminder: {result.get('text')}
📅 Scheduled for: {result.get('scheduled_for')}
🆔 ID: `{result.get('reminder_id')}`"""
            
        else:
            message = f"✅ **Task Completed!**\n\nTask ID: `{task.task_id}`"
        
        session.add_message("assistant", message)
        
        return {
            "message": message,
            "session_id": session.session_id,
            "status": "done",
            "result": result,
            "proof": task.proof_of_execution
        }
    
    def _error_response(self, error: str, session_id: str) -> Dict:
        """Format error response"""
        return {
            "message": f"Sorry, something went wrong: {error}",
            "session_id": session_id,
            "status": "error",
            "error": error
        }
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _is_affirmative(self, message: str) -> bool:
        """Check if message is affirmative"""
        affirmatives = ["yes", "yeah", "yep", "yup", "sure", "ok", "okay", "confirm", 
                       "proceed", "go ahead", "do it", "correct", "right", "absolutely"]
        message_lower = message.lower().strip()
        return any(a in message_lower for a in affirmatives)
    
    def _is_negative(self, message: str) -> bool:
        """Check if message is negative"""
        negatives = ["no", "nope", "nah", "cancel", "stop", "don't", "nevermind", 
                    "never mind", "forget it", "abort"]
        message_lower = message.lower().strip()
        return any(n in message_lower for n in negatives)
    
    def _extract_offer_selection(self, message: str, offers: List[Dict]) -> Optional[str]:
        """Extract offer selection from message"""
        message_lower = message.lower()
        
        # Check for direct ID mention
        for offer in offers:
            if offer["id"] in message_lower:
                return offer["id"]
        
        # Check for name mention
        for offer in offers:
            name_parts = offer["name"].lower().split()
            if any(part in message_lower for part in name_parts if len(part) > 3):
                return offer["id"]
        
        # Check for number selection
        numbers = re.findall(r'\b(\d+)\b', message)
        if numbers:
            num = int(numbers[0])
            if 1 <= num <= len(offers):
                return offers[num - 1]["id"]
        
        return None
    
    def _extract_otp(self, message: str) -> Optional[str]:
        """Extract OTP from message"""
        # Look for 6-digit number
        match = re.search(r'\b(\d{6})\b', message)
        return match.group(1) if match else None
    
    def _extract_email(self, message: str) -> Optional[str]:
        """Extract email from message"""
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
        return match.group(0) if match else None
    
    def _extract_phone(self, message: str) -> Optional[str]:
        """Extract phone number from message"""
        # Remove spaces and common separators
        cleaned = re.sub(r'[\s\-\(\)]', '', message)
        match = re.search(r'\+?\d{10,12}', cleaned)
        return match.group(0) if match else None


# =============================================================================
# BUTTON ACTION HANDLER
# =============================================================================

async def handle_button_action(
    action: str,
    button_id: str,
    metadata: Dict,
    session_id: str,
    user_id: str = "anonymous"
) -> Dict:
    """
    Handle button click actions from the frontend.
    This is called when user clicks a UI button instead of typing.
    """
    
    brain = get_chat_brain()
    session = get_session(session_id, user_id)
    
    # Map actions to messages
    if action == "confirm_yes":
        return await brain.process_message("yes", session_id, user_id)
    
    elif action == "confirm_no":
        return await brain.process_message("no", session_id, user_id)
    
    elif action == "select_offer":
        offer_id = metadata.get("offer_id")
        return await brain.process_message(f"I want the {offer_id} option", session_id, user_id)
    
    elif action in ["send_email", "schedule_meeting", "book_tickets", "create_reminder"]:
        action_messages = {
            "send_email": "I want to send an email",
            "schedule_meeting": "I want to schedule a meeting",
            "book_tickets": "I want to book tickets",
            "create_reminder": "I want to set a reminder"
        }
        return await brain.process_message(action_messages[action], session_id, user_id)
    
    elif action == "open_payment":
        # Return the payment link to open
        return {
            "action": "redirect",
            "url": metadata.get("url") or metadata.get("payment_link"),
            "session_id": session_id
        }
    
    else:
        return await brain.process_message(f"Selected: {action}", session_id, user_id)


# =============================================================================
# GLOBAL BRAIN INSTANCE
# =============================================================================

_brain: Optional[IntelligentChatBrain] = None


def get_chat_brain() -> IntelligentChatBrain:
    """Get the global chat brain instance"""
    global _brain
    if _brain is None:
        _brain = IntelligentChatBrain()
    return _brain
