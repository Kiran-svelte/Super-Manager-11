"""
Memory Tool - Save/Recall User Data
====================================
Stores user preferences, notes, and data in-memory per user.
No external API needed.
"""

from .base import Tool, ToolResult


# Shared memory store - imported by brain.py
_memory_store: dict = {}


def get_user_memory(user_id: str) -> dict:
    """Get all memory for a user"""
    return _memory_store.get(user_id, {})


def set_user_memory(user_id: str, key: str, value: str):
    """Set a memory value for a user"""
    if user_id not in _memory_store:
        _memory_store[user_id] = {}
    _memory_store[user_id][key] = value


class MemoryTool(Tool):
    name = "memory_store"
    description = "Save or recall user information, preferences, and notes for future reference. Use this to remember names, preferences, addresses, or any data the user shares."
    parameters = {
        "action": {
            "description": "Action: 'save' to store data, 'recall' to retrieve, 'list' to show all saved items",
            "required": True,
            "type": "string",
        },
        "key": {
            "description": "What to remember (e.g. 'user_name', 'favorite_color', 'home_address')",
            "required": True,
            "type": "string",
        },
        "value": {
            "description": "Value to store (only needed for 'save' action)",
            "required": False,
            "type": "string",
        },
    }
    requires_confirmation = False

    async def execute(self, **params) -> ToolResult:
        action = params.get("action", "").lower()
        key = params.get("key", "")
        value = params.get("value", "")
        user_id = params.get("_user_id", "default")

        if action == "save":
            if not key or not value:
                return ToolResult(
                    success=False,
                    output="Both 'key' and 'value' are required for saving.",
                    error="missing_params",
                )
            set_user_memory(user_id, key, value)
            return ToolResult(
                success=True,
                output=f"Saved: {key} = {value}",
                data={"action": "save", "key": key, "value": value},
            )

        elif action == "recall":
            if not key:
                return ToolResult(
                    success=False,
                    output="'key' is required for recall.",
                    error="missing_key",
                )
            memory = get_user_memory(user_id)
            if key in memory:
                return ToolResult(
                    success=True,
                    output=f"{key}: {memory[key]}",
                    data={"action": "recall", "key": key, "value": memory[key]},
                )
            else:
                return ToolResult(
                    success=True,
                    output=f"No saved data for '{key}'.",
                    data={"action": "recall", "key": key, "value": None},
                )

        elif action == "list":
            memory = get_user_memory(user_id)
            if not memory:
                return ToolResult(
                    success=True,
                    output="No saved data yet.",
                    data={"action": "list", "items": {}},
                )
            lines = [f"- {k}: {v}" for k, v in memory.items()]
            return ToolResult(
                success=True,
                output=f"Saved data:\n" + "\n".join(lines),
                data={"action": "list", "items": memory},
            )

        else:
            return ToolResult(
                success=False,
                output=f"Unknown action '{action}'. Use 'save', 'recall', or 'list'.",
                error="invalid_action",
            )
