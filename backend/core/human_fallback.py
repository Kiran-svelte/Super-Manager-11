"""
Human Fallback System
======================
v6 NEW - Pause agent execution for manual human intervention.

Use Cases:
- CAPTCHA detected
- Login required
- Complex forms
- Multi-factor authentication
- File uploads
- Any task that requires human judgment

Registers with ToolRegistry as "human_fallback" (safe - it's just a pause).
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List

from .primitives import PrimitiveResult

logger = logging.getLogger(__name__)


@dataclass
class FallbackContext:
    """
    Context for a human fallback request.
    Contains all information needed for user to complete the task manually.
    """
    reason: str  # "captcha_detected", "login_required", "complex_form", "file_upload", "mfa_required"
    task_description: str  # What the agent was trying to do
    completed_steps: List[str] = field(default_factory=list)  # What's already done
    remaining_steps: List[str] = field(default_factory=list)  # What needs manual completion
    prefilled_data: Dict[str, Any] = field(default_factory=dict)  # Form data to pre-fill
    screenshot_url: Optional[str] = None  # Optional screenshot for reference
    resume_data: Dict[str, Any] = field(default_factory=dict)  # Data to resume agent after completion
    url: Optional[str] = None  # URL where manual action is needed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization"""
        return asdict(self)


async def trigger_fallback(
    reason: str,
    task_description: str,
    remaining_steps: List[str],
    completed_steps: Optional[List[str]] = None,
    prefilled_data: Optional[Dict[str, Any]] = None,
    screenshot_url: Optional[str] = None,
    url: Optional[str] = None,
    resume_data: Optional[Dict[str, Any]] = None,
) -> PrimitiveResult:
    """
    Trigger a human fallback request.
    
    This function returns a PrimitiveResult that the agent interprets as a
    human_fallback event, pausing execution and showing a manual steps UI.
    
    Args:
        reason: Why human intervention is needed
        task_description: What the agent was trying to accomplish
        remaining_steps: List of steps user needs to complete manually
        completed_steps: List of steps already completed
        prefilled_data: Data that can be pre-filled (e.g., form values)
        screenshot_url: Optional screenshot showing the current state
        url: URL where manual action is needed
        resume_data: Data to resume agent after user completes steps
    
    Returns:
        PrimitiveResult that triggers human_fallback event
    """
    context = FallbackContext(
        reason=reason,
        task_description=task_description,
        completed_steps=completed_steps or [],
        remaining_steps=remaining_steps,
        prefilled_data=prefilled_data or {},
        screenshot_url=screenshot_url,
        url=url,
        resume_data=resume_data or {},
    )
    
    # Format output message
    output_lines = [
        f"⚠️ Manual intervention required: {reason}",
        "",
        f"Task: {task_description}",
        "",
    ]
    
    if context.completed_steps:
        output_lines.append("✅ Completed:")
        for step in context.completed_steps:
            output_lines.append(f"  - {step}")
        output_lines.append("")
    
    output_lines.append("📋 Please complete these steps manually:")
    for i, step in enumerate(remaining_steps, 1):
        output_lines.append(f"  {i}. {step}")
    
    if context.url:
        output_lines.append("")
        output_lines.append(f"🔗 URL: {context.url}")
    
    if context.prefilled_data:
        output_lines.append("")
        output_lines.append("📝 Prefilled data available:")
        for key, value in context.prefilled_data.items():
            output_lines.append(f"  - {key}: {value}")
    
    output_lines.append("")
    output_lines.append("Once you've completed these steps, click 'I've completed these steps' to resume.")
    
    output = "\n".join(output_lines)
    
    logger.info(f"Human fallback triggered: {reason}")
    
    return PrimitiveResult(
        success=False,  # Marked as false to pause execution
        output=output,
        error="human_fallback_required",
        data={
            "fallback_context": context.to_dict(),
            "event_type": "human_fallback",  # Special marker for agent
        },
    )


async def human_fallback_tool(
    reason: str,
    remaining_steps: List[str],
    task_description: str = "Complete manual steps",
    prefilled_data: Optional[Dict[str, Any]] = None,
    url: Optional[str] = None,
) -> PrimitiveResult:
    """
    Tool function for human_fallback (registered with ToolRegistry).
    
    Simplified interface for the agent to call.
    
    Args:
        reason: Why human intervention is needed
        remaining_steps: Steps user needs to complete
        task_description: What task is being attempted
        prefilled_data: Optional pre-filled data
        url: Optional URL where action is needed
    
    Returns:
        PrimitiveResult that triggers human_fallback event
    """
    return await trigger_fallback(
        reason=reason,
        task_description=task_description,
        remaining_steps=remaining_steps,
        prefilled_data=prefilled_data,
        url=url,
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_captcha_fallback(
    url: str,
    captcha_type: str,
    task_description: str,
    completed_steps: Optional[List[str]] = None,
) -> PrimitiveResult:
    """
    Create a fallback context for CAPTCHA scenarios.
    
    Args:
        url: URL with CAPTCHA
        captcha_type: Type of CAPTCHA (recaptcha_v2, hcaptcha, cloudflare, etc.)
        task_description: What task was being attempted
        completed_steps: Steps completed before CAPTCHA
    
    Returns:
        PrimitiveResult for human_fallback
    """
    import asyncio
    
    remaining_steps = [
        f"Open {url} in your browser",
        f"Solve the {captcha_type} CAPTCHA",
        "Complete the form or action you were attempting",
        "Return here and confirm completion",
    ]
    
    return asyncio.run(trigger_fallback(
        reason="captcha_detected",
        task_description=task_description,
        remaining_steps=remaining_steps,
        completed_steps=completed_steps or [],
        url=url,
    ))


def create_login_fallback(
    url: str,
    service_name: str,
    task_description: str,
) -> PrimitiveResult:
    """
    Create a fallback context for login scenarios.
    
    Args:
        url: Login URL
        service_name: Name of service requiring login
        task_description: What task requires login
    
    Returns:
        PrimitiveResult for human_fallback
    """
    import asyncio
    
    remaining_steps = [
        f"Open {url} in your browser",
        f"Log in to {service_name}",
        "Complete your task on the website",
        "Return here and confirm completion",
    ]
    
    return asyncio.run(trigger_fallback(
        reason="login_required",
        task_description=task_description,
        remaining_steps=remaining_steps,
        url=url,
    ))


def create_mfa_fallback(
    url: str,
    service_name: str,
    mfa_method: str = "2FA code",
) -> PrimitiveResult:
    """
    Create a fallback context for multi-factor authentication.
    
    Args:
        url: URL requiring MFA
        service_name: Name of service
        mfa_method: Type of MFA (2FA code, authenticator, SMS, etc.)
    
    Returns:
        PrimitiveResult for human_fallback
    """
    import asyncio
    
    remaining_steps = [
        f"Open {url} in your browser",
        f"Enter your {mfa_method} for {service_name}",
        "Complete the verification process",
        "Return here and confirm completion",
    ]
    
    return asyncio.run(trigger_fallback(
        reason="mfa_required",
        task_description=f"Complete {mfa_method} verification for {service_name}",
        remaining_steps=remaining_steps,
        url=url,
    ))


# =============================================================================
# TOOL REGISTRATION
# =============================================================================

def register_fallback_tool():
    """
    Register human_fallback tool with ToolRegistry.
    Should be called on application startup.
    """
    try:
        from .tool_registry import get_tool_registry, ToolDef
        
        registry = get_tool_registry()
        
        tool = ToolDef(
            name="human_fallback",
            description="Pause execution and request human intervention for manual steps",
            parameters={
                "reason": {"type": "string", "description": "Why human intervention is needed"},
                "remaining_steps": {"type": "array", "description": "Steps user needs to complete"},
                "task_description": {"type": "string", "description": "What task is being attempted"},
                "prefilled_data": {"type": "object", "description": "Optional pre-filled data"},
                "url": {"type": "string", "description": "Optional URL where action is needed"},
            },
            risk_level="safe",  # It's just a pause, not an action
            source="fallback",
            handler=human_fallback_tool,
        )
        
        registry.register(tool)
        logger.info("Registered human_fallback tool")
    
    except Exception as e:
        logger.error(f"Failed to register fallback tool: {e}")
