"""
Super Manager Agent System
==========================
A TRUE AI agent that:
- Becomes domain experts (fashion designer, executive assistant, travel agent)
- Takes autonomous action (not just talks)
- Remembers everything (preferences, contacts, history)
- Uses real integrations (Gmail, Calendar, Zoom, Telegram, etc.)

This is NOT a chatbot. This is a digital human that works for you.

Supabase URL: https://hpqmcdygbjdmvxfmvucf.supabase.co
"""

__version__ = "3.0.1"
__author__ = "Super Manager AI"

from .core import Agent, AgentConfig, get_agent
from .memory import Memory, UserProfile, get_memory
from .executor import ActionExecutor, get_executor

__all__ = [
    "Agent",
    "AgentConfig",
    "get_agent",
    "Memory",
    "UserProfile",
    "get_memory",
    "ActionExecutor",
    "get_executor"
]
