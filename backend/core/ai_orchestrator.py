"""
Real AI Chat Orchestrator
Main orchestrator that brings together all components for a production-ready AI assistant.
Handles task understanding, execution, verification, and interactive responses.
"""

import asyncio
import json
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import openai
import anthropic

from .task_engine import TaskEngine, TaskCategory, TaskStatus, SecurityLevel, IntentParser, TaskContext
from .interactive_ui import UIBuilder, InteractiveResponse, ButtonGroup, Button, ButtonStyle, CardGrid, Form
from .secure_payment import SecurePaymentService, PaymentMethod, PaymentStatus
from .real_integrations import CommunicationService, EmailMessage, CalendarEvent, MeetingPlatform
from .verification_system import VerificationService, ProofType

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """State of the conversation"""
    IDLE = "idle"
    COLLECTING_INFO = "collecting_info"
    AWAITING_SELECTION = "awaiting_selection"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ConversationContext:
    """Context for ongoing conversation"""
    session_id: str
    user_id: str
    state: ConversationState = ConversationState.IDLE
    current_task_id: Optional[str] = None
    current_intent: Optional[Dict] = None
    collected_data: Dict = field(default_factory=dict)
    pending_requirements: List[Dict] = field(default_factory=list)
    messages: List[Dict] = field(default_factory=list)
    user_tokens: Dict = field(default_factory=dict)  # OAuth tokens
    user_preferences: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


class AIProvider:
    """AI model provider for natural language understanding"""
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GOOGLE_AI_API_KEY")
        
        if self.openai_key:
            self.openai_client = openai.AsyncOpenAI(api_key=self.openai_key)
        else:
            self.openai_client = None
            
        if self.anthropic_key:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)
        else:
            self.anthropic_client = None
    
    async def understand_intent(self, message: str, context: List[Dict] = None) -> Dict:
        """Use AI to understand user intent"""
        
        system_prompt = """You are an AI assistant that analyzes user requests and extracts structured information.
        
Analyze the user's message and extract:
1. Primary intent/task category
2. All relevant parameters
3. Any missing information needed
4. Confidence level

Categories: booking, payment, scheduling, communication, creative, travel, shopping, research

Respond in JSON format:
{
    "category": "category_name",
    "sub_category": "specific_type",
    "parameters": {
        "param1": "value1",
        ...
    },
    "missing_info": ["list of missing required info"],
    "confidence": 0.0-1.0,
    "summary": "brief description of what user wants"
}"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            for msg in context[-5:]:  # Last 5 messages for context
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        messages.append({"role": "user", "content": message})
        
        try:
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                return json.loads(response.choices[0].message.content)
            elif self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": message}]
                )
                return json.loads(response.content[0].text)
            else:
                # Fallback to rule-based parsing
                return IntentParser.parse(message)
        except Exception as e:
            logger.error(f"AI intent parsing error: {str(e)}")
            return IntentParser.parse(message)
    
    async def generate_response(
        self,
        context: ConversationContext,
        task_result: Dict = None,
        response_type: str = "default"
    ) -> str:
        """Generate natural language response"""
        
        system_prompt = """You are Super Manager, an AI assistant that helps users with various tasks.
        
Guidelines:
- Be helpful, concise, and friendly
- Explain what you're doing clearly
- If asking for information, explain why you need it
- If presenting options, explain the differences briefly
- For payments and sensitive actions, emphasize security
- Always provide confirmation details after completing tasks

Current context will be provided with each message."""
        
        user_context = f"""
Current task: {context.current_intent.get('summary') if context.current_intent else 'None'}
Collected info: {json.dumps(context.collected_data)}
Task result: {json.dumps(task_result) if task_result else 'None'}
Response type: {response_type}
"""
        
        try:
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_context}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI response generation error: {str(e)}")
        
        # Fallback responses
        if response_type == "confirmation":
            return "Task completed successfully!"
        elif response_type == "error":
            return "I encountered an issue. Please try again."
        else:
            return "How can I help you?"


class RealAIChatOrchestrator:
    """Main orchestrator for the AI chat assistant"""
    
    def __init__(self):
        self.ai_provider = AIProvider()
        self.task_engine = TaskEngine()
        self.payment_service = SecurePaymentService()
        self.verification_service = VerificationService()
        
        # Active sessions
        self.sessions: Dict[str, ConversationContext] = {}
    
    def get_or_create_session(self, session_id: str, user_id: str = None) -> ConversationContext:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id or f"user_{secrets.token_hex(4)}"
            )
        return self.sessions[session_id]
    
    def create_communication_service(self, context: ConversationContext) -> CommunicationService:
        """Create communication service with user's tokens"""
        return CommunicationService(context.user_tokens)
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        user_id: str = None,
        metadata: Dict = None
    ) -> Dict:
        """Process an incoming message and return response"""
        
        context = self.get_or_create_session(session_id, user_id)
        context.last_activity = datetime.now()
        
        # Add message to history
        context.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Check if this is a response to a pending action
        if context.state == ConversationState.AWAITING_SELECTION:
            return await self._handle_selection(context, message)
        elif context.state == ConversationState.AWAITING_CONFIRMATION:
            return await self._handle_confirmation(context, message)
        elif context.state == ConversationState.COLLECTING_INFO:
            return await self._handle_info_collection(context, message)
        
        # New request - understand intent
        intent = await self.ai_provider.understand_intent(message, context.messages)
        context.current_intent = intent
        
        # Route based on category
        category = intent.get("category", "research")
        
        handlers = {
            "booking": self._handle_booking_request,
            "payment": self._handle_payment_request,
            "scheduling": self._handle_scheduling_request,
            "communication": self._handle_communication_request,
            "shopping": self._handle_shopping_request,
            "travel": self._handle_travel_request,
            "creative": self._handle_creative_request,
            "research": self._handle_research_request
        }
        
        handler = handlers.get(category, self._handle_general_request)
        return await handler(context, intent)
    
    async def _handle_booking_request(self, context: ConversationContext, intent: Dict) -> Dict:
        """Handle booking requests (tickets, reservations, etc.)"""
        
        params = intent.get("parameters", {})
        missing = intent.get("missing_info", [])
        
        # Check what type of booking
        sub_category = intent.get("sub_category", "general")
        
        # If it's an event/park booking like Wonderla
        if sub_category in ["event", "amusement_park", "tickets"]:
            venue = params.get("venue") or params.get("destination")
            quantity = params.get("quantity") or params.get("people", 1)
            group_type = params.get("group_type")  # student, family, etc.
            
            # Search for offers first
            offers_result = await self.verification_service.real_booking.search_offers(
                venue=venue or "Wonderla Bangalore",
                date=datetime.now() + timedelta(days=1),
                group_size=int(quantity) if quantity else 1,
                group_type=group_type
            )
            
            if offers_result.get("applicable_offers"):
                # Present offers with interactive cards
                response = InteractiveResponse()
                
                offers = offers_result.get("applicable_offers", [])
                best_offer = offers_result.get("best_offer")
                
                # Format offer cards
                offer_cards = []
                for offer in offers:
                    offer_cards.append({
                        "id": offer["id"],
                        "label": offer["offer_name"],
                        "description": offer["description"],
                        "icon": "🎟️" if offer.get("recommended") else "🏷️",
                        "metadata": {
                            "price": offer["discounted_price"],
                            "original_price": offer["original_price"],
                            "discount": f"{offer['discount_percent']}% off",
                            "total": offer["discounted_price"] * int(quantity or 1)
                        },
                        "recommended": offer.get("recommended", False)
                    })
                
                text = f"I found {len(offers)} offers for {venue}!\n\n"
                
                if best_offer:
                    savings = offers_result.get("savings_with_best_offer", 0)
                    text += f"💡 **Best Deal**: {best_offer['offer_name']} saves you ₹{savings:,.0f}\n\n"
                
                text += "Please select an offer to continue:"
                
                context.state = ConversationState.AWAITING_SELECTION
                context.collected_data["offers"] = offers
                context.collected_data["venue"] = venue
                context.collected_data["quantity"] = quantity
                context.collected_data["group_type"] = group_type
                
                return response.with_text(text).with_buttons(
                    offer_cards,
                    layout="vertical"
                ).with_metadata(
                    task_type="offer_selection",
                    venue=venue
                ).build()
        
        # Generic booking flow
        if missing:
            return await self._request_missing_info(context, missing, "booking")
        
        return {
            "text": "I can help you with that booking. Let me find the best options for you.",
            "interactive": False,
            "status": "processing"
        }
    
    async def _handle_selection(self, context: ConversationContext, message: str) -> Dict:
        """Handle user selection from options"""
        
        # Parse selection (could be button click ID or text)
        selection = message.lower().strip()
        
        offers = context.collected_data.get("offers", [])
        
        # Find matching offer
        selected_offer = None
        for offer in offers:
            if offer["id"].lower() in selection or offer["offer_name"].lower() in selection:
                selected_offer = offer
                break
        
        # Also check for "yes", "confirm", number selection
        if not selected_offer:
            if selection in ["1", "first", "best", "recommended"]:
                # Select best/recommended offer
                selected_offer = next((o for o in offers if o.get("recommended")), offers[0] if offers else None)
            elif selection.isdigit() and int(selection) <= len(offers):
                selected_offer = offers[int(selection) - 1]
        
        if selected_offer:
            context.collected_data["selected_offer"] = selected_offer
            
            quantity = int(context.collected_data.get("quantity", 1))
            total = selected_offer["discounted_price"] * quantity
            
            # Show confirmation with payment
            context.state = ConversationState.AWAITING_CONFIRMATION
            
            details = [
                {"label": "Venue", "value": context.collected_data.get("venue")},
                {"label": "Offer", "value": selected_offer["offer_name"]},
                {"label": "Tickets", "value": str(quantity)},
                {"label": "Price/ticket", "value": f"₹{selected_offer['discounted_price']:,.0f}"},
                {"label": "Total", "value": f"₹{total:,.0f}"}
            ]
            
            response = InteractiveResponse()
            return response.with_text(
                f"Great choice! Here's your booking summary:\n\n"
                f"**{selected_offer['offer_name']}**\n"
                f"• {quantity} tickets × ₹{selected_offer['discounted_price']:,.0f} = **₹{total:,.0f}**\n\n"
                f"Original price would have been ₹{selected_offer['original_price'] * quantity:,.0f}\n"
                f"You're saving ₹{(selected_offer['original_price'] - selected_offer['discounted_price']) * quantity:,.0f}! 🎉\n\n"
                f"Before I proceed with the booking, I need some details."
            ).with_component(
                UIBuilder.create_booking_form("ticket", {"quantity": quantity})
            ).with_metadata(
                task_type="booking_form",
                requires_payment=True,
                amount=total
            ).build()
        
        return {
            "text": "I couldn't understand your selection. Please select one of the offers above or type the offer name.",
            "interactive": True
        }
    
    async def _handle_confirmation(self, context: ConversationContext, message: str) -> Dict:
        """Handle confirmation responses"""
        
        message_lower = message.lower().strip()
        
        # Check for cancellation
        if any(word in message_lower for word in ["cancel", "no", "stop", "abort"]):
            context.state = ConversationState.IDLE
            context.collected_data = {}
            return {
                "text": "No problem! The booking has been cancelled. Is there anything else I can help you with?",
                "interactive": False
            }
        
        # Check for confirmation with form data
        if message_lower in ["yes", "confirm", "proceed", "ok", "okay"]:
            # Need to collect customer details first
            if not context.collected_data.get("customer_details"):
                return {
                    "text": "Please fill in the booking form above with your details first.",
                    "interactive": True
                }
        
        # Try to parse as form submission (JSON from frontend)
        try:
            form_data = json.loads(message)
            context.collected_data["customer_details"] = form_data
        except:
            # Try to extract details from text
            pass
        
        # If we have all details, proceed to payment
        if context.collected_data.get("customer_details") or context.collected_data.get("selected_offer"):
            return await self._initiate_booking_payment(context)
        
        return {
            "text": "Please confirm your booking details or provide the required information.",
            "interactive": True
        }
    
    async def _initiate_booking_payment(self, context: ConversationContext) -> Dict:
        """Initiate payment for booking"""
        
        selected_offer = context.collected_data.get("selected_offer", {})
        quantity = int(context.collected_data.get("quantity", 1))
        venue = context.collected_data.get("venue", "Venue")
        total = selected_offer.get("discounted_price", 1000) * quantity
        
        # Initiate secure payment
        payment_result = await self.payment_service.initiate_payment(
            user_id=context.user_id,
            amount=total,
            description=f"{quantity}x {selected_offer.get('offer_name', 'Tickets')} at {venue}",
            merchant_id=venue.lower().replace(" ", "_"),
            merchant_name=venue,
            items=[{
                "name": selected_offer.get("offer_name", "Ticket"),
                "quantity": quantity,
                "price": selected_offer.get("discounted_price", 1000)
            }]
        )
        
        if not payment_result.get("success"):
            return {
                "text": f"Sorry, there was an issue initiating the payment: {payment_result.get('error')}",
                "interactive": False,
                "status": "error"
            }
        
        context.collected_data["payment_id"] = payment_result["payment_id"]
        
        # Check if OTP is required
        if payment_result.get("requires_otp"):
            context.state = ConversationState.COLLECTING_INFO
            context.pending_requirements = [{"name": "phone", "type": "phone"}]
            
            return {
                "text": f"To complete your booking of ₹{total:,.0f}, I need to verify your identity.\n\n"
                       f"Please enter your phone number to receive an OTP:",
                "interactive": False,
                "metadata": {
                    "input_type": "phone",
                    "payment_id": payment_result["payment_id"]
                }
            }
        
        # Low amount, proceed directly to payment
        return await self._show_payment_options(context, payment_result)
    
    async def _show_payment_options(self, context: ConversationContext, payment_data: Dict) -> Dict:
        """Show payment options to user"""
        
        response = InteractiveResponse()
        
        payment_methods = [
            {"id": "upi", "label": "Pay with UPI", "icon": "📱", "description": "Google Pay, PhonePe, Paytm, etc."},
            {"id": "card", "label": "Credit/Debit Card", "icon": "💳", "description": "Visa, Mastercard, RuPay"},
            {"id": "netbanking", "label": "Net Banking", "icon": "🏦", "description": "All major banks"}
        ]
        
        return response.with_text(
            f"**Secure Payment**\n\n"
            f"Amount: **{payment_data.get('formatted_amount', payment_data.get('amount'))}**\n"
            f"Reference: `{payment_data.get('payment_id')}`\n\n"
            f"Choose your preferred payment method:"
        ).with_buttons(
            payment_methods,
            layout="vertical"
        ).with_metadata(
            task_type="payment_method_selection",
            payment_id=payment_data.get("payment_id"),
            amount=payment_data.get("amount")
        ).build()
    
    async def _handle_info_collection(self, context: ConversationContext, message: str) -> Dict:
        """Handle information collection flow"""
        
        pending = context.pending_requirements
        
        if not pending:
            context.state = ConversationState.IDLE
            return await self.process_message(context.session_id, message, context.user_id)
        
        current_req = pending[0]
        
        # Validate and store the response
        if current_req.get("type") == "phone":
            # Validate phone number
            phone = re.sub(r'\D', '', message)
            if len(phone) >= 10:
                context.collected_data["phone"] = phone
                
                # Send OTP
                payment_id = context.collected_data.get("payment_id")
                if payment_id:
                    otp_result = await self.payment_service.send_verification_otp(
                        payment_id=payment_id,
                        phone_number=phone,
                        session_token=self.payment_service.transactions[payment_id].session_token
                    )
                    
                    if otp_result.get("success"):
                        context.pending_requirements = [{"name": "otp", "type": "otp"}]
                        
                        return {
                            "text": f"✅ OTP sent to ******{phone[-4:]}\n\n"
                                   f"Please enter the 6-digit OTP to verify your payment:",
                            "interactive": False,
                            "metadata": {
                                "input_type": "otp",
                                "expires_in": 300
                            }
                        }
                    else:
                        return {
                            "text": f"Failed to send OTP: {otp_result.get('error')}. Please try again.",
                            "interactive": False
                        }
            else:
                return {
                    "text": "Please enter a valid 10-digit phone number:",
                    "interactive": False
                }
        
        elif current_req.get("type") == "otp":
            otp = re.sub(r'\D', '', message)
            if len(otp) == 6:
                payment_id = context.collected_data.get("payment_id")
                
                if payment_id:
                    transaction = self.payment_service.transactions.get(payment_id)
                    verify_result = await self.payment_service.verify_otp(
                        payment_id=payment_id,
                        otp=otp,
                        session_token=transaction.session_token if transaction else ""
                    )
                    
                    if verify_result.get("success"):
                        context.pending_requirements = []
                        
                        # Show payment options
                        return await self._show_payment_options(context, {
                            "payment_id": payment_id,
                            "formatted_amount": f"₹{transaction.amount:,.2f}" if transaction else "",
                            "amount": transaction.amount if transaction else 0
                        })
                    else:
                        return {
                            "text": f"❌ {verify_result.get('error')}\n\nPlease enter the correct OTP:",
                            "interactive": False
                        }
            else:
                return {
                    "text": "Please enter the 6-digit OTP sent to your phone:",
                    "interactive": False
                }
        
        return {
            "text": f"Please provide the required information: {current_req.get('name')}",
            "interactive": False
        }
    
    async def _handle_payment_request(self, context: ConversationContext, intent: Dict) -> Dict:
        """Handle payment-related requests"""
        
        params = intent.get("parameters", {})
        amount = params.get("amount")
        recipient = params.get("recipient")
        
        if not amount:
            return {
                "text": "What amount would you like to pay?",
                "interactive": False,
                "metadata": {"input_type": "amount"}
            }
        
        # Parse amount
        try:
            amount = float(re.sub(r'[^\d.]', '', str(amount)))
        except:
            return {
                "text": "I couldn't understand the amount. Please enter the amount in numbers (e.g., 5000):",
                "interactive": False
            }
        
        # High security for payments
        if amount >= 500:
            context.state = ConversationState.COLLECTING_INFO
            context.pending_requirements = [{"name": "phone", "type": "phone"}]
            context.collected_data["payment_amount"] = amount
            context.collected_data["payment_recipient"] = recipient
            
            return {
                "text": f"🔐 **Secure Payment**\n\n"
                       f"Amount: **₹{amount:,.2f}**\n"
                       f"To: {recipient or 'Not specified'}\n\n"
                       f"For your security, please verify your phone number to proceed:",
                "interactive": False,
                "metadata": {"input_type": "phone", "security_level": "high"}
            }
        
        return {
            "text": f"I'll help you pay ₹{amount:,.2f}. Please confirm the recipient details.",
            "interactive": False
        }
    
    async def _handle_scheduling_request(self, context: ConversationContext, intent: Dict) -> Dict:
        """Handle meeting/calendar requests"""
        
        params = intent.get("parameters", {})
        missing = intent.get("missing_info", [])
        
        # Check if user has connected calendar
        comm_service = self.create_communication_service(context)
        
        if not context.user_tokens.get("google_access_token"):
            auth_url = comm_service.get_auth_url()
            
            response = InteractiveResponse()
            return response.with_text(
                "To schedule meetings on your behalf, I need access to your Google Calendar.\n\n"
                "This will allow me to:\n"
                "• Check your availability\n"
                "• Create calendar events\n"
                "• Send meeting invitations\n\n"
                "Click below to connect your Google account:"
            ).with_buttons([
                {"id": "connect_google", "label": "Connect Google Account", "icon": "🔗"}
            ]).with_metadata(
                auth_url=auth_url,
                action="oauth_redirect"
            ).build()
        
        # If we have missing info, request it
        if missing:
            return await self._request_missing_info(context, missing, "meeting")
        
        # All info available, schedule the meeting
        title = params.get("title") or params.get("subject", "Meeting")
        attendees = params.get("attendees", [])
        if isinstance(attendees, str):
            attendees = [a.strip() for a in attendees.split(",")]
        
        # Parse date/time
        date_str = params.get("date")
        time_str = params.get("time")
        duration = int(params.get("duration", 60))
        
        # Default to tomorrow at 10 AM if not specified
        start_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end_time = start_time + timedelta(minutes=duration)
        
        # Create meeting
        result = await comm_service.schedule_meeting(
            title=title,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            description=params.get("description", ""),
            platform=MeetingPlatform.GOOGLE_MEET
        )
        
        if result.get("success"):
            response = InteractiveResponse()
            return response.with_text(
                f"✅ **Meeting Scheduled!**\n\n"
                f"**{title}**\n"
                f"📅 {start_time.strftime('%B %d, %Y')}\n"
                f"🕐 {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}\n"
                f"👥 {', '.join(attendees) if attendees else 'No attendees'}\n\n"
                f"📎 Meeting Link: {result.get('meeting_link', 'Will be shared via email')}\n\n"
                f"Calendar invites have been sent to all attendees."
            ).with_buttons([
                {"id": "add_to_calendar", "label": "Open in Calendar", "icon": "📅"},
                {"id": "copy_link", "label": "Copy Meeting Link", "icon": "🔗"}
            ]).with_metadata(
                meeting_id=result.get("event_id"),
                meeting_link=result.get("meeting_link"),
                calendar_link=result.get("calendar_link")
            ).build()
        else:
            if result.get("auth_required"):
                return {
                    "text": f"I need access to your calendar to schedule meetings. {result.get('error', '')}",
                    "interactive": True,
                    "metadata": {"auth_url": result.get("auth_url")}
                }
            return {
                "text": f"Sorry, I couldn't schedule the meeting: {result.get('error')}",
                "interactive": False
            }
    
    async def _handle_communication_request(self, context: ConversationContext, intent: Dict) -> Dict:
        """Handle email/communication requests"""
        
        params = intent.get("parameters", {})
        missing = intent.get("missing_info", [])
        
        comm_service = self.create_communication_service(context)
        
        sub_category = intent.get("sub_category", "email")
        
        if sub_category == "email":
            to = params.get("to") or params.get("recipient")
            subject = params.get("subject")
            body = params.get("body") or params.get("content")
            
            if not all([to, subject, body]):
                # Need more info
                missing_fields = []
                if not to:
                    missing_fields.append("recipient email address")
                if not subject:
                    missing_fields.append("email subject")
                if not body:
                    missing_fields.append("email content")
                
                return {
                    "text": f"To send the email, I need: {', '.join(missing_fields)}.\n\nPlease provide these details.",
                    "interactive": False
                }
            
            # Send email
            result = await comm_service.send_email(
                to=[to] if isinstance(to, str) else to,
                subject=subject,
                body=body
            )
            
            if result.get("success"):
                return {
                    "text": f"✅ **Email Sent Successfully!**\n\n"
                           f"**To:** {to}\n"
                           f"**Subject:** {subject}\n\n"
                           f"Tracking ID: `{result.get('tracking_id')}`",
                    "interactive": False,
                    "metadata": {"email_id": result.get("message_id")}
                }
            elif result.get("auth_required"):
                return {
                    "text": "I need access to your email account to send emails on your behalf. "
                           "Would you like to connect your Gmail account?",
                    "interactive": True,
                    "metadata": {"auth_url": result.get("auth_url")}
                }
            else:
                return {
                    "text": f"Failed to send email: {result.get('error')}",
                    "interactive": False
                }
        
        return {"text": "I can help with that. What would you like to communicate?", "interactive": False}
    
    async def _handle_shopping_request(self, context: ConversationContext, intent: Dict) -> Dict:
        """Handle shopping/offer search requests"""
        return await self._handle_booking_request(context, intent)
    
    async def _handle_travel_request(self, context: ConversationContext, intent: Dict) -> Dict:
        """Handle travel planning requests"""
        params = intent.get("parameters", {})
        
        return {
            "text": f"I can help you plan a trip to {params.get('destination', 'your destination')}. "
                   f"Let me find the best options for flights, hotels, and activities.",
            "interactive": False,
            "status": "processing"
        }
    
    async def _handle_creative_request(self, context: ConversationContext, intent: Dict) -> Dict:
        """Handle creative tasks (logo design, etc.)"""
        params = intent.get("parameters", {})
        
        return {
            "text": f"I'll help you create a {params.get('type', 'design')}. "
                   f"Let me work on that for you.",
            "interactive": False,
            "status": "processing"
        }
    
    async def _handle_research_request(self, context: ConversationContext, intent: Dict) -> Dict:
        """Handle research/information requests"""
        
        # Use AI to generate response
        response = await self.ai_provider.generate_response(context, response_type="research")
        
        return {
            "text": response,
            "interactive": False
        }
    
    async def _handle_general_request(self, context: ConversationContext, intent: Dict) -> Dict:
        """Handle general requests"""
        return await self._handle_research_request(context, intent)
    
    async def _request_missing_info(
        self,
        context: ConversationContext,
        missing: List[str],
        task_type: str
    ) -> Dict:
        """Request missing information from user"""
        
        context.state = ConversationState.COLLECTING_INFO
        context.pending_requirements = [{"name": item} for item in missing]
        
        if len(missing) == 1:
            return {
                "text": f"To complete this {task_type}, I need to know: {missing[0]}",
                "interactive": False
            }
        
        return {
            "text": f"To complete this {task_type}, I need a few details:\n\n" +
                   "\n".join([f"• {item}" for item in missing]),
            "interactive": False
        }
    
    async def handle_button_click(
        self,
        session_id: str,
        button_id: str,
        metadata: Dict = None
    ) -> Dict:
        """Handle button click from UI"""
        
        context = self.get_or_create_session(session_id)
        
        # Route based on button action
        if button_id.startswith("select_offer:"):
            offer_id = button_id.split(":")[1]
            return await self.process_message(session_id, offer_id, context.user_id)
        
        elif button_id.startswith("payment_method:"):
            method = button_id.split(":")[1]
            return await self._process_payment_method(context, method)
        
        elif button_id == "connect_google":
            # Return OAuth URL
            comm_service = self.create_communication_service(context)
            return {
                "type": "oauth_redirect",
                "url": comm_service.get_auth_url()
            }
        
        return await self.process_message(session_id, button_id, context.user_id)
    
    async def _process_payment_method(self, context: ConversationContext, method: str) -> Dict:
        """Process selected payment method"""
        
        payment_id = context.collected_data.get("payment_id")
        if not payment_id:
            return {"text": "Payment session expired. Please start again.", "interactive": False}
        
        transaction = self.payment_service.transactions.get(payment_id)
        if not transaction:
            return {"text": "Payment not found. Please start again.", "interactive": False}
        
        payment_method = PaymentMethod(method) if method in [m.value for m in PaymentMethod] else PaymentMethod.UPI
        
        result = await self.payment_service.process_payment(
            payment_id=payment_id,
            method=payment_method,
            payment_details={"payee_vpa": "merchant@upi"},
            session_token=transaction.session_token
        )
        
        if result.get("success"):
            if method == "upi":
                response = InteractiveResponse()
                return response.with_text(
                    f"**Complete Payment via UPI**\n\n"
                    f"Amount: **{result.get('formatted_amount')}**\n"
                    f"UPI ID: `{result.get('payee_vpa')}`\n\n"
                    f"**Option 1:** Click your preferred UPI app below\n"
                    f"**Option 2:** Copy the UPI ID and pay from any app\n\n"
                    f"Reference: `{result.get('reference_id')}`"
                ).with_buttons([
                    {"id": "gpay", "label": "Google Pay", "icon": "📱"},
                    {"id": "phonepe", "label": "PhonePe", "icon": "📱"},
                    {"id": "paytm", "label": "Paytm", "icon": "📱"}
                ]).with_metadata(
                    upi_link=result.get("upi_link"),
                    deep_links=result.get("deep_links"),
                    reference_id=result.get("reference_id")
                ).build()
            else:
                return {
                    "text": f"Please complete your payment of {result.get('formatted_amount')} on the payment page.",
                    "interactive": False,
                    "metadata": {"payment_link": result.get("payment_link")}
                }
        
        return {
            "text": f"Payment initiation failed: {result.get('error')}",
            "interactive": False
        }


# Export main orchestrator instance
chat_orchestrator = RealAIChatOrchestrator()
