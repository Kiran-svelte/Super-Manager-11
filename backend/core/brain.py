"""
SUPER MANAGER - AI BRAIN v6 (Adaptive Agent + ToolRegistry + MCP + Stealth)
=============================================================================
General-purpose AI agent that can handle ANY request.
Uses Adaptive Agent pattern: dynamic code generation with tools.

Architecture:
- ToolRegistry: Unified tool layer (primitives, MCP, stealth, payment, fallback, workflows)
- AdaptiveAgent: Think -> Generate Code -> Classify Risk -> Execute -> Observe loop
- Sandbox: Restricted code execution with risk classification
- Strategy Store: Learns from successful task patterns
- Session management: Conversation history + pending confirmations
- Feedback system: Red/green user ratings that influence future responses
- SSE streaming: Real-time progress events
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Import the Adaptive Agent
from .adaptive_agent import AdaptiveAgent, AgentEvent

# Import tool registration functions (register tools on startup)
from .tool_registry import get_tool_registry
from .payment_links import register_payment_tools
from .stealth_browser import register_stealth_tools
from .human_fallback import register_fallback_tools
from .mcp_client import get_mcp_client
from .teaching_mode import get_teaching_mode


# =============================================================================
# CONFIRMATION KEYWORDS (expanded)
# =============================================================================
CONFIRM_YES = {
    "yes", "yeah", "yep", "yea", "confirm", "ok", "okay", "sure",
    "do it", "go ahead", "go for it", "proceed", "send", "pay",
    "absolutely", "please", "please do", "approved", "y", "affirmative",
    "correct", "right", "definitely", "of course", "fine", "accept",
}

CONFIRM_NO = {
    "no", "nah", "nope", "cancel", "don't", "stop", "nevermind",
    "never mind", "abort", "decline", "reject", "n", "negative",
    "not now", "skip", "pass", "forget it",
}


def _is_confirmation(text: str, keywords: set) -> bool:
    """Check if text contains any confirmation keyword"""
    lower = text.lower().strip()
    if lower in keywords:
        return True
    for kw in keywords:
        if " " in kw and kw in lower:
            return True
    words = set(lower.split())
    return bool(words & {kw for kw in keywords if " " not in kw})


# =============================================================================
# DATA MODELS
# =============================================================================
class MessageType(str, Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


@dataclass
class Message:
    role: MessageType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Session:
    id: str
    messages: List[Message] = field(default_factory=list)
    user_data: Dict[str, Any] = field(default_factory=dict)
    pending_confirmation: Optional[Dict[str, Any]] = None
    feedback_history: List[Dict[str, Any]] = field(default_factory=list)


# =============================================================================
# DATABASE - In-Memory Session Store
# =============================================================================
class Database:
    """Session storage - replace with Supabase/PostgreSQL in production"""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.users: Dict[str, Dict] = {}
        self.feedback: Dict[str, List[Dict]] = {}
        self.memory: Dict[str, Dict[str, str]] = {}  # user_id -> {key: value}

    def get_session(self, session_id: str) -> Session:
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(id=session_id)
        return self.sessions[session_id]

    def save_user(self, identifier: str, data: Dict):
        self.users[identifier] = {**self.users.get(identifier, {}), **data}

    def get_user(self, identifier: str) -> Optional[Dict]:
        return self.users.get(identifier)

    def add_feedback(self, user_id: str, feedback: Dict):
        if user_id not in self.feedback:
            self.feedback[user_id] = []
        self.feedback[user_id].append(feedback)

    def get_feedback(self, user_id: str, limit: int = 5) -> List[Dict]:
        return self.feedback.get(user_id, [])[-limit:]

    def get_memory(self, user_id: str) -> Dict[str, str]:
        return self.memory.get(user_id, {})

    def save_memory(self, user_id: str, key: str, value: str):
        if user_id not in self.memory:
            self.memory[user_id] = {}
        self.memory[user_id][key] = value


db = Database()


# =============================================================================
# AI BRAIN - Adaptive Agent Wrapper
# =============================================================================
class AIBrain:
    """
    General-purpose AI brain using the Adaptive Agent pattern.
    Handles ANY user request by dynamically generating code with primitives.
    Includes feedback system and memory.
    """

    def __init__(self):
        self.agent = AdaptiveAgent()

    def _build_feedback_context(self, session: Session, user_id: str) -> str:
        """Build feedback context string for the system prompt"""
        session_fb = session.feedback_history[-5:]
        user_fb = db.get_feedback(user_id, 5)

        all_fb = session_fb + [f for f in user_fb if f not in session_fb]
        recent = all_fb[-5:]

        if not recent:
            return ""

        lines = []
        positive_count = sum(1 for f in recent if f.get("rating") == "positive")
        negative_count = sum(1 for f in recent if f.get("rating") == "negative")

        for fb in recent:
            emoji = "LIKED" if fb.get("rating") == "positive" else "DISLIKED"
            preview = fb.get("answer_preview", "")[:100]
            lines.append(f"- {emoji}: {preview}")
            if fb.get("comment"):
                lines.append(f"  User said: \"{fb['comment']}\"")

        if negative_count >= 2:
            lines.append("\nWARNING: Multiple negative feedbacks. Significantly improve your response quality.")
        elif positive_count >= 3:
            lines.append("\nThe user is satisfied. Maintain this quality level.")

        return "\n".join(lines)

    def _build_memory_context(self, user_id: str) -> str:
        """Build user memory context for the system prompt"""
        memory = db.get_memory(user_id)
        if not memory:
            return ""

        lines = ["USER CONTEXT (from memory):"]
        for key, value in memory.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    async def process(self, session_id: str, user_message: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Process a user message. Non-streaming version.
        Collects all agent events and returns final result.
        """
        session = db.get_session(session_id)
        session.messages.append(Message(role=MessageType.USER, content=user_message))

        # Check if we have a pending confirmation
        if session.pending_confirmation:
            return await self._handle_confirmation(session, user_message, user_id)

        # Build conversation history for agent (last 10 messages)
        history = self._build_history(session)

        # Build feedback and memory context
        feedback_context = self._build_feedback_context(session, user_id)
        memory_context = self._build_memory_context(user_id)

        full_context = ""
        if memory_context:
            full_context = memory_context + "\n\n"
        if feedback_context:
            full_context += feedback_context

        # Run agent and collect all events
        final_answer = ""
        steps = []
        confirm_data = None
        ask_data = None
        options = None

        async for event in self.agent.run(
            user_message, history, user_id, full_context,
            session_id=session_id,
        ):
            steps.append(event.to_dict())

            if event.type == "answer":
                final_answer = event.content
            elif event.type == "ask":
                ask_data = event.data
                final_answer = event.content
            elif event.type == "confirm_needed":
                confirm_data = event.data
                final_answer = event.content

        # Store final answer in session
        if final_answer:
            session.messages.append(Message(role=MessageType.AI, content=final_answer))

        # If asking user to choose options
        if ask_data:
            session.pending_confirmation = {
                "type": "ask",
                "options": ask_data.get("options", []),
                "scratchpad": ask_data.get("scratchpad", []),
                "history": ask_data.get("history", []),
                "context": ask_data.get("context", {}),
            }
            return {
                "message": final_answer,
                "type": "ask",
                "status": "choose",
                "options": ask_data.get("options", []),
                "session_id": session_id,
                "steps": steps,
            }

        # If confirmation needed for risky action
        if confirm_data:
            session.pending_confirmation = confirm_data
            code_preview = confirm_data.get("code") if confirm_data.get("action_type") == "code" else None
            return {
                "message": final_answer,
                "type": "task",
                "status": "confirm",
                "code_preview": code_preview,
                "session_id": session_id,
                "steps": steps,
            }

        return {
            "message": final_answer,
            "type": "answer",
            "session_id": session_id,
            "steps": steps,
        }

    async def process_stream(self, session_id: str, user_message: str, user_id: str = "default"):
        """
        Process a user message. Streaming version.
        Yields AgentEvent objects for SSE streaming.
        """
        session = db.get_session(session_id)
        session.messages.append(Message(role=MessageType.USER, content=user_message))

        # Check for pending confirmation
        if session.pending_confirmation:
            async for event in self._handle_confirmation_stream(session, user_message, user_id):
                yield event
            return

        # Build context
        history = self._build_history(session)
        feedback_context = self._build_feedback_context(session, user_id)
        memory_context = self._build_memory_context(user_id)

        full_context = ""
        if memory_context:
            full_context = memory_context + "\n\n"
        if feedback_context:
            full_context += feedback_context

        final_answer = ""

        async for event in self.agent.run(
            user_message, history, user_id, full_context,
            session_id=session_id,
        ):
            yield event

            if event.type == "answer":
                final_answer = event.content
            elif event.type == "ask":
                session.pending_confirmation = {
                    "type": "ask",
                    "options": event.data.get("options", []),
                    "scratchpad": event.data.get("scratchpad", []),
                    "history": event.data.get("history", []),
                    "context": event.data.get("context", {}),
                }
                final_answer = event.content
            elif event.type == "confirm_needed":
                session.pending_confirmation = event.data
                final_answer = event.content

        if final_answer:
            session.messages.append(Message(role=MessageType.AI, content=final_answer))

    async def _handle_confirmation(self, session: Session, user_message: str, user_id: str) -> Dict[str, Any]:
        """Handle a pending confirmation (user said yes/no or selected an option)"""
        pending = session.pending_confirmation

        # Handle option selection from <ask>
        if pending.get("type") == "ask":
            session.pending_confirmation = None
            # User's selection becomes the next message - run agent again with context
            history = self._build_history(session)
            scratchpad = pending.get("scratchpad", [])
            context = pending.get("context", {})

            # Add the selection to scratchpad as context
            scratchpad.append({
                "role": "user",
                "content": f"<user_selection>{user_message}</user_selection>",
            })

            # Continue the agent from where it left off
            final_answer = ""
            steps = []
            confirm_data = None
            ask_data = None

            # Build context string
            feedback_context = self._build_feedback_context(session, user_id)
            memory_context = self._build_memory_context(user_id)
            full_context = ""
            if memory_context:
                full_context = memory_context + "\n\n"
            if feedback_context:
                full_context += feedback_context

            # Run agent with the selection
            effective_message = f"User selected: {user_message}"
            combined_history = history + scratchpad

            async for event in self.agent.run(
                effective_message, combined_history, user_id, full_context,
                session_id=session.id,
            ):
                steps.append(event.to_dict())
                if event.type == "answer":
                    final_answer = event.content
                elif event.type == "ask":
                    ask_data = event.data
                    final_answer = event.content
                elif event.type == "confirm_needed":
                    confirm_data = event.data
                    final_answer = event.content

            if final_answer:
                session.messages.append(Message(role=MessageType.AI, content=final_answer))

            if ask_data:
                session.pending_confirmation = {
                    "type": "ask",
                    "options": ask_data.get("options", []),
                    "scratchpad": ask_data.get("scratchpad", []),
                    "history": ask_data.get("history", []),
                    "context": ask_data.get("context", {}),
                }
                return {
                    "message": final_answer,
                    "type": "ask",
                    "status": "choose",
                    "options": ask_data.get("options", []),
                    "session_id": session.id,
                    "steps": steps,
                }

            if confirm_data:
                session.pending_confirmation = confirm_data
                return {
                    "message": final_answer,
                    "type": "task",
                    "status": "confirm",
                    "code_preview": confirm_data.get("code"),
                    "session_id": session.id,
                    "steps": steps,
                }

            return {
                "message": final_answer,
                "type": "answer",
                "session_id": session.id,
                "steps": steps,
            }

        # Handle yes/no confirmation for risky actions
        if _is_confirmation(user_message, CONFIRM_YES):
            session.pending_confirmation = None

            action_type = pending.get("action_type", "")
            primitive_name = pending.get("primitive")
            params = pending.get("params", {})
            code = pending.get("code")
            scratchpad = pending.get("scratchpad", [])
            history = pending.get("history", self._build_history(session))
            context = pending.get("context", {})

            final_answer = ""
            steps = []

            async for event in self.agent.execute_confirmed_action(
                action_type, primitive_name, params, code,
                history, scratchpad, context, user_id,
            ):
                steps.append(event.to_dict())
                if event.type == "answer":
                    final_answer = event.content

            if final_answer:
                session.messages.append(Message(role=MessageType.AI, content=final_answer))

            return {
                "message": final_answer,
                "type": "task",
                "status": "done",
                "session_id": session.id,
                "steps": steps,
            }

        elif _is_confirmation(user_message, CONFIRM_NO):
            session.pending_confirmation = None
            msg = "Okay, cancelled."
            session.messages.append(Message(role=MessageType.AI, content=msg))
            return {"message": msg, "type": "cancelled", "session_id": session.id}

        else:
            # User said something else - treat as new message
            session.pending_confirmation = None
            return await self.process(session.id, user_message, user_id)

    async def _handle_confirmation_stream(self, session: Session, user_message: str, user_id: str):
        """Streaming version of confirmation handling"""
        pending = session.pending_confirmation

        # Handle option selection from <ask>
        if pending.get("type") == "ask":
            session.pending_confirmation = None
            history = self._build_history(session)
            scratchpad = pending.get("scratchpad", [])

            scratchpad.append({
                "role": "user",
                "content": f"<user_selection>{user_message}</user_selection>",
            })

            feedback_context = self._build_feedback_context(session, user_id)
            memory_context = self._build_memory_context(user_id)
            full_context = ""
            if memory_context:
                full_context = memory_context + "\n\n"
            if feedback_context:
                full_context += feedback_context

            effective_message = f"User selected: {user_message}"
            combined_history = history + scratchpad
            final_answer = ""

            async for event in self.agent.run(
                effective_message, combined_history, user_id, full_context,
                session_id=session.id,
            ):
                yield event
                if event.type == "answer":
                    final_answer = event.content
                elif event.type == "ask":
                    session.pending_confirmation = {
                        "type": "ask",
                        "options": event.data.get("options", []),
                        "scratchpad": event.data.get("scratchpad", []),
                        "history": event.data.get("history", []),
                        "context": event.data.get("context", {}),
                    }
                    final_answer = event.content
                elif event.type == "confirm_needed":
                    session.pending_confirmation = event.data
                    final_answer = event.content

            if final_answer:
                session.messages.append(Message(role=MessageType.AI, content=final_answer))
            return

        # Handle yes/no confirmation
        if _is_confirmation(user_message, CONFIRM_YES):
            session.pending_confirmation = None

            action_type = pending.get("action_type", "")
            primitive_name = pending.get("primitive")
            params = pending.get("params", {})
            code = pending.get("code")
            scratchpad = pending.get("scratchpad", [])
            history = pending.get("history", self._build_history(session))
            context = pending.get("context", {})

            final_answer = ""
            async for event in self.agent.execute_confirmed_action(
                action_type, primitive_name, params, code,
                history, scratchpad, context, user_id,
            ):
                yield event
                if event.type == "answer":
                    final_answer = event.content

            if final_answer:
                session.messages.append(Message(role=MessageType.AI, content=final_answer))

        elif _is_confirmation(user_message, CONFIRM_NO):
            session.pending_confirmation = None
            msg = "Okay, cancelled."
            session.messages.append(Message(role=MessageType.AI, content=msg))
            yield AgentEvent(type="answer", content=msg)

        else:
            session.pending_confirmation = None
            async for event in self.process_stream(session.id, user_message, user_id):
                yield event

    def _build_history(self, session: Session) -> List[Dict[str, str]]:
        """Build conversation history for the agent (last 10 messages, excluding the latest)"""
        history = []
        for m in session.messages[-11:-1]:
            role = "user" if m.role == MessageType.USER else "assistant"
            history.append({"role": role, "content": m.content})
        return history

    def submit_feedback(self, session_id: str, user_id: str, message_index: int,
                        rating: str, comment: str = None, answer_preview: str = "") -> Dict:
        """Submit user feedback for an AI response"""
        session = db.get_session(session_id)

        feedback = {
            "session_id": session_id,
            "message_index": message_index,
            "rating": rating,
            "comment": comment,
            "answer_preview": answer_preview[:200] if answer_preview else "",
            "timestamp": datetime.now().isoformat(),
        }

        session.feedback_history.append(feedback)
        db.add_feedback(user_id, feedback)

        logger.info(f"Feedback: {rating} from user {user_id[:8]}... session {session_id[:8]}...")

        return {"status": "recorded", "rating": rating}


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================
brain = AIBrain()


# =============================================================================
# PUBLIC API - Functions called by routes/api.py
# =============================================================================
async def chat(session_id: str, message: str, user_id: str = "default") -> Dict[str, Any]:
    """Send a message and get response (non-streaming)"""
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
