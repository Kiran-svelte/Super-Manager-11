"""
Confirmation Manager for User Approval Workflow
Handles multi-step confirmations before executing actions
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

class PendingAction:
    """Represents an action pending user confirmation"""
    def __init__(self, action_type: str, description: str, parameters: Dict[str, Any], plugin: str):
        self.id = str(uuid.uuid4())
        self.action_type = action_type
        self.description = description
        self.parameters = parameters
        self.plugin = plugin
        self.status = "pending"  # pending, approved, rejected
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action_type": self.action_type,
            "description": self.description,
            "parameters": self.parameters,
            "plugin": self.plugin,
            "status": self.status,
            "created_at": self.created_at,
        }

class ConfirmationManager:
    """Manages confirmation workflow for actions"""
    def __init__(self):
        # In production, use Redis or database for persistence
        self.pending_actions: Dict[str, List[PendingAction]] = {}
        self.session_plans: Dict[str, Dict[str, Any]] = {}

    def create_confirmation_request(
        self,
        session_id: str,
        plan: Dict[str, Any],
        user_input: str,
    ) -> Dict[str, Any]:
        """Create a confirmation request from a plan.
        Supports both legacy 'steps' and newer 'actions' keys.
        """
        actions: List[PendingAction] = []
        # Determine source of steps
        plan_steps = plan.get("steps")
        if plan_steps is None:
            plan_steps = plan.get("actions", [])
        for step in plan_steps:
            # Resolve action type (may be under 'action' or 'type')
            action_type = step.get("action") or step.get("type")
            description = self._generate_friendly_description(step)
            parameters = step.get("parameters", {})
            plugin = step.get("plugin", "general")
            actions.append(PendingAction(action_type, description, parameters, plugin))
        # Store pending actions and plan
        self.pending_actions[session_id] = actions
        self.session_plans[session_id] = {
            "plan": plan,
            "user_input": user_input,
            "created_at": datetime.utcnow().isoformat(),
        }
        return {
            "session_id": session_id,
            "requires_confirmation": True,
            "message": self._generate_confirmation_message(actions, user_input),
            "actions": [a.to_dict() for a in actions],
            "total_actions": len(actions),
        }

    def _generate_friendly_description(self, step: Dict[str, Any]) -> str:
        """Generate user-friendly description of an action"""
        action = step.get("action", "")
        params = step.get("parameters", {})
        plugin = step.get("plugin", "")
        if plugin == "zoom":
            meeting_time = params.get("time", "")
            meeting_date = params.get("date", "")
            return f"Schedule a Zoom meeting for {meeting_date} at {meeting_time}"
        elif plugin == "email":
            recipient = params.get("to", "the recipient")
            subject = params.get("subject", "meeting invitation")
            return f"Send email to {recipient} with subject: '{subject}'"
        elif plugin == "whatsapp":
            recipient = params.get("to", "the recipient")
            return f"Send WhatsApp message to {recipient}"
        elif plugin == "calendar":
            event_title = params.get("title", "Event")
            event_time = params.get("time", "")
            return f"Add '{event_title}' to calendar at {event_time}"
        else:
            return action

    def _generate_confirmation_message(self, actions: List[PendingAction], user_input: str) -> str:
        """Generate a human-like confirmation message"""
        from .human_ai import generate_human_confirmation_message
        
        # Convert actions to simple dict format for the generator
        actions_list = [{"description": action.description, "type": action.action_type} for action in actions] if actions else []
        
        return generate_human_confirmation_message(user_input, actions_list)

    def get_pending_actions(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get pending actions for a session"""
        actions = self.pending_actions.get(session_id, [])
        return [a.to_dict() for a in actions]

    def approve_action(self, session_id: str, action_id: str) -> bool:
        """Approve a specific action"""
        for a in self.pending_actions.get(session_id, []):
            if a.id == action_id:
                a.status = "approved"
                return True
        return False

    def reject_action(self, session_id: str, action_id: str) -> bool:
        """Reject a specific action"""
        for a in self.pending_actions.get(session_id, []):
            if a.id == action_id:
                a.status = "rejected"
                return True
        return False

    def approve_all(self, session_id: str) -> bool:
        """Approve all actions in a session"""
        for a in self.pending_actions.get(session_id, []):
            a.status = "approved"
        return True

    def reject_all(self, session_id: str) -> bool:
        """Reject all actions in a session"""
        for a in self.pending_actions.get(session_id, []):
            a.status = "rejected"
        return True

    def get_approved_actions(self, session_id: str) -> List[PendingAction]:
        """Get all approved actions for execution"""
        return [a for a in self.pending_actions.get(session_id, []) if a.status == "approved"]

    def get_session_plan(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the original plan for a session"""
        return self.session_plans.get(session_id)

    def clear_session(self, session_id: str):
        """Clear session data after execution"""
        self.pending_actions.pop(session_id, None)
        self.session_plans.pop(session_id, None)

# Global instance
_confirmation_manager: Optional[ConfirmationManager] = None

def get_confirmation_manager() -> ConfirmationManager:
    """Get or create global confirmation manager instance"""
    global _confirmation_manager
    if _confirmation_manager is None:
        _confirmation_manager = ConfirmationManager()
    return _confirmation_manager
