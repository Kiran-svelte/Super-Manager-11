"""
Super Manager Agent System
==========================
A TRUE AI agent that:
- Has its own digital identity (Gmail account)
- Signs up for services, gets API keys autonomously
- Becomes domain experts (fashion designer, executive assistant, travel agent)
- Takes autonomous action (not just talks)
- Remembers everything (preferences, contacts, history)
- Uses real integrations (Gmail, Calendar, Zoom, Telegram, etc.)
- Tracks task progress in real-time with substeps
- Is responsible, consistent, and accountable

This is NOT a chatbot. This is a digital human that works for you.

Supabase URL: https://hpqmcdygbjdmvxfmvucf.supabase.co
"""

__version__ = "4.0.0"
__author__ = "Super Manager AI"

from .core import Agent, AgentConfig, get_agent
from .memory import Memory, UserProfile, get_memory
from .executor import ActionExecutor, get_executor, AIIdentityExecutor, get_ai_executor
from .orchestrator import TaskOrchestrator, OrchestratedTask, get_orchestrator
from .scheduler import JobScheduler, get_scheduler, start_scheduler, stop_scheduler
from .identity import (
    AIIdentity, 
    AIIdentityManager, 
    get_identity_manager,
    GmailManager,
    ResponsibleAI,
    SensitiveDataHandler
)
from .service_signup import (
    ServiceSignup, 
    ServiceRegistry, 
    get_service_signup,
    CaptchaSolver
)

__all__ = [
    "Agent",
    "AgentConfig",
    "get_agent",
    "Memory",
    "UserProfile",
    "get_memory",
    "ActionExecutor",
    "get_executor",
    "AIIdentityExecutor",
    "get_ai_executor",
    "TaskOrchestrator",
    "OrchestratedTask",
    "get_orchestrator",
    "JobScheduler",
    "get_scheduler",
    "start_scheduler",
    "stop_scheduler",
    # AI Identity
    "AIIdentity",
    "AIIdentityManager",
    "get_identity_manager",
    "GmailManager",
    "ResponsibleAI",
    "SensitiveDataHandler",
    # Service Signup
    "ServiceSignup",
    "ServiceRegistry",
    "get_service_signup",
    "CaptchaSolver"
]
