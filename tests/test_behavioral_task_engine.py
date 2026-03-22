"""
Behavioral Tests: Task Engine
==============================
Tests that the task engine ACTUALLY works:
- TaskCategory enum
- TaskStatus enum
- SecurityLevel enum
- TaskContext dataclass
- TaskRequirement dataclass
- InteractiveOption dataclass
- TaskStep dataclass
- TaskExecution dataclass
- IntentParser

README Requirements:
- Task execution
- Multi-step workflows
- Security levels
"""

import pytest
from dataclasses import is_dataclass
from datetime import datetime

from backend.core.task_engine import (
    TaskCategory,
    TaskStatus,
    SecurityLevel,
    TaskContext,
    TaskRequirement,
    InteractiveOption,
    TaskStep,
    TaskExecution,
    IntentParser,
)


class TestTaskCategoryEnum:
    """Test TaskCategory enum"""
    
    def test_has_booking(self):
        """Should have BOOKING category"""
        assert hasattr(TaskCategory, "BOOKING")
        assert TaskCategory.BOOKING.value == "booking"
    
    def test_has_payment(self):
        """Should have PAYMENT category"""
        assert hasattr(TaskCategory, "PAYMENT")
        assert TaskCategory.PAYMENT.value == "payment"
    
    def test_has_communication(self):
        """Should have COMMUNICATION category"""
        assert hasattr(TaskCategory, "COMMUNICATION")
        assert TaskCategory.COMMUNICATION.value == "communication"
    
    def test_has_scheduling(self):
        """Should have SCHEDULING category"""
        assert hasattr(TaskCategory, "SCHEDULING")
        assert TaskCategory.SCHEDULING.value == "scheduling"
    
    def test_has_creative(self):
        """Should have CREATIVE category"""
        assert hasattr(TaskCategory, "CREATIVE")
        assert TaskCategory.CREATIVE.value == "creative"
    
    def test_has_research(self):
        """Should have RESEARCH category"""
        assert hasattr(TaskCategory, "RESEARCH")
        assert TaskCategory.RESEARCH.value == "research"
    
    def test_has_automation(self):
        """Should have AUTOMATION category"""
        assert hasattr(TaskCategory, "AUTOMATION")
        assert TaskCategory.AUTOMATION.value == "automation"
    
    def test_has_verification(self):
        """Should have VERIFICATION category"""
        assert hasattr(TaskCategory, "VERIFICATION")
        assert TaskCategory.VERIFICATION.value == "verification"
    
    def test_has_travel(self):
        """Should have TRAVEL category"""
        assert hasattr(TaskCategory, "TRAVEL")
        assert TaskCategory.TRAVEL.value == "travel"
    
    def test_has_shopping(self):
        """Should have SHOPPING category"""
        assert hasattr(TaskCategory, "SHOPPING")
        assert TaskCategory.SHOPPING.value == "shopping"


class TestTaskStatusEnum:
    """Test TaskStatus enum"""
    
    def test_has_pending(self):
        """Should have PENDING status"""
        assert hasattr(TaskStatus, "PENDING")
        assert TaskStatus.PENDING.value == "pending"
    
    def test_has_awaiting_input(self):
        """Should have AWAITING_INPUT status"""
        assert hasattr(TaskStatus, "AWAITING_INPUT")
        assert TaskStatus.AWAITING_INPUT.value == "awaiting_input"
    
    def test_has_awaiting_confirmation(self):
        """Should have AWAITING_CONFIRMATION status"""
        assert hasattr(TaskStatus, "AWAITING_CONFIRMATION")
    
    def test_has_awaiting_verification(self):
        """Should have AWAITING_VERIFICATION status"""
        assert hasattr(TaskStatus, "AWAITING_VERIFICATION")
    
    def test_has_processing(self):
        """Should have PROCESSING status"""
        assert hasattr(TaskStatus, "PROCESSING")
        assert TaskStatus.PROCESSING.value == "processing"
    
    def test_has_executing(self):
        """Should have EXECUTING status"""
        assert hasattr(TaskStatus, "EXECUTING")
        assert TaskStatus.EXECUTING.value == "executing"
    
    def test_has_completed(self):
        """Should have COMPLETED status"""
        assert hasattr(TaskStatus, "COMPLETED")
        assert TaskStatus.COMPLETED.value == "completed"
    
    def test_has_failed(self):
        """Should have FAILED status"""
        assert hasattr(TaskStatus, "FAILED")
        assert TaskStatus.FAILED.value == "failed"
    
    def test_has_cancelled(self):
        """Should have CANCELLED status"""
        assert hasattr(TaskStatus, "CANCELLED")
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestSecurityLevelEnum:
    """Test SecurityLevel enum"""
    
    def test_has_low(self):
        """Should have LOW level"""
        assert hasattr(SecurityLevel, "LOW")
        assert SecurityLevel.LOW.value == 1
    
    def test_has_medium(self):
        """Should have MEDIUM level"""
        assert hasattr(SecurityLevel, "MEDIUM")
        assert SecurityLevel.MEDIUM.value == 2
    
    def test_has_high(self):
        """Should have HIGH level"""
        assert hasattr(SecurityLevel, "HIGH")
        assert SecurityLevel.HIGH.value == 3
    
    def test_has_critical(self):
        """Should have CRITICAL level"""
        assert hasattr(SecurityLevel, "CRITICAL")
        assert SecurityLevel.CRITICAL.value == 4
    
    def test_has_ultra(self):
        """Should have ULTRA level"""
        assert hasattr(SecurityLevel, "ULTRA")
        assert SecurityLevel.ULTRA.value == 5
    
    def test_security_ordering(self):
        """Security levels should be ordered correctly"""
        assert SecurityLevel.LOW.value < SecurityLevel.MEDIUM.value
        assert SecurityLevel.MEDIUM.value < SecurityLevel.HIGH.value
        assert SecurityLevel.HIGH.value < SecurityLevel.CRITICAL.value
        assert SecurityLevel.CRITICAL.value < SecurityLevel.ULTRA.value


class TestTaskContextDataclass:
    """Test TaskContext dataclass"""
    
    def test_is_dataclass(self):
        """TaskContext should be a dataclass"""
        assert is_dataclass(TaskContext)
    
    def test_can_create(self):
        """TaskContext should be creatable"""
        ctx = TaskContext(user_id="user-1", session_id="sess-1")
        assert ctx is not None
    
    def test_has_user_id(self):
        """Should have user_id"""
        ctx = TaskContext(user_id="my-user", session_id="sess")
        assert ctx.user_id == "my-user"
    
    def test_has_session_id(self):
        """Should have session_id"""
        ctx = TaskContext(user_id="u", session_id="my-session")
        assert ctx.session_id == "my-session"
    
    def test_default_conversation_history(self):
        """Default conversation_history should be empty list"""
        ctx = TaskContext(user_id="u", session_id="s")
        assert ctx.conversation_history == []
    
    def test_default_verified_identity_false(self):
        """Default verified_identity should be False"""
        ctx = TaskContext(user_id="u", session_id="s")
        assert ctx.verified_identity is False
    
    def test_default_security_level_low(self):
        """Default security_level should be LOW"""
        ctx = TaskContext(user_id="u", session_id="s")
        assert ctx.security_level == SecurityLevel.LOW


class TestTaskRequirementDataclass:
    """Test TaskRequirement dataclass"""
    
    def test_is_dataclass(self):
        """TaskRequirement should be a dataclass"""
        assert is_dataclass(TaskRequirement)
    
    def test_can_create(self):
        """TaskRequirement should be creatable"""
        req = TaskRequirement(name="email", description="User email")
        assert req is not None
    
    def test_has_name(self):
        """Should have name"""
        req = TaskRequirement(name="phone", description="desc")
        assert req.name == "phone"
    
    def test_has_description(self):
        """Should have description"""
        req = TaskRequirement(name="n", description="Phone number")
        assert req.description == "Phone number"
    
    def test_default_required_true(self):
        """Default required should be True"""
        req = TaskRequirement(name="n", description="d")
        assert req.required is True
    
    def test_default_collected_false(self):
        """Default collected should be False"""
        req = TaskRequirement(name="n", description="d")
        assert req.collected is False
    
    def test_default_value_none(self):
        """Default value should be None"""
        req = TaskRequirement(name="n", description="d")
        assert req.value is None


class TestInteractiveOptionDataclass:
    """Test InteractiveOption dataclass"""
    
    def test_is_dataclass(self):
        """InteractiveOption should be a dataclass"""
        assert is_dataclass(InteractiveOption)
    
    def test_can_create(self):
        """InteractiveOption should be creatable"""
        opt = InteractiveOption(id="opt-1", label="Option 1")
        assert opt is not None
    
    def test_has_id(self):
        """Should have id"""
        opt = InteractiveOption(id="my-id", label="Label")
        assert opt.id == "my-id"
    
    def test_has_label(self):
        """Should have label"""
        opt = InteractiveOption(id="id", label="My Label")
        assert opt.label == "My Label"
    
    def test_default_description_none(self):
        """Default description should be None"""
        opt = InteractiveOption(id="id", label="l")
        assert opt.description is None
    
    def test_default_icon_none(self):
        """Default icon should be None"""
        opt = InteractiveOption(id="id", label="l")
        assert opt.icon is None
    
    def test_default_action_none(self):
        """Default action should be None"""
        opt = InteractiveOption(id="id", label="l")
        assert opt.action is None


class TestTaskStepDataclass:
    """Test TaskStep dataclass"""
    
    def test_is_dataclass(self):
        """TaskStep should be a dataclass"""
        assert is_dataclass(TaskStep)
    
    def test_can_create(self):
        """TaskStep should be creatable"""
        step = TaskStep(step_id="s-1", name="Step 1", description="First step")
        assert step is not None
    
    def test_has_step_id(self):
        """Should have step_id"""
        step = TaskStep(step_id="my-step", name="n", description="d")
        assert step.step_id == "my-step"
    
    def test_has_name(self):
        """Should have name"""
        step = TaskStep(step_id="s", name="My Step", description="d")
        assert step.name == "My Step"
    
    def test_has_description(self):
        """Should have description"""
        step = TaskStep(step_id="s", name="n", description="My Desc")
        assert step.description == "My Desc"
    
    def test_default_status_pending(self):
        """Default status should be PENDING"""
        step = TaskStep(step_id="s", name="n", description="d")
        assert step.status == TaskStatus.PENDING
    
    def test_default_requirements_empty(self):
        """Default requirements should be empty list"""
        step = TaskStep(step_id="s", name="n", description="d")
        assert step.requirements == []
    
    def test_default_result_none(self):
        """Default result should be None"""
        step = TaskStep(step_id="s", name="n", description="d")
        assert step.result is None


class TestTaskExecutionDataclass:
    """Test TaskExecution dataclass"""
    
    def test_is_dataclass(self):
        """TaskExecution should be a dataclass"""
        assert is_dataclass(TaskExecution)
    
    def test_can_create(self):
        """TaskExecution should be creatable"""
        task = TaskExecution(
            task_id="task-1",
            category=TaskCategory.BOOKING,
            original_request="Book a ticket",
            parsed_intent={}
        )
        assert task is not None
    
    def test_has_task_id(self):
        """Should have task_id"""
        task = TaskExecution(
            task_id="my-task",
            category=TaskCategory.BOOKING,
            original_request="r",
            parsed_intent={}
        )
        assert task.task_id == "my-task"
    
    def test_has_category(self):
        """Should have category"""
        task = TaskExecution(
            task_id="t",
            category=TaskCategory.PAYMENT,
            original_request="r",
            parsed_intent={}
        )
        assert task.category == TaskCategory.PAYMENT
    
    def test_default_status_pending(self):
        """Default status should be PENDING"""
        task = TaskExecution(
            task_id="t",
            category=TaskCategory.BOOKING,
            original_request="r",
            parsed_intent={}
        )
        assert task.status == TaskStatus.PENDING
    
    def test_default_security_low(self):
        """Default security_level should be LOW"""
        task = TaskExecution(
            task_id="t",
            category=TaskCategory.BOOKING,
            original_request="r",
            parsed_intent={}
        )
        assert task.security_level == SecurityLevel.LOW
    
    def test_default_requires_confirmation_false(self):
        """Default requires_confirmation should be False"""
        task = TaskExecution(
            task_id="t",
            category=TaskCategory.BOOKING,
            original_request="r",
            parsed_intent={}
        )
        assert task.requires_confirmation is False
    
    def test_has_created_at(self):
        """Should have created_at timestamp"""
        task = TaskExecution(
            task_id="t",
            category=TaskCategory.BOOKING,
            original_request="r",
            parsed_intent={}
        )
        assert isinstance(task.created_at, datetime)


class TestTaskExecutionToDict:
    """Test TaskExecution to_dict method"""
    
    def test_has_to_dict_method(self):
        """Should have to_dict method"""
        task = TaskExecution(
            task_id="t",
            category=TaskCategory.BOOKING,
            original_request="r",
            parsed_intent={}
        )
        assert hasattr(task, "to_dict")
        assert callable(task.to_dict)
    
    def test_to_dict_returns_dict(self):
        """to_dict should return dict"""
        task = TaskExecution(
            task_id="t",
            category=TaskCategory.BOOKING,
            original_request="r",
            parsed_intent={}
        )
        result = task.to_dict()
        assert isinstance(result, dict)
    
    def test_to_dict_includes_task_id(self):
        """to_dict should include task_id"""
        task = TaskExecution(
            task_id="xyz",
            category=TaskCategory.BOOKING,
            original_request="r",
            parsed_intent={}
        )
        result = task.to_dict()
        assert result["task_id"] == "xyz"
    
    def test_to_dict_includes_category_value(self):
        """to_dict should include category as string value"""
        task = TaskExecution(
            task_id="t",
            category=TaskCategory.PAYMENT,
            original_request="r",
            parsed_intent={}
        )
        result = task.to_dict()
        assert result["category"] == "payment"


class TestIntentParserClass:
    """Test IntentParser class"""
    
    def test_class_exists(self):
        """IntentParser class should exist"""
        assert IntentParser is not None
    
    def test_has_intent_patterns(self):
        """Should have INTENT_PATTERNS"""
        assert hasattr(IntentParser, "INTENT_PATTERNS")
    
    def test_intent_patterns_is_dict(self):
        """INTENT_PATTERNS should be a dict"""
        assert isinstance(IntentParser.INTENT_PATTERNS, dict)
    
    def test_intent_patterns_not_empty(self):
        """INTENT_PATTERNS should not be empty"""
        assert len(IntentParser.INTENT_PATTERNS) > 0
    
    def test_intent_patterns_have_category(self):
        """Each pattern should have category"""
        for pattern, config in IntentParser.INTENT_PATTERNS.items():
            assert "category" in config
    
    def test_intent_patterns_have_security(self):
        """Each pattern should have security level"""
        for pattern, config in IntentParser.INTENT_PATTERNS.items():
            assert "security" in config
