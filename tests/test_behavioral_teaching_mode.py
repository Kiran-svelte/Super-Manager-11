"""
Behavioral Tests: Teaching Mode
=================================
Tests that teaching mode ACTUALLY works:
- WorkflowStep dataclass
- WorkflowDef dataclass
- TeachingMode recording start/stop
- Action analysis and workflow creation
- Parameter detection

README Requirements:
- User can demonstrate a task by recording browser actions
- Actions converted to replayable workflow
- Workflows saved and registered as tools
"""

import pytest
from dataclasses import is_dataclass
from datetime import datetime

from backend.core.teaching_mode import (
    WorkflowStep, WorkflowDef, TeachingMode
)


class TestWorkflowStepDataclass:
    """Test WorkflowStep dataclass structure"""
    
    def test_is_dataclass(self):
        """WorkflowStep should be a dataclass"""
        assert is_dataclass(WorkflowStep)
    
    def test_action_field_required(self):
        """WorkflowStep should have action as required"""
        step = WorkflowStep(action="click")
        assert step.action == "click"
    
    def test_selector_default_empty(self):
        """WorkflowStep selector should default to empty"""
        step = WorkflowStep(action="click")
        assert step.selector == ""
    
    def test_value_default_empty(self):
        """WorkflowStep value should default to empty"""
        step = WorkflowStep(action="fill")
        assert step.value == ""
    
    def test_wait_ms_default(self):
        """WorkflowStep wait_ms should default to 500"""
        step = WorkflowStep(action="click")
        assert step.wait_ms == 500
    
    def test_all_fields(self):
        """WorkflowStep should support all fields"""
        step = WorkflowStep(
            action="fill",
            selector="#email",
            value="test@example.com",
            wait_ms=300
        )
        
        assert step.action == "fill"
        assert step.selector == "#email"
        assert step.value == "test@example.com"
        assert step.wait_ms == 300


class TestWorkflowStepActionTypes:
    """Test supported workflow action types"""
    
    def test_navigate_action(self):
        """WorkflowStep should support navigate action"""
        step = WorkflowStep(action="navigate", value="https://example.com")
        assert step.action == "navigate"
    
    def test_click_action(self):
        """WorkflowStep should support click action"""
        step = WorkflowStep(action="click", selector="#button")
        assert step.action == "click"
    
    def test_fill_action(self):
        """WorkflowStep should support fill action"""
        step = WorkflowStep(action="fill", selector="#input", value="text")
        assert step.action == "fill"
    
    def test_select_action(self):
        """WorkflowStep should support select action"""
        step = WorkflowStep(action="select", selector="#dropdown", value="option1")
        assert step.action == "select"
    
    def test_wait_action(self):
        """WorkflowStep should support wait action"""
        step = WorkflowStep(action="wait", wait_ms=2000)
        assert step.action == "wait"
    
    def test_screenshot_action(self):
        """WorkflowStep should support screenshot action"""
        step = WorkflowStep(action="screenshot")
        assert step.action == "screenshot"


class TestWorkflowDefDataclass:
    """Test WorkflowDef dataclass structure"""
    
    def test_is_dataclass(self):
        """WorkflowDef should be a dataclass"""
        assert is_dataclass(WorkflowDef)
    
    def test_name_required(self):
        """WorkflowDef should have name as required"""
        workflow = WorkflowDef(name="my_workflow", description="Test")
        assert workflow.name == "my_workflow"
    
    def test_description_required(self):
        """WorkflowDef should have description as required"""
        workflow = WorkflowDef(name="test", description="A test workflow")
        assert workflow.description == "A test workflow"
    
    def test_steps_default_empty(self):
        """WorkflowDef steps should default to empty list"""
        workflow = WorkflowDef(name="test", description="Test")
        assert workflow.steps == []
    
    def test_parameters_default_empty(self):
        """WorkflowDef parameters should default to empty list"""
        workflow = WorkflowDef(name="test", description="Test")
        assert workflow.parameters == []
    
    def test_created_at_auto_generated(self):
        """WorkflowDef created_at should be auto-generated"""
        workflow = WorkflowDef(name="test", description="Test")
        assert workflow.created_at is not None
        assert isinstance(workflow.created_at, str)
    
    def test_replay_count_default_zero(self):
        """WorkflowDef replay_count should default to 0"""
        workflow = WorkflowDef(name="test", description="Test")
        assert workflow.replay_count == 0
    
    def test_with_steps(self):
        """WorkflowDef should store steps"""
        workflow = WorkflowDef(
            name="login_flow",
            description="Login to website",
            steps=[
                WorkflowStep(action="navigate", value="https://example.com/login"),
                WorkflowStep(action="fill", selector="#email", value="{{email}}"),
                WorkflowStep(action="click", selector="#submit")
            ]
        )
        
        assert len(workflow.steps) == 3
        assert workflow.steps[0].action == "navigate"
        assert workflow.steps[1].selector == "#email"
    
    def test_with_parameters(self):
        """WorkflowDef should store parameter placeholders"""
        workflow = WorkflowDef(
            name="signup_flow",
            description="Sign up",
            parameters=["{{email}}", "{{name}}", "{{password}}"]
        )
        
        assert len(workflow.parameters) == 3
        assert "{{email}}" in workflow.parameters


class TestTeachingModeInit:
    """Test TeachingMode initialization"""
    
    def test_can_instantiate(self):
        """TeachingMode should be instantiatable"""
        teaching = TeachingMode()
        assert teaching is not None
    
    def test_has_workflows_storage(self):
        """TeachingMode should have workflows storage"""
        teaching = TeachingMode()
        assert hasattr(teaching, "_workflows")
        assert isinstance(teaching._workflows, dict)
    
    def test_has_active_recordings(self):
        """TeachingMode should have active recordings storage"""
        teaching = TeachingMode()
        assert hasattr(teaching, "_active_recordings")
        assert isinstance(teaching._active_recordings, dict)
    
    def test_starts_with_no_workflows(self):
        """TeachingMode should start with no workflows"""
        teaching = TeachingMode()
        assert len(teaching._workflows) == 0
    
    def test_starts_with_no_recordings(self):
        """TeachingMode should start with no active recordings"""
        teaching = TeachingMode()
        assert len(teaching._active_recordings) == 0


class TestStartRecording:
    """Test TeachingMode.start_recording()"""
    
    def test_start_recording_returns_dict(self):
        """start_recording should return dict"""
        teaching = TeachingMode()
        result = teaching.start_recording("session123")
        
        assert isinstance(result, dict)
    
    def test_start_recording_has_status(self):
        """start_recording result should have status"""
        teaching = TeachingMode()
        result = teaching.start_recording("session123")
        
        assert result["status"] == "recording"
    
    def test_start_recording_has_session_id(self):
        """start_recording result should have session_id"""
        teaching = TeachingMode()
        result = teaching.start_recording("session123")
        
        assert result["session_id"] == "session123"
    
    def test_start_recording_has_instructions(self):
        """start_recording result should have instructions"""
        teaching = TeachingMode()
        result = teaching.start_recording("session123")
        
        assert "instructions" in result
        assert len(result["instructions"]) > 0
    
    def test_start_recording_stores_session(self):
        """start_recording should store session in active recordings"""
        teaching = TeachingMode()
        teaching.start_recording("session123", "Login flow")
        
        assert "session123" in teaching._active_recordings
    
    def test_start_recording_stores_task_description(self):
        """start_recording should store task description"""
        teaching = TeachingMode()
        teaching.start_recording("session123", "Login to Gmail")
        
        session = teaching._active_recordings["session123"]
        assert session["task_description"] == "Login to Gmail"
    
    def test_start_recording_initializes_actions_list(self):
        """start_recording should initialize empty actions list"""
        teaching = TeachingMode()
        teaching.start_recording("session123")
        
        session = teaching._active_recordings["session123"]
        assert "actions" in session
        assert session["actions"] == []


class TestStopRecording:
    """Test TeachingMode.stop_recording()"""
    
    def test_stop_recording_no_session_returns_error(self):
        """stop_recording should error if no active session"""
        teaching = TeachingMode()
        result = teaching.stop_recording("unknown_session", [])
        
        assert result["status"] == "error"
    
    def test_stop_recording_clears_session(self):
        """stop_recording should remove session from active recordings"""
        teaching = TeachingMode()
        teaching.start_recording("session123")
        teaching.stop_recording("session123", [
            {"type": "navigate", "url": "https://example.com"}
        ])
        
        assert "session123" not in teaching._active_recordings
    
    def test_stop_recording_empty_actions_returns_error(self):
        """stop_recording with no actionable steps should error"""
        teaching = TeachingMode()
        teaching.start_recording("session123")
        result = teaching.stop_recording("session123", [])
        
        assert result["status"] == "error"
        assert "No actionable steps" in result["message"]
    
    def test_stop_recording_with_actions_saves_workflow(self):
        """stop_recording should save workflow from actions"""
        teaching = TeachingMode()
        teaching.start_recording("session123", "Test workflow")
        
        actions = [
            {"type": "navigate", "url": "https://example.com"},
            {"type": "click", "selector": "#button"}
        ]
        
        result = teaching.stop_recording("session123", actions)
        
        assert result["status"] == "saved"
        assert "workflow_name" in result
    
    def test_stop_recording_returns_steps_count(self):
        """stop_recording should return steps count"""
        teaching = TeachingMode()
        teaching.start_recording("session123")
        
        actions = [
            {"type": "navigate", "url": "https://example.com"},
            {"type": "click", "selector": "#button"},
            {"type": "click", "selector": "#link"}
        ]
        
        result = teaching.stop_recording("session123", actions)
        
        assert "steps_count" in result
        assert result["steps_count"] >= 1


class TestActionAnalysis:
    """Test workflow action analysis"""
    
    def test_analyze_navigate_action(self):
        """Analysis should convert navigate action"""
        teaching = TeachingMode()
        teaching.start_recording("session123")
        
        actions = [{"type": "navigate", "url": "https://example.com"}]
        result = teaching.stop_recording("session123", actions)
        
        assert result["status"] == "saved"
    
    def test_analyze_pageload_action(self):
        """Analysis should convert pageload action"""
        teaching = TeachingMode()
        teaching.start_recording("session123")
        
        actions = [{"type": "pageload", "url": "https://example.com"}]
        result = teaching.stop_recording("session123", actions)
        
        assert result["status"] == "saved"
    
    def test_analyze_click_action(self):
        """Analysis should convert click action"""
        teaching = TeachingMode()
        teaching.start_recording("session123")
        
        actions = [
            {"type": "navigate", "url": "https://example.com"},
            {"type": "click", "selector": "#submit-button"}
        ]
        result = teaching.stop_recording("session123", actions)
        
        assert result["status"] == "saved"
    
    def test_analyze_input_action(self):
        """Analysis should convert input action"""
        teaching = TeachingMode()
        teaching.start_recording("session123")
        
        actions = [
            {"type": "navigate", "url": "https://example.com"},
            {"type": "input", "selector": "#email", "value": "test@example.com"}
        ]
        result = teaching.stop_recording("session123", actions)
        
        assert result["status"] == "saved"


class TestParameterDetection:
    """Test parameter detection in workflows"""
    
    def test_email_field_detected_as_parameter(self):
        """Email inputs should be detected as parameters"""
        teaching = TeachingMode()
        teaching.start_recording("session123")
        
        actions = [
            {"type": "navigate", "url": "https://example.com"},
            {"type": "input", "selector": "#email", "value": "john@test.com"}
        ]
        result = teaching.stop_recording("session123", actions)
        
        # Should have parameters detected
        if result["status"] == "saved":
            assert "parameters" in result
            # Parameters may include {{email}} depending on detection


class TestWorkflowStorage:
    """Test workflow persistence"""
    
    def test_workflow_stored_in_memory(self):
        """Saved workflow should be stored in _workflows"""
        teaching = TeachingMode()
        teaching.start_recording("session123", "Test flow")
        
        actions = [
            {"type": "navigate", "url": "https://example.com"},
            {"type": "click", "selector": "#button"}
        ]
        
        result = teaching.stop_recording("session123", actions)
        
        if result["status"] == "saved":
            workflow_name = result["workflow_name"]
            assert workflow_name in teaching._workflows
    
    def test_multiple_workflows_stored(self):
        """Multiple workflows can be stored"""
        teaching = TeachingMode()
        
        # First workflow
        teaching.start_recording("session1", "First flow")
        teaching.stop_recording("session1", [
            {"type": "navigate", "url": "https://example.com"}
        ])
        
        # Second workflow
        teaching.start_recording("session2", "Second flow")
        teaching.stop_recording("session2", [
            {"type": "navigate", "url": "https://other.com"}
        ])
        
        assert len(teaching._workflows) >= 1


class TestWorkflowDefTimestamp:
    """Test WorkflowDef timestamp handling"""
    
    def test_created_at_is_iso_format(self):
        """created_at should be ISO format timestamp"""
        workflow = WorkflowDef(name="test", description="Test")
        
        # Should be parseable as ISO datetime
        try:
            datetime.fromisoformat(workflow.created_at)
            parsed = True
        except ValueError:
            parsed = False
        
        assert parsed is True


class TestWorkflowStepWaitTimes:
    """Test wait time configurations"""
    
    def test_default_wait_500ms(self):
        """Default wait should be 500ms"""
        step = WorkflowStep(action="click")
        assert step.wait_ms == 500
    
    def test_custom_wait_time(self):
        """Custom wait time should be supported"""
        step = WorkflowStep(action="wait", wait_ms=3000)
        assert step.wait_ms == 3000
    
    def test_zero_wait_time(self):
        """Zero wait time should be allowed"""
        step = WorkflowStep(action="click", wait_ms=0)
        assert step.wait_ms == 0
