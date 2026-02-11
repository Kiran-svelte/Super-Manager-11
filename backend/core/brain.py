"""
SUPER MANAGER - AI BRAIN v3 (ReAct Agent)
==========================================
General-purpose AI agent that can handle ANY request.
Uses ReAct (Reasoning + Acting) pattern with Groq LLM.

Architecture:
- ReactAgent: Think → Act → Observe loop
- ToolRegistry: Pluggable tools (search, browse, email, image, meeting, payment, python)
- Session management: Conversation history + pending confirmations
- SSE streaming: Real-time progress events
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

# Import the ReAct agent and tools
from .react_agent import ReactAgent, AgentEvent, PendingConfirmation
from .tools import ToolRegistry


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
    pending_confirmation: Optional[Dict[str, Any]] = None  # Tool awaiting "yes"


# =============================================================================
# DATABASE - In-Memory Session Store
# =============================================================================
class Database:
    """Session storage - replace with Supabase/PostgreSQL in production"""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.users: Dict[str, Dict] = {}

    def get_session(self, session_id: str) -> Session:
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(id=session_id)
        return self.sessions[session_id]

    def save_user(self, identifier: str, data: Dict):
        self.users[identifier] = {**self.users.get(identifier, {}), **data}

    def get_user(self, identifier: str) -> Optional[Dict]:
        return self.users.get(identifier)


db = Database()


# =============================================================================
# AI BRAIN - ReAct Agent Wrapper
# =============================================================================
class AIBrain:
    """
    General-purpose AI brain using the ReAct agent pattern.
    Can handle ANY user request by dynamically choosing tools.
    """

    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.agent = ReactAgent(self.tool_registry)

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

        # Run agent and collect all events
        final_answer = ""
        ui_components = None
        proof = None
        steps = []
        confirm_data = None

        async for event in self.agent.run(user_message, history, user_id):
            steps.append(event.to_dict())

            if event.type == "answer":
                final_answer = event.content
            elif event.type == "tool_result" and event.data:
                # Collect UI components from tool results
                if "ui_components" in event.data:
                    ui_components = event.data["ui_components"]
                if "proof" in event.data:
                    proof = event.data["proof"]
            elif event.type == "confirm_needed":
                confirm_data = event.data
                final_answer = event.content

        # Store final answer in session
        if final_answer:
            session.messages.append(Message(role=MessageType.AI, content=final_answer))

        # If confirmation needed, store pending state
        if confirm_data:
            session.pending_confirmation = confirm_data
            return {
                "message": final_answer,
                "type": "task",
                "status": "confirm",
                "session_id": session_id,
                "steps": steps,
            }

        return {
            "message": final_answer,
            "type": "answer",
            "session_id": session_id,
            "ui_components": ui_components,
            "proof": proof,
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

        history = self._build_history(session)
        final_answer = ""

        async for event in self.agent.run(user_message, history, user_id):
            yield event

            if event.type == "answer":
                final_answer = event.content
            elif event.type == "confirm_needed":
                session.pending_confirmation = event.data
                final_answer = event.content

        if final_answer:
            session.messages.append(Message(role=MessageType.AI, content=final_answer))

    async def _handle_confirmation(self, session: Session, user_message: str, user_id: str) -> Dict[str, Any]:
        """Handle a pending confirmation (user said yes/no)"""
        pending = session.pending_confirmation
        lower = user_message.lower().strip()

        # Check for confirmation
        if any(word in lower for word in ["yes", "confirm", "do it", "go ahead", "ok", "sure", "send", "pay"]):
            session.pending_confirmation = None

            tool_name = pending.get("tool", "")
            tool_params = pending.get("params", {})
            scratchpad = pending.get("scratchpad", [])
            history = pending.get("history", self._build_history(session))

            # Execute the confirmed tool
            final_answer = ""
            ui_components = None
            steps = []

            async for event in self.agent.execute_confirmed_tool(
                tool_name, tool_params, history, scratchpad, user_id
            ):
                steps.append(event.to_dict())
                if event.type == "answer":
                    final_answer = event.content
                elif event.type == "tool_result" and event.data:
                    if "ui_components" in event.data:
                        ui_components = event.data["ui_components"]

            session.messages.append(Message(role=MessageType.AI, content=final_answer))

            return {
                "message": final_answer,
                "type": "task",
                "status": "done",
                "session_id": session.id,
                "ui_components": ui_components,
                "steps": steps,
            }

        elif any(word in lower for word in ["no", "cancel", "don't", "stop", "nevermind"]):
            session.pending_confirmation = None
            msg = "Okay, cancelled."
            session.messages.append(Message(role=MessageType.AI, content=msg))
            return {"message": msg, "type": "cancelled", "session_id": session.id}

        else:
            # User said something else while we were waiting for confirmation
            # Process as a new message (clear pending)
            session.pending_confirmation = None
            return await self.process(session.id, user_message, user_id)

    async def _handle_confirmation_stream(self, session: Session, user_message: str, user_id: str):
        """Streaming version of confirmation handling"""
        pending = session.pending_confirmation
        lower = user_message.lower().strip()

        if any(word in lower for word in ["yes", "confirm", "do it", "go ahead", "ok", "sure", "send", "pay"]):
            session.pending_confirmation = None

            tool_name = pending.get("tool", "")
            tool_params = pending.get("params", {})
            scratchpad = pending.get("scratchpad", [])
            history = pending.get("history", self._build_history(session))

            final_answer = ""
            async for event in self.agent.execute_confirmed_tool(
                tool_name, tool_params, history, scratchpad, user_id
            ):
                yield event
                if event.type == "answer":
                    final_answer = event.content

            if final_answer:
                session.messages.append(Message(role=MessageType.AI, content=final_answer))

        elif any(word in lower for word in ["no", "cancel", "don't", "stop", "nevermind"]):
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
        for m in session.messages[-11:-1]:  # Last 10 messages before the current one
            role = "user" if m.role == MessageType.USER else "assistant"
            history.append({"role": role, "content": m.content})
        return history


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
