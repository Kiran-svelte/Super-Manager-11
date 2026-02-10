"""
Unified AI Brain - The Real Intelligence Layer

This module connects the Groq LLM with the TaskOrchestrator to actually
execute tasks and return REAL results, not fake responses.

Architecture:
- Uses Groq LLM for understanding user intent
- Delegates to TaskOrchestrator for REAL execution
- Returns actual proof of work (URLs, receipts, etc.)
"""

import os
import json
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
from datetime import datetime

# Import our task engine
from .engine import (
    TaskOrchestrator,
    Config,
    TaskType,
    TaskStatus,
    Task,
    ExecutionProof
)


class IntentType(Enum):
    """What the user wants to do"""
    SEND_EMAIL = "send_email"
    GENERATE_IMAGE = "generate_image"
    BOOK_TICKET = "book_ticket"
    MAKE_PAYMENT = "make_payment"
    WEB_SEARCH = "web_search"
    GENERAL_CHAT = "general_chat"
    SHOW_CAPABILITIES = "show_capabilities"
    UNCLEAR = "unclear"


@dataclass
class UserIntent:
    """Parsed user intent with extracted details"""
    intent_type: IntentType
    confidence: float
    extracted_data: Dict[str, Any]
    original_message: str
    clarification_needed: Optional[str] = None


@dataclass
class BrainResponse:
    """Response from the AI brain"""
    message: str
    success: bool
    intent: Optional[IntentType] = None
    execution_proof: Optional[Dict[str, Any]] = None
    ui_elements: Optional[List[Dict[str, Any]]] = None
    suggestions: Optional[List[str]] = None


class UnifiedBrain:
    """
    The central AI brain that:
    1. Understands user intent via LLM
    2. Extracts required parameters
    3. Delegates to TaskOrchestrator for real execution
    4. Returns actual results with proof
    """
    
    def __init__(self):
        self.config = Config()
        self.orchestrator = TaskOrchestrator()
        self.groq_api_key = self.config.GROQ_API_KEY
        self.conversation_history: List[Dict[str, str]] = []
        
        # System prompt that prevents fake responses
        self.system_prompt = """You are an AI assistant that EXECUTES real tasks. You are NOT a chatbot that pretends.

CRITICAL RULES:
1. NEVER say you've done something unless you receive confirmation from the system
2. NEVER generate fake data or pretend to execute tasks
3. When you detect a task intent, output a JSON command (see format below)
4. Be HONEST about limitations - if a service is unavailable, say so
5. Ask for missing information rather than making it up

YOUR CAPABILITIES (REAL, NOT FAKE):
- Send emails: Using SendGrid or SMTP (need recipient, subject, body)
- Generate images: Using Together AI or Replicate (need description)
- Search web: Using DuckDuckGo (need search query)
- Book tickets: Wonderla parks (Bangalore, Hyderabad, Kochi), Movies (redirect to BookMyShow)
- Make payments: Razorpay or UPI (need amount, recipient details)

TASK COMMAND FORMAT (output this when you detect a task):
```task
{
    "type": "send_email|generate_image|book_ticket|make_payment|web_search",
    "params": {
        // task-specific parameters
    }
}
```

EMAIL PARAMS: {"to": "email", "subject": "subject", "body": "body", "cc": "optional", "bcc": "optional"}
IMAGE PARAMS: {"prompt": "description", "count": 1-4, "size": "1024x1024"}
SEARCH PARAMS: {"query": "search terms", "max_results": 5}
TICKET PARAMS: {"type": "wonderla|movie", "venue": "bangalore|hyderabad|kochi", "date": "YYYY-MM-DD", "tickets": {"adult": N, "child": N}}
PAYMENT PARAMS: {"amount": 100, "currency": "INR", "description": "what for", "method": "razorpay|upi"}

RESPONSE GUIDELINES:
- Be concise and direct
- Don't overpromise or pretend
- If task execution fails, explain why honestly
- Provide clear next steps when asking for info
- Use natural language, not robotic responses

WHEN YOU DON'T KNOW:
- Say "I'm not sure" rather than making up information
- Suggest alternatives if the requested task isn't supported
- Be transparent about what services are available vs unavailable"""

    async def _call_groq(self, messages: List[Dict[str, str]]) -> str:
        """Call Groq API for LLM responses"""
        if not self.groq_api_key:
            return "I apologize, but I'm not configured properly. Please set up the GROQ_API_KEY."
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1024
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"API Error: {response.status_code} - {response.text[:200]}"
                    
        except Exception as e:
            return f"Connection error: {str(e)}"

    def _extract_task_command(self, llm_response: str) -> Optional[Dict[str, Any]]:
        """Extract task command JSON from LLM response"""
        # Look for ```task ... ``` blocks
        task_pattern = r'```task\s*\n?(.*?)\n?```'
        matches = re.findall(task_pattern, llm_response, re.DOTALL | re.IGNORECASE)
        
        if matches:
            try:
                return json.loads(matches[0].strip())
            except json.JSONDecodeError:
                pass
        
        # Also try to find raw JSON with task type
        json_pattern = r'\{[^{}]*"type"\s*:\s*"[^"]+_?[^"]*"[^{}]*\}'
        matches = re.findall(json_pattern, llm_response, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match)
                if "type" in data and data["type"] in [
                    "send_email", "generate_image", "book_ticket", 
                    "make_payment", "web_search"
                ]:
                    return data
            except json.JSONDecodeError:
                continue
        
        return None

    def _clean_response(self, response: str) -> str:
        """Remove task command blocks from response for user display"""
        # Remove ```task...``` blocks
        cleaned = re.sub(r'```task\s*\n?.*?\n?```', '', response, flags=re.DOTALL | re.IGNORECASE)
        # Remove standalone JSON command blocks
        cleaned = re.sub(r'```json\s*\n?\{[^}]*"type"[^}]*\}\s*\n?```', '', cleaned, flags=re.DOTALL)
        # Clean up extra whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
        return cleaned

    async def process_message(self, user_message: str, user_id: str = "default") -> BrainResponse:
        """
        Main entry point - process user message and return response
        
        Flow:
        1. Add to conversation history
        2. Send to Groq LLM with system prompt
        3. Parse response for task commands
        4. If task found, execute via TaskOrchestrator
        5. Return results with proof
        """
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add conversation history (last 10 messages)
        for msg in self.conversation_history[-10:]:
            messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Get LLM response
        llm_response = await self._call_groq(messages)
        
        # Check if LLM wants to execute a task
        task_command = self._extract_task_command(llm_response)
        
        if task_command:
            # Execute the real task
            return await self._execute_task(task_command, llm_response, user_id)
        else:
            # Just a conversational response
            self.conversation_history.append({"role": "assistant", "content": llm_response})
            
            return BrainResponse(
                message=llm_response,
                success=True,
                intent=IntentType.GENERAL_CHAT,
                suggestions=self._get_suggestions(llm_response)
            )

    async def _execute_task(
        self, 
        command: Dict[str, Any], 
        original_response: str,
        user_id: str
    ) -> BrainResponse:
        """Execute a real task via the orchestrator"""
        
        task_type_str = command.get("type", "")
        params = command.get("params", {})
        
        # Map string to TaskType enum
        type_mapping = {
            "send_email": TaskType.SEND_EMAIL,
            "generate_image": TaskType.GENERATE_IMAGE,
            "create_logo": TaskType.CREATE_LOGO,
            "book_ticket": TaskType.BOOK_TICKETS,
            "make_payment": TaskType.MAKE_PAYMENT,
            "web_search": TaskType.SEARCH_WEB
        }
        
        task_type = type_mapping.get(task_type_str)
        
        if not task_type:
            return BrainResponse(
                message=f"I don't recognize the task type '{task_type_str}'. I can help with: email, images, tickets, payments, and web search.",
                success=False,
                intent=IntentType.UNCLEAR
            )
        
        # Create task using orchestrator
        session_id = f"session_{user_id}"
        task = self.orchestrator.create_task(
            task_type=task_type.value,  # Pass string value
            user_id=user_id,
            session_id=session_id,
            initial_data=params
        )
        
        # Execute the task
        result = await self.orchestrator.execute_task(task.task_id)
        
        # Build response based on execution result
        if result.get("success"):
            return self._build_success_response(task_type, task, result, original_response)
        else:
            return self._build_failure_response(task_type, task, result, original_response)

    def _build_success_response(
        self, 
        task_type: TaskType, 
        task: Task,
        result: Dict[str, Any],
        original_response: str
    ) -> BrainResponse:
        """Build response for successful task execution"""
        
        # Get proof from result, or from task
        proof = result.get("proof") or (asdict(task.proof) if task.proof else None)
        ui_elements = []
        message = ""
        
        if task_type in [TaskType.GENERATE_IMAGE, TaskType.CREATE_LOGO]:
            # Image generation success
            images = result.get("images") or (proof.get("images", []) if proof else [])
            
            if images:
                message = f"Here are your {len(images)} generated image(s):\n\n"
                
                for i, img in enumerate(images):
                    url = img.get("url", "")
                    ui_elements.append({
                        "type": "image",
                        "url": url,
                        "alt": f"Generated image {i+1}",
                        "prompt": result.get("prompt", ""),
                        "action": {
                            "type": "download",
                            "url": url
                        }
                    })
                    message += f"• Image {i+1}: Generated successfully\n"
                
                message += "\nClick on any image to download it."
            else:
                message = "Images were generated but no URLs were returned. Please try again."
        
        elif task_type == TaskType.SEND_EMAIL:
            recipient = result.get("to") or (proof.get("recipient", "unknown") if proof else "unknown")
            subject = result.get("subject") or (proof.get("subject", "") if proof else "")
            message = f"Email sent successfully!\n\n📧 To: {recipient}\n📋 Subject: {subject}\n✅ Status: Delivered"
            
        elif task_type == TaskType.SEARCH_WEB:
            results_list = result.get("results") or (proof.get("results", []) if proof else [])
            
            if results_list:
                message = f"Found {len(results_list)} results:\n\n"
                
                for i, res in enumerate(results_list[:5]):
                    title = res.get("title", "Untitled")
                    url = res.get("url", "#")
                    snippet = res.get("snippet", "")[:100]
                    
                    ui_elements.append({
                        "type": "link_card",
                        "title": title,
                        "url": url,
                        "description": snippet
                    })
                    
                    message += f"{i+1}. {title}\n   {snippet}...\n\n"
            else:
                message = "Search completed but no results found. Try different keywords."
        
        elif task_type == TaskType.BOOK_TICKETS:
            ticket_type = result.get("ticket_type") or (proof.get("ticket_type", "ticket") if proof else "ticket")
            
            if ticket_type == "wonderla":
                pricing = result.get("pricing") or (proof.get("pricing", {}) if proof else {})
                venue = result.get("venue") or (proof.get("venue", "N/A") if proof else "N/A")
                date = result.get("date") or (proof.get("date", "Not specified") if proof else "Not specified")
                
                message = f"🎢 Wonderla Ticket Information:\n\n"
                message += f"Location: {venue}\n"
                message += f"Date: {date}\n\n"
                message += "💰 Pricing:\n"
                message += f"• Adult: ₹{pricing.get('adult', 'N/A')}\n"
                message += f"• Child: ₹{pricing.get('child', 'N/A')}\n\n"
                
                booking_url = result.get("booking_url") or (proof.get("booking_url", "https://www.wonderla.com") if proof else "https://www.wonderla.com")
                ui_elements.append({
                    "type": "button",
                    "text": "Book Now on Wonderla",
                    "url": booking_url,
                    "style": "primary"
                })
                
            elif ticket_type == "movie":
                message = "🎬 For movie tickets, I'll redirect you to BookMyShow:\n\n"
                movie_url = result.get("redirect_url") or (proof.get("redirect_url", "https://www.bookmyshow.com") if proof else "https://www.bookmyshow.com")
                
                ui_elements.append({
                    "type": "button",
                    "text": "Browse Movies on BookMyShow",
                    "url": movie_url,
                    "style": "primary"
                })
        
        elif task_type == TaskType.MAKE_PAYMENT:
            method = result.get("provider") or (proof.get("method", "payment") if proof else "payment")
            
            if method == "razorpay":
                payment_link = result.get("short_url") or (proof.get("payment_link", "") if proof else "")
                amount = result.get("amount") or (proof.get("amount", 0) if proof else 0)
                
                message = f"💳 Payment link created!\n\nAmount: ₹{amount}\n"
                
                if payment_link:
                    ui_elements.append({
                        "type": "button",
                        "text": f"Pay ₹{amount}",
                        "url": payment_link,
                        "style": "primary"
                    })
            elif method == "upi_direct":
                upi_uri = result.get("payment_url") or (proof.get("upi_uri", "") if proof else "")
                upi_id = result.get("upi_id") or (proof.get("upi_id", "") if proof else "")
                
                message = f"📱 UPI Payment Details:\n\nUPI ID: {upi_id}\n"
                message += "\nOpen your UPI app and pay to this ID."
                
                ui_elements.append({
                    "type": "upi_widget",
                    "upi_uri": upi_uri,
                    "upi_id": upi_id
                })
        
        # Save to conversation
        self.conversation_history.append({"role": "assistant", "content": message})
        
        return BrainResponse(
            message=message,
            success=True,
            intent=IntentType(task_type.value) if hasattr(IntentType, task_type.value.upper()) else IntentType.GENERAL_CHAT,
            execution_proof=proof,
            ui_elements=ui_elements if ui_elements else None
        )

    def _build_partial_response(
        self, 
        task_type: TaskType, 
        task: Task,
        original_response: str
    ) -> BrainResponse:
        """Build response for partially completed task"""
        
        proof = asdict(task.proof) if task.proof else {}
        errors = task.errors or []
        
        message = "⚠️ Task partially completed:\n\n"
        message += f"What worked: {proof.get('partial_success', 'Some steps')}\n"
        message += f"Issues: {', '.join(errors)}\n\n"
        message += "Would you like me to retry or try a different approach?"
        
        self.conversation_history.append({"role": "assistant", "content": message})
        
        return BrainResponse(
            message=message,
            success=False,
            execution_proof=proof,
            suggestions=["Retry the task", "Try alternative method", "Cancel"]
        )

    def _build_failure_response(
        self, 
        task_type: TaskType, 
        task: Task,
        result: Dict[str, Any],
        original_response: str
    ) -> BrainResponse:
        """Build response for failed task"""
        
        # Get errors from result or task
        errors = []
        if result.get("error"):
            errors.append(result.get("error"))
        if result.get("missing_fields"):
            errors.append(f"Missing: {', '.join(result.get('missing_fields', []))}")
        if not errors:
            errors = task.errors or ["Unknown error occurred"]
        
        # Provide honest, helpful error messages
        error_messages = {
            TaskType.SEND_EMAIL: "I couldn't send the email. Reason: {}. Please check if the email configuration (SendGrid or SMTP) is properly set up.",
            TaskType.GENERATE_IMAGE: "Image generation failed. Reason: {}. This might be due to API limits or service unavailability.",
            TaskType.CREATE_LOGO: "Logo generation failed. Reason: {}. This might be due to API limits or service unavailability.",
            TaskType.SEARCH_WEB: "Web search failed. Reason: {}. Please try again with different search terms.",
            TaskType.BOOK_TICKETS: "Ticket booking failed. Reason: {}.",
            TaskType.MAKE_PAYMENT: "Payment creation failed. Reason: {}. Please verify payment gateway configuration."
        }
        
        template = error_messages.get(task_type, "Task failed. Reason: {}")
        message = template.format(", ".join(errors))
        
        # Add available services info
        available = self.config.get_available_services()
        if available:
            message += f"\n\n✅ Currently available services: {', '.join(available)}"
        
        self.conversation_history.append({"role": "assistant", "content": message})
        
        return BrainResponse(
            message=message,
            success=False,
            suggestions=["Try again", "What else can you do?"]
        )

    def _get_suggestions(self, response: str) -> List[str]:
        """Generate contextual suggestions based on conversation"""
        
        # Default suggestions
        default = [
            "Generate an image",
            "Send an email",
            "Search the web",
            "Book tickets"
        ]
        
        # Could be enhanced with LLM-based suggestion generation
        return default

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    def get_capabilities(self) -> Dict[str, Any]:
        """Return current capabilities and their status"""
        
        available = self.config.get_available_services()
        
        return {
            "email": {
                "available": "email" in available,
                "provider": "SendGrid" if self.config.SENDGRID_API_KEY else "SMTP" if self.config.SMTP_HOST else None,
                "description": "Send real emails to any recipient"
            },
            "image_generation": {
                "available": "image" in available,
                "provider": "Together AI" if self.config.TOGETHER_API_KEY else "Replicate" if self.config.REPLICATE_API_TOKEN else None,
                "description": "Generate images from text descriptions"
            },
            "web_search": {
                "available": True,  # DuckDuckGo always available
                "provider": "DuckDuckGo",
                "description": "Search the web for information"
            },
            "tickets": {
                "available": True,  # Info is always available
                "provider": "Wonderla + BookMyShow",
                "description": "Book theme park and movie tickets"
            },
            "payments": {
                "available": "payment" in available,
                "provider": "Razorpay" if self.config.RAZORPAY_KEY_ID else "UPI Direct",
                "description": "Create payment links or UPI payments"
            },
            "llm": {
                "available": bool(self.config.GROQ_API_KEY),
                "provider": "Groq (Llama 3.1 70B)",
                "description": "Natural language understanding"
            }
        }


# Singleton instance for the app
_brain_instance: Optional[UnifiedBrain] = None


def get_brain() -> UnifiedBrain:
    """Get or create the singleton brain instance"""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = UnifiedBrain()
    return _brain_instance


# FastAPI integration helper
async def chat_handler(message: str, user_id: str = "default") -> Dict[str, Any]:
    """
    Handler for chat endpoint
    Returns response in format expected by frontend
    """
    brain = get_brain()
    response = await brain.process_message(message, user_id)
    
    # Convert ui_elements to ui_components format expected by frontend
    ui_components = None
    if response.ui_elements:
        # Check if we have images
        images = [el for el in response.ui_elements if el.get("type") == "image"]
        buttons = [el for el in response.ui_elements if el.get("type") == "button"]
        link_cards = [el for el in response.ui_elements if el.get("type") == "link_card"]
        
        if images:
            # Create image_gallery component
            ui_components = {
                "type": "image_gallery",
                "images": [
                    {
                        "id": f"img_{i}",
                        "url": img.get("url"),
                        "alt": img.get("alt", f"Generated image {i+1}"),
                        "prompt": img.get("prompt", ""),
                        "downloadable": True
                    }
                    for i, img in enumerate(images)
                ],
                "actions": [
                    {
                        "id": "regenerate",
                        "action": "regenerate_logos",
                        "label": "Generate More"
                    }
                ]
            }
        elif buttons:
            # Create button_group component
            ui_components = {
                "type": "button_group",
                "layout": "horizontal",
                "buttons": [
                    {
                        "id": btn.get("id", f"btn_{i}"),
                        "label": btn.get("text", btn.get("label", "Click")),
                        "url": btn.get("url"),
                        "action": btn.get("action"),
                        "style": btn.get("style", "primary")
                    }
                    for i, btn in enumerate(buttons)
                ]
            }
        elif link_cards:
            # Create card_grid component
            ui_components = {
                "type": "card_grid",
                "cards": [
                    {
                        "id": f"card_{i}",
                        "title": card.get("title"),
                        "description": card.get("description"),
                        "style": "bordered",
                        "actions": [
                            {
                                "id": f"open_{i}",
                                "label": "Open",
                                "url": card.get("url"),
                                "style": "secondary"
                            }
                        ] if card.get("url") else []
                    }
                    for i, card in enumerate(link_cards)
                ]
            }
    
    return {
        "message": response.message,
        "success": response.success,
        "type": "task" if response.execution_proof else "answer",
        "status": "done" if response.success and response.execution_proof else None,
        "intent": response.intent.value if response.intent else None,
        "proof": response.execution_proof,
        "ui_components": ui_components,
        "suggestions": response.suggestions,
        "timestamp": datetime.now().isoformat()
    }
