"""
Meeting Tool - Jitsi
=====================
Create video meeting links using Jitsi.
Free, no API key or signup needed.
"""

import secrets

from .base import Tool, ToolResult


class CreateMeetingTool(Tool):
    name = "create_meeting"
    description = "Create a free video meeting link (Jitsi)"
    parameters = {
        "title": {"description": "Meeting title/topic", "required": True, "type": "string"},
    }
    requires_confirmation = False

    async def execute(self, **params) -> ToolResult:
        title = params.get("title", "Meeting")

        if not title:
            title = "Meeting"

        # Generate unique meeting ID
        meeting_id = f"supermanager-{secrets.token_hex(8)}"
        link = f"https://meet.jit.si/{meeting_id}"

        return ToolResult(
            success=True,
            output=f"Meeting '{title}' created!\nJoin link: {link}\n\nAnyone with this link can join. No account needed.",
            data={
                "meeting_link": link,
                "meeting_id": meeting_id,
                "title": title,
                "platform": "jitsi",
                "ui_components": {
                    "type": "button_group",
                    "buttons": [
                        {
                            "id": "join_meeting",
                            "label": f"Join: {title}",
                            "url": link,
                            "style": "primary",
                        }
                    ],
                },
            },
        )
