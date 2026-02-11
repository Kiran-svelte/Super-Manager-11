"""
Reminder Tool - In-Session Reminders
=====================================
Sets short-term reminders that trigger on the user's next message
after the specified delay. Stored in-memory per session.
"""

from datetime import datetime, timedelta

from .base import Tool, ToolResult


# Shared reminder store - keyed by session_id
_reminder_store: dict = {}


def get_due_reminders(session_id: str) -> list:
    """Get and remove any reminders that are due"""
    if session_id not in _reminder_store:
        return []

    now = datetime.now()
    due = []
    remaining = []

    for reminder in _reminder_store[session_id]:
        if now >= reminder["remind_at"]:
            due.append(reminder)
        else:
            remaining.append(reminder)

    _reminder_store[session_id] = remaining
    return due


def add_reminder(session_id: str, message: str, delay_minutes: int):
    """Add a reminder to a session"""
    if session_id not in _reminder_store:
        _reminder_store[session_id] = []

    remind_at = datetime.now() + timedelta(minutes=delay_minutes)
    _reminder_store[session_id].append({
        "message": message,
        "remind_at": remind_at,
        "created_at": datetime.now(),
        "delay_minutes": delay_minutes,
    })


class ReminderTool(Tool):
    name = "set_reminder"
    description = "Set a short-term reminder. The reminder will appear in the conversation after the specified delay (when the user sends their next message after the time is up). Best for reminders within the current session (0-120 minutes)."
    parameters = {
        "message": {
            "description": "What to remind about",
            "required": True,
            "type": "string",
        },
        "delay_minutes": {
            "description": "Minutes from now (0-120). Use 0 for immediate reminder on next message.",
            "required": True,
            "type": "integer",
        },
    }
    requires_confirmation = False

    async def execute(self, **params) -> ToolResult:
        message = params.get("message", "")
        delay_minutes = params.get("delay_minutes", 5)
        session_id = params.get("_session_id", "")

        if not message:
            return ToolResult(
                success=False,
                output="Please specify what to remind about.",
                error="missing_message",
            )

        try:
            delay_minutes = int(delay_minutes)
        except (TypeError, ValueError):
            delay_minutes = 5

        delay_minutes = max(0, min(120, delay_minutes))

        if not session_id:
            return ToolResult(
                success=False,
                output="Session context not available for reminders.",
                error="no_session",
            )

        add_reminder(session_id, message, delay_minutes)
        remind_at = datetime.now() + timedelta(minutes=delay_minutes)

        if delay_minutes == 0:
            time_str = "on your next message"
        elif delay_minutes < 60:
            time_str = f"in {delay_minutes} minute{'s' if delay_minutes != 1 else ''}"
        else:
            hours = delay_minutes // 60
            mins = delay_minutes % 60
            time_str = f"in {hours}h {mins}m" if mins else f"in {hours} hour{'s' if hours != 1 else ''}"

        return ToolResult(
            success=True,
            output=f"Reminder set: '{message}' - will appear {time_str} (at {remind_at.strftime('%I:%M %p')})",
            data={
                "reminder": message,
                "delay_minutes": delay_minutes,
                "remind_at": remind_at.isoformat(),
            },
        )
