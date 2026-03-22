"""
Behavioral Tests: Confirmation Manager
=======================================
Tests that the confirmation manager module ACTUALLY works:
- PendingAction class
- ConfirmationManager class
- Approval/rejection workflow

README Requirements:
- User confirmation before actions
- Multi-step action approval
- Action status tracking
"""

import pytest
import uuid

from backend.core.confirmation_manager import (
    PendingAction,
    ConfirmationManager,
)


class TestPendingActionInit:
    """Test PendingAction initialization"""
    
    def test_can_create(self):
        """PendingAction should be creatable"""
        action = PendingAction(
            action_type="send_email",
            description="Send email to test@test.com",
            parameters={"to": "test@test.com"},
            plugin="email"
        )
        assert action is not None
    
    def test_has_id(self):
        """Should auto-generate id"""
        action = PendingAction("type", "desc", {}, "plugin")
        assert action.id is not None
        assert len(action.id) > 0
    
    def test_id_is_uuid(self):
        """id should be valid UUID"""
        action = PendingAction("type", "desc", {}, "plugin")
        # Should not raise exception
        uuid.UUID(action.id)
    
    def test_has_action_type(self):
        """Should have action_type"""
        action = PendingAction("my_action", "desc", {}, "plugin")
        assert action.action_type == "my_action"
    
    def test_has_description(self):
        """Should have description"""
        action = PendingAction("type", "My Description", {}, "plugin")
        assert action.description == "My Description"
    
    def test_has_parameters(self):
        """Should have parameters"""
        action = PendingAction("type", "desc", {"key": "value"}, "plugin")
        assert action.parameters == {"key": "value"}
    
    def test_has_plugin(self):
        """Should have plugin"""
        action = PendingAction("type", "desc", {}, "email")
        assert action.plugin == "email"
    
    def test_default_status_is_pending(self):
        """Default status should be 'pending'"""
        action = PendingAction("type", "desc", {}, "plugin")
        assert action.status == "pending"
    
    def test_has_created_at(self):
        """Should have created_at timestamp"""
        action = PendingAction("type", "desc", {}, "plugin")
        assert action.created_at is not None


class TestPendingActionToDict:
    """Test PendingAction to_dict method"""
    
    def test_has_to_dict_method(self):
        """Should have to_dict method"""
        action = PendingAction("type", "desc", {}, "plugin")
        assert hasattr(action, "to_dict")
        assert callable(action.to_dict)
    
    def test_to_dict_returns_dict(self):
        """to_dict should return dict"""
        action = PendingAction("type", "desc", {}, "plugin")
        result = action.to_dict()
        assert isinstance(result, dict)
    
    def test_to_dict_includes_all_fields(self):
        """to_dict should include all fields"""
        action = PendingAction("send_email", "Send email", {"to": "a@b.com"}, "email")
        result = action.to_dict()
        assert "id" in result
        assert "action_type" in result
        assert "description" in result
        assert "parameters" in result
        assert "plugin" in result
        assert "status" in result
        assert "created_at" in result
        assert result["action_type"] == "send_email"


class TestConfirmationManagerInit:
    """Test ConfirmationManager initialization"""
    
    def test_can_instantiate(self):
        """ConfirmationManager should be instantiatable"""
        manager = ConfirmationManager()
        assert manager is not None
    
    def test_has_pending_actions_dict(self):
        """Should have pending_actions dict"""
        manager = ConfirmationManager()
        assert hasattr(manager, "pending_actions")
        assert isinstance(manager.pending_actions, dict)
    
    def test_has_session_plans_dict(self):
        """Should have session_plans dict"""
        manager = ConfirmationManager()
        assert hasattr(manager, "session_plans")
        assert isinstance(manager.session_plans, dict)
    
    def test_starts_empty(self):
        """Should start with empty dicts"""
        manager = ConfirmationManager()
        assert len(manager.pending_actions) == 0
        assert len(manager.session_plans) == 0


class TestConfirmationManagerCreateRequest:
    """Test ConfirmationManager create_confirmation_request"""
    
    def test_has_create_confirmation_request_method(self):
        """Should have create_confirmation_request method"""
        manager = ConfirmationManager()
        assert hasattr(manager, "create_confirmation_request")
        assert callable(manager.create_confirmation_request)
    
    def test_creates_confirmation_request(self):
        """Should create confirmation request"""
        manager = ConfirmationManager()
        plan = {
            "steps": [
                {"action": "send_email", "parameters": {"to": "test@test.com"}, "plugin": "email"}
            ]
        }
        result = manager.create_confirmation_request("session-1", plan, "Send email to test")
        assert result is not None
        assert isinstance(result, dict)
    
    def test_returns_session_id(self):
        """Result should include session_id"""
        manager = ConfirmationManager()
        plan = {"steps": [{"action": "test", "parameters": {}, "plugin": "test"}]}
        result = manager.create_confirmation_request("my-session", plan, "test")
        assert result["session_id"] == "my-session"
    
    def test_returns_requires_confirmation(self):
        """Result should include requires_confirmation"""
        manager = ConfirmationManager()
        plan = {"steps": [{"action": "test", "parameters": {}, "plugin": "test"}]}
        result = manager.create_confirmation_request("session", plan, "test")
        assert result["requires_confirmation"] is True
    
    def test_returns_actions_list(self):
        """Result should include actions list"""
        manager = ConfirmationManager()
        plan = {"steps": [{"action": "test", "parameters": {}, "plugin": "test"}]}
        result = manager.create_confirmation_request("session", plan, "test")
        assert "actions" in result
        assert isinstance(result["actions"], list)


class TestConfirmationManagerGetPendingActions:
    """Test ConfirmationManager get_pending_actions"""
    
    def test_has_get_pending_actions_method(self):
        """Should have get_pending_actions method"""
        manager = ConfirmationManager()
        assert hasattr(manager, "get_pending_actions")
        assert callable(manager.get_pending_actions)
    
    def test_returns_empty_for_unknown_session(self):
        """Should return empty list for unknown session"""
        manager = ConfirmationManager()
        result = manager.get_pending_actions("unknown-session")
        assert result == []
    
    def test_returns_pending_actions(self):
        """Should return pending actions for session"""
        manager = ConfirmationManager()
        plan = {"steps": [{"action": "test", "parameters": {}, "plugin": "test"}]}
        manager.create_confirmation_request("session-1", plan, "test")
        result = manager.get_pending_actions("session-1")
        assert len(result) == 1


class TestConfirmationManagerApproval:
    """Test ConfirmationManager approval methods"""
    
    def test_has_approve_action_method(self):
        """Should have approve_action method"""
        manager = ConfirmationManager()
        assert hasattr(manager, "approve_action")
        assert callable(manager.approve_action)
    
    def test_has_reject_action_method(self):
        """Should have reject_action method"""
        manager = ConfirmationManager()
        assert hasattr(manager, "reject_action")
        assert callable(manager.reject_action)
    
    def test_has_approve_all_method(self):
        """Should have approve_all method"""
        manager = ConfirmationManager()
        assert hasattr(manager, "approve_all")
        assert callable(manager.approve_all)
    
    def test_has_reject_all_method(self):
        """Should have reject_all method"""
        manager = ConfirmationManager()
        assert hasattr(manager, "reject_all")
        assert callable(manager.reject_all)
    
    def test_approve_action_returns_bool(self):
        """approve_action should return bool"""
        manager = ConfirmationManager()
        result = manager.approve_action("session", "action-id")
        assert isinstance(result, bool)
    
    def test_approve_all_changes_status(self):
        """approve_all should change all action statuses"""
        manager = ConfirmationManager()
        plan = {"steps": [
            {"action": "action1", "parameters": {}, "plugin": "test"},
            {"action": "action2", "parameters": {}, "plugin": "test"}
        ]}
        manager.create_confirmation_request("session-1", plan, "test")
        manager.approve_all("session-1")
        
        actions = manager.pending_actions.get("session-1", [])
        for action in actions:
            assert action.status == "approved"
    
    def test_reject_all_changes_status(self):
        """reject_all should change all action statuses"""
        manager = ConfirmationManager()
        plan = {"steps": [{"action": "test", "parameters": {}, "plugin": "test"}]}
        manager.create_confirmation_request("session-1", plan, "test")
        manager.reject_all("session-1")
        
        actions = manager.pending_actions.get("session-1", [])
        for action in actions:
            assert action.status == "rejected"


class TestConfirmationManagerGetApproved:
    """Test ConfirmationManager get_approved_actions"""
    
    def test_has_get_approved_actions_method(self):
        """Should have get_approved_actions method"""
        manager = ConfirmationManager()
        assert hasattr(manager, "get_approved_actions")
        assert callable(manager.get_approved_actions)
    
    def test_returns_only_approved(self):
        """Should return only approved actions"""
        manager = ConfirmationManager()
        plan = {"steps": [
            {"action": "keep", "parameters": {}, "plugin": "test"},
            {"action": "reject", "parameters": {}, "plugin": "test"}
        ]}
        manager.create_confirmation_request("session-1", plan, "test")
        
        # Approve first, reject second
        actions = manager.pending_actions["session-1"]
        actions[0].status = "approved"
        actions[1].status = "rejected"
        
        approved = manager.get_approved_actions("session-1")
        assert len(approved) == 1
        assert approved[0].action_type == "keep"


class TestConfirmationManagerSessionPlan:
    """Test ConfirmationManager session plan methods"""
    
    def test_has_get_session_plan_method(self):
        """Should have get_session_plan method"""
        manager = ConfirmationManager()
        assert hasattr(manager, "get_session_plan")
        assert callable(manager.get_session_plan)
    
    def test_returns_none_for_unknown(self):
        """Should return None for unknown session"""
        manager = ConfirmationManager()
        result = manager.get_session_plan("unknown")
        assert result is None
    
    def test_returns_stored_plan(self):
        """Should return stored plan"""
        manager = ConfirmationManager()
        plan = {"steps": [{"action": "test", "parameters": {}, "plugin": "test"}]}
        manager.create_confirmation_request("session-1", plan, "original input")
        
        result = manager.get_session_plan("session-1")
        assert result is not None
        assert "plan" in result
        assert "user_input" in result
        assert result["user_input"] == "original input"


class TestConfirmationManagerClearSession:
    """Test ConfirmationManager clear_session"""
    
    def test_has_clear_session_method(self):
        """Should have clear_session method"""
        manager = ConfirmationManager()
        assert hasattr(manager, "clear_session")
        assert callable(manager.clear_session)
    
    def test_clears_pending_actions(self):
        """Should clear pending_actions for session"""
        manager = ConfirmationManager()
        plan = {"steps": [{"action": "test", "parameters": {}, "plugin": "test"}]}
        manager.create_confirmation_request("session-1", plan, "test")
        
        assert "session-1" in manager.pending_actions
        manager.clear_session("session-1")
        assert "session-1" not in manager.pending_actions
    
    def test_clears_session_plans(self):
        """Should clear session_plans for session"""
        manager = ConfirmationManager()
        plan = {"steps": [{"action": "test", "parameters": {}, "plugin": "test"}]}
        manager.create_confirmation_request("session-1", plan, "test")
        
        assert "session-1" in manager.session_plans
        manager.clear_session("session-1")
        assert "session-1" not in manager.session_plans


class TestFriendlyDescriptions:
    """Test friendly description generation"""
    
    def test_zoom_description(self):
        """Should generate friendly Zoom description"""
        manager = ConfirmationManager()
        step = {
            "action": "schedule_meeting",
            "parameters": {"time": "10am", "date": "tomorrow"},
            "plugin": "zoom"
        }
        desc = manager._generate_friendly_description(step)
        assert "Zoom" in desc
        assert "10am" in desc
    
    def test_email_description(self):
        """Should generate friendly email description"""
        manager = ConfirmationManager()
        step = {
            "action": "send",
            "parameters": {"to": "john@test.com", "subject": "Hello"},
            "plugin": "email"
        }
        desc = manager._generate_friendly_description(step)
        assert "email" in desc.lower()
        assert "john@test.com" in desc
