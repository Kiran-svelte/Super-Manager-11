"""
Human Fallback - Structured Handoff When Automation Fails
==========================================================
When the agent can't complete a task (CAPTCHA, login wall, anti-bot,
complex forms), it provides structured context for the user to
complete the task manually.

The agent pauses, provides instructions, and resumes after the user
signals completion.
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List

from .primitives import PrimitiveResult

logger = logging.getLogger(__name__)


@dataclass
class FallbackContext:
    """Context provided during human fallback"""
    reason: str                              # "captcha_detected", "login_required", "complex_form", "anti_bot"
    task_description: str                    # What the agent was trying to do
    completed_steps: List[str] = field(default_factory=list)    # What was already done
    remaining_steps: List[str] = field(default_factory=list)    # What the user needs to do
    prefilled_data: Dict[str, Any] = field(default_factory=dict)  # Data the agent collected
    current_url: Optional[str] = None        # URL where it stopped
    screenshot_url: Optional[str] = None     # Screenshot of where it stopped
    resume_data: Dict[str, Any] = field(default_factory=dict)   # Data needed to resume


async def human_fallback(
    reason: str = "automation_blocked",
    task_description: str = "",
    completed_steps: str = "",
    remaining_steps: str = "",
    prefilled_data: str = "",
    current_url: str = "",
) -> PrimitiveResult:
    """
    Trigger a human fallback - pause automation and ask the user to
    complete the remaining steps manually.

    This is called by the agent when it hits a wall (CAPTCHA, login, anti-bot).
    Returns a PrimitiveResult that the agent uses to inform the user.
    """
    # Parse steps from comma-separated strings (LLM-friendly format)
    completed = [s.strip() for s in completed_steps.split(",") if s.strip()] if completed_steps else []
    remaining = [s.strip() for s in remaining_steps.split(",") if s.strip()] if remaining_steps else []

    # Parse prefilled data from key=value format
    prefilled: Dict[str, str] = {}
    if prefilled_data:
        for pair in prefilled_data.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                prefilled[k.strip()] = v.strip()

    reason_labels = {
        "captcha_detected": "CAPTCHA Detected",
        "login_required": "Login Required",
        "anti_bot": "Anti-Bot Protection",
        "complex_form": "Complex Form",
        "two_factor": "Two-Factor Authentication",
        "automation_blocked": "Automation Blocked",
    }

    reason_label = reason_labels.get(reason, reason.replace("_", " ").title())

    context = FallbackContext(
        reason=reason,
        task_description=task_description,
        completed_steps=completed,
        remaining_steps=remaining,
        prefilled_data=prefilled,
        current_url=current_url,
    )

    output_lines = [
        f"MANUAL ACTION REQUIRED: {reason_label}",
        f"",
        f"Task: {task_description}",
    ]

    if completed:
        output_lines.append(f"\nCompleted steps:")
        for i, step in enumerate(completed, 1):
            output_lines.append(f"  {i}. {step}")

    if remaining:
        output_lines.append(f"\nPlease complete these steps manually:")
        for i, step in enumerate(remaining, 1):
            output_lines.append(f"  {i}. {step}")

    if prefilled:
        output_lines.append(f"\nPre-filled data you can use:")
        for k, v in prefilled.items():
            output_lines.append(f"  {k}: {v}")

    if current_url:
        output_lines.append(f"\nCurrent URL: {current_url}")

    output_lines.append(f"\nPlease complete the steps above and let me know when you're done.")

    return PrimitiveResult(
        success=True,
        output="\n".join(output_lines),
        data={
            "type": "human_fallback",
            "context": asdict(context),
        },
    )


def register_fallback_tools():
    """Register human fallback tools with the ToolRegistry"""
    try:
        from .tool_registry import get_tool_registry, ToolDef

        registry = get_tool_registry()
        registry.register(ToolDef(
            name="human_fallback",
            description="Pause automation and ask the user to complete remaining steps manually (use when blocked by CAPTCHA, login, anti-bot, etc.)",
            parameters='reason (str), task_description (str), completed_steps (str, comma-separated), remaining_steps (str, comma-separated), prefilled_data (str, key=value pairs), current_url (str)',
            returns="Structured handoff message for the user with instructions and pre-filled data",
            risk_level="safe",
            source="fallback",
            handler=human_fallback,
        ))
        logger.info("[HUMAN_FALLBACK] Registered human_fallback tool")
    except Exception as e:
        logger.warning(f"[HUMAN_FALLBACK] Failed to register: {e}")
