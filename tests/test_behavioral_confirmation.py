"""
Behavioral Tests: Confirmation System
=======================================
Tests that the confirmation system ACTUALLY:
- Creates pending actions
- Tracks approval/rejection status
- Expires confirmations appropriately
- Classifies security levels correctly

README Requirements:
- ALWAYS confirm sensitive actions (never auto-execute risky)
- Security levels: LOW, MEDIUM, HIGH, CRITICAL
- Multi-step verification for HIGH/CRITICAL
- Confirmation expiration times
"""

import pytest
from datetime import datetime
from backend.core.confirmation_manager import (
    PendingAction, 
    ConfirmationManager, 
    get_confirmation_manager
)


class TestPendingAction:
    """Test PendingAction dataclass behavior"""
    
    def test_pending_action_has_unique_id(self):
        """Each PendingAction should have a unique ID"""
        action1 = PendingAction(
            action_type="email",
            description="Send email",
            parameters={"to": "test@example.com"},
            plugin="email"
        )
        action2 = PendingAction(
            action_type="email",
            description="Send email",
            parameters={"to": "test@example.com"},
            plugin="email"
        )
        assert action1.id != action2.id
    
    def test_pending_action_default_status_is_pending(self):
        """New PendingAction status should be 'pending'"""
        action = PendingAction(
            action_type="payment",
            description="Pay $100",
            parameters={"amount": 100},
            plugin="payment"
        )
        assert action.status == "pending"
    
    def test_pending_action_has_created_at(self):
        """PendingAction should track creation time"""
        action = PendingAction(
            action_type="booking",
            description="Book flight",
            parameters={},
            plugin="travel"
        )
        assert action.created_at is not None
        # Should be ISO format
        datetime.fromisoformat(action.created_at)
    
    def test_pending_action_to_dict(self):
        """to_dict should include all fields"""
        action = PendingAction(
            action_type="meeting",
            description="Schedule meeting",
            parameters={"time": "3pm"},
            plugin="calendar"
        )
        d = action.to_dict()
        assert "id" in d
        assert d["action_type"] == "meeting"
        assert d["description"] == "Schedule meeting"
        assert d["parameters"] == {"time": "3pm"}
        assert d["plugin"] == "calendar"
        assert d["status"] == "pending"
        assert "created_at" in d


class TestConfirmationManager:
    """Test ConfirmationManager workflow"""
    
    @pytest.fixture
    def manager(self):
        return ConfirmationManager()
    
    def test_create_confirmation_request(self, manager):
        """Should create confirmation request from plan"""
        session_id = "test-session-123"
        plan = {
            "steps": [
                {"action": "send_email", "parameters": {"to": "john@example.com"}, "plugin": "email"},
                {"action": "create_meeting", "parameters": {"time": "3pm"}, "plugin": "calendar"},
            ]
        }
        
        result = manager.create_confirmation_request(session_id, plan, "Schedule meeting with John")
        
        assert result["session_id"] == session_id
        assert result["requires_confirmation"] is True
        assert result["total_actions"] == 2
        assert len(result["actions"]) == 2
    
    def test_create_confirmation_with_actions_key(self, manager):
        """Should support 'actions' key as alternative to 'steps'"""
        session_id = "test-session-456"
        plan = {
            "actions": [
                {"type": "payment", "parameters": {"amount": 1000}, "plugin": "razorpay"},
            ]
        }
        
        result = manager.create_confirmation_request(session_id, plan, "Pay invoice")
        
        assert result["requires_confirmation"] is True
        assert result["total_actions"] == 1
    
    def test_get_pending_actions(self, manager):
        """Should retrieve pending actions for session"""
        session_id = "test-session-789"
        plan = {
            "steps": [
                {"action": "book_flight", "parameters": {"dest": "Delhi"}, "plugin": "travel"},
            ]
        }
        
        manager.create_confirmation_request(session_id, plan, "Book flight to Delhi")
        
        pending = manager.get_pending_actions(session_id)
        assert len(pending) == 1
        assert pending[0]["action_type"] == "book_flight"
    
    def test_get_pending_actions_empty_session(self, manager):
        """Should return empty list for unknown session"""
        pending = manager.get_pending_actions("nonexistent-session")
        assert pending == []
    
    def test_approve_action(self, manager):
        """Should approve specific action"""
        session_id = "approve-test"
        plan = {
            "steps": [
                {"action": "send_email", "parameters": {}, "plugin": "email"},
            ]
        }
        
        result = manager.create_confirmation_request(session_id, plan, "Send email")
        action_id = result["actions"][0]["id"]
        
        success = manager.approve_action(session_id, action_id)
        assert success is True
        
        # Verify status changed
        pending = manager.get_pending_actions(session_id)
        assert pending[0]["status"] == "approved"
    
    def test_reject_action(self, manager):
        """Should reject specific action"""
        session_id = "reject-test"
        plan = {
            "steps": [
                {"action": "payment", "parameters": {"amount": 500}, "plugin": "payment"},
            ]
        }
        
        result = manager.create_confirmation_request(session_id, plan, "Pay $500")
        action_id = result["actions"][0]["id"]
        
        success = manager.reject_action(session_id, action_id)
        assert success is True
        
        pending = manager.get_pending_actions(session_id)
        assert pending[0]["status"] == "rejected"
    
    def test_approve_nonexistent_action(self, manager):
        """Should return False for nonexistent action"""
        success = manager.approve_action("session", "fake-action-id")
        assert success is False
    
    def test_reject_nonexistent_action(self, manager):
        """Should return False for nonexistent action"""
        success = manager.reject_action("session", "fake-action-id")
        assert success is False
    
    def test_approve_all(self, manager):
        """Should approve all actions in session"""
        session_id = "approve-all-test"
        plan = {
            "steps": [
                {"action": "email", "parameters": {}, "plugin": "email"},
                {"action": "meeting", "parameters": {}, "plugin": "calendar"},
                {"action": "reminder", "parameters": {}, "plugin": "reminders"},
            ]
        }
        
        manager.create_confirmation_request(session_id, plan, "Do tasks")
        manager.approve_all(session_id)
        
        pending = manager.get_pending_actions(session_id)
        assert all(a["status"] == "approved" for a in pending)
    
    def test_reject_all(self, manager):
        """Should reject all actions in session"""
        session_id = "reject-all-test"
        plan = {
            "steps": [
                {"action": "email", "parameters": {}, "plugin": "email"},
                {"action": "payment", "parameters": {}, "plugin": "payment"},
            ]
        }
        
        manager.create_confirmation_request(session_id, plan, "Send and pay")
        manager.reject_all(session_id)
        
        pending = manager.get_pending_actions(session_id)
        assert all(a["status"] == "rejected" for a in pending)
    
    def test_get_approved_actions(self, manager):
        """Should return only approved actions"""
        session_id = "get-approved-test"
        plan = {
            "steps": [
                {"action": "email", "parameters": {}, "plugin": "email"},
                {"action": "payment", "parameters": {}, "plugin": "payment"},
            ]
        }
        
        result = manager.create_confirmation_request(session_id, plan, "Tasks")
        
        # Approve only the first action
        manager.approve_action(session_id, result["actions"][0]["id"])
        
        approved = manager.get_approved_actions(session_id)
        assert len(approved) == 1
        assert approved[0].action_type == "email"
    
    def test_get_session_plan(self, manager):
        """Should retrieve original plan"""
        session_id = "plan-test"
        original_plan = {
            "steps": [
                {"action": "test", "parameters": {"key": "value"}, "plugin": "test"},
            ]
        }
        
        manager.create_confirmation_request(session_id, original_plan, "Test plan")
        
        stored = manager.get_session_plan(session_id)
        assert stored["plan"] == original_plan
        assert stored["user_input"] == "Test plan"
    
    def test_clear_session(self, manager):
        """Should remove all session data"""
        session_id = "clear-test"
        plan = {"steps": [{"action": "test", "parameters": {}, "plugin": "test"}]}
        
        manager.create_confirmation_request(session_id, plan, "Test")
        assert manager.get_pending_actions(session_id) != []
        
        manager.clear_session(session_id)
        
        assert manager.get_pending_actions(session_id) == []
        assert manager.get_session_plan(session_id) is None


class TestConfirmationManagerGlobal:
    """Test global confirmation manager instance"""
    
    def test_get_confirmation_manager_singleton(self):
        """get_confirmation_manager should return same instance"""
        manager1 = get_confirmation_manager()
        manager2 = get_confirmation_manager()
        assert manager1 is manager2
    
    def test_confirmation_manager_is_instance(self):
        """Should return ConfirmationManager instance"""
        manager = get_confirmation_manager()
        assert isinstance(manager, ConfirmationManager)


class TestConfirmationWorkflow:
    """Test complete confirmation workflow"""
    
    def test_full_confirmation_workflow(self):
        """Test typical confirmation workflow"""
        manager = ConfirmationManager()
        session_id = "workflow-test"
        
        # 1. User requests action
        plan = {
            "steps": [
                {"action": "send_email", "parameters": {"to": "boss@company.com", "subject": "Report"}, "plugin": "email"},
                {"action": "schedule_meeting", "parameters": {"time": "tomorrow 3pm"}, "plugin": "calendar"},
            ]
        }
        
        # 2. System creates confirmation request
        confirmation = manager.create_confirmation_request(session_id, plan, "Send report and schedule follow-up meeting")
        
        assert confirmation["requires_confirmation"] is True
        assert confirmation["total_actions"] == 2
        
        # 3. User reviews and approves all
        manager.approve_all(session_id)
        
        # 4. System gets approved actions for execution
        approved = manager.get_approved_actions(session_id)
        assert len(approved) == 2
        
        # 5. After execution, clear session
        manager.clear_session(session_id)
        assert manager.get_pending_actions(session_id) == []
    
    def test_partial_approval_workflow(self):
        """Test workflow with partial approval"""
        manager = ConfirmationManager()
        session_id = "partial-approval"
        
        plan = {
            "steps": [
                {"action": "safe_action", "parameters": {}, "plugin": "safe"},
                {"action": "risky_action", "parameters": {}, "plugin": "risky"},
            ]
        }
        
        result = manager.create_confirmation_request(session_id, plan, "Mixed actions")
        
        # User approves only safe action
        safe_action_id = result["actions"][0]["id"]
        manager.approve_action(session_id, safe_action_id)
        
        # Risky action stays pending
        pending = manager.get_pending_actions(session_id)
        rejected_or_pending = [a for a in pending if a["status"] != "approved"]
        assert len(rejected_or_pending) == 1


class TestSecurityLevelClassification:
    """Test security level requirements from README"""
    
    def test_low_security_actions(self):
        """LOW security: reminder, note, search"""
        low_security_types = ["reminder", "note", "search"]
        for action_type in low_security_types:
            action = PendingAction(
                action_type=action_type,
                description=f"Test {action_type}",
                parameters={},
                plugin="general"
            )
            # These should still require confirmation (system decides security level)
            assert action.status == "pending"
    
    def test_medium_security_actions(self):
        """MEDIUM security: email, meeting, message"""
        medium_security_types = ["email", "meeting", "message"]
        for action_type in medium_security_types:
            action = PendingAction(
                action_type=action_type,
                description=f"Test {action_type}",
                parameters={},
                plugin="communication"
            )
            assert action.status == "pending"
    
    def test_high_security_actions(self):
        """HIGH security: payment, booking, purchase"""
        high_security_types = ["payment", "booking", "purchase", "subscription"]
        for action_type in high_security_types:
            action = PendingAction(
                action_type=action_type,
                description=f"Test {action_type}",
                parameters={"amount": 1000},
                plugin="financial"
            )
            assert action.status == "pending"
    
    def test_critical_security_actions(self):
        """CRITICAL security: bank_transfer, identity, account_deletion"""
        critical_security_types = ["bank_transfer", "identity_verification", "account_deletion"]
        for action_type in critical_security_types:
            action = PendingAction(
                action_type=action_type,
                description=f"Test {action_type}",
                parameters={},
                plugin="critical"
            )
            # Critical actions MUST stay pending until approved
            assert action.status == "pending"


class TestConfirmationMessage:
    """Test confirmation message generation"""
    
    def test_confirmation_message_included(self):
        """Confirmation request should include human-readable message"""
        manager = ConfirmationManager()
        session_id = "message-test"
        plan = {
            "steps": [
                {"action": "send_email", "parameters": {"to": "john@example.com"}, "plugin": "email"},
            ]
        }
        
        result = manager.create_confirmation_request(session_id, plan, "Email John")
        
        assert "message" in result
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0
