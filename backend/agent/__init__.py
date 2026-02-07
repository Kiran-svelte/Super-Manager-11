"""
Super Manager Agent System
==========================
A TRUE AI agent that:
- Becomes domain experts (fashion designer, executive assistant, travel agent)
- Takes autonomous action (not just talks)
- Remembers everything (preferences, contacts, history)
- Uses real integrations (Gmail, Calendar, Zoom, Telegram, etc.)

This is NOT a chatbot. This is a digital human that works for you.
"""

__version__ = "3.0.0"
__author__ = "Super Manager AI"

from .core import Agent, AgentConfig
from .memory import Memory, UserProfile
from .executor import ActionExecutor

__all__ = [
    "Agent",
    "AgentConfig", 
    "Memory",
    "UserProfile",
    "ActionExecutor"
]
