"""
Behavioral Tests: Task Orchestrator
=====================================
Tests that the orchestrator module ACTUALLY works:
- TaskStatus enum
- SubstepStatus enum
- DetectionType enum
- Substep dataclass
- OrchestratedTask dataclass
- TASK_TEMPLATES

README Requirements:
- Multi-step task orchestration
- Progress tracking
- Scheduling
- Dependency management
"""

import pytest
from datetime import datetime
from dataclasses import is_dataclass, fields

from backend.agent.orchestrator import (
    SUPABASE_AVAILABLE,
    TaskStatus,
    SubstepStatus,
    DetectionType,
    Substep,
    OrchestratedTask,
    TASK_TEMPLATES,
)


class TestSupabaseAvailable:
    """Test Supabase availability flag"""
    
    def test_supabase_available_is_bool(self):
        """SUPABASE_AVAILABLE should be boolean"""
        assert isinstance(SUPABASE_AVAILABLE, bool)


class TestTaskStatusEnum:
    """Test TaskStatus enum"""
    
    def test_has_pending(self):
        """Should have PENDING status"""
        assert hasattr(TaskStatus, "PENDING")
        assert TaskStatus.PENDING.value == "pending"
    
    def test_has_in_progress(self):
        """Should have IN_PROGRESS status"""
        assert hasattr(TaskStatus, "IN_PROGRESS")
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
    
    def test_has_waiting_input(self):
        """Should have WAITING_INPUT status"""
        assert hasattr(TaskStatus, "WAITING_INPUT")
        assert TaskStatus.WAITING_INPUT.value == "waiting_input"
    
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
    
    def test_status_count(self):
        """Should have 6 statuses"""
        assert len(TaskStatus) == 6


class TestSubstepStatusEnum:
    """Test SubstepStatus enum"""
    
    def test_has_pending(self):
        """Should have PENDING status"""
        assert hasattr(SubstepStatus, "PENDING")
        assert SubstepStatus.PENDING.value == "pending"
    
    def test_has_in_progress(self):
        """Should have IN_PROGRESS status"""
        assert hasattr(SubstepStatus, "IN_PROGRESS")
        assert SubstepStatus.IN_PROGRESS.value == "in_progress"
    
    def test_has_completed(self):
        """Should have COMPLETED status"""
        assert hasattr(SubstepStatus, "COMPLETED")
        assert SubstepStatus.COMPLETED.value == "completed"
    
    def test_has_failed(self):
        """Should have FAILED status"""
        assert hasattr(SubstepStatus, "FAILED")
        assert SubstepStatus.FAILED.value == "failed"
    
    def test_has_skipped(self):
        """Should have SKIPPED status"""
        assert hasattr(SubstepStatus, "SKIPPED")
        assert SubstepStatus.SKIPPED.value == "skipped"
    
    def test_has_waiting(self):
        """Should have WAITING status"""
        assert hasattr(SubstepStatus, "WAITING")
        assert SubstepStatus.WAITING.value == "waiting"
    
    def test_substep_status_count(self):
        """Should have 6 statuses"""
        assert len(SubstepStatus) == 6


class TestDetectionTypeEnum:
    """Test DetectionType enum"""
    
    def test_has_immediate(self):
        """Should have IMMEDIATE type"""
        assert hasattr(DetectionType, "IMMEDIATE")
        assert DetectionType.IMMEDIATE.value == "immediate"
    
    def test_has_scheduled(self):
        """Should have SCHEDULED type"""
        assert hasattr(DetectionType, "SCHEDULED")
        assert DetectionType.SCHEDULED.value == "scheduled"
    
    def test_has_webhook(self):
        """Should have WEBHOOK type"""
        assert hasattr(DetectionType, "WEBHOOK")
        assert DetectionType.WEBHOOK.value == "webhook"
    
    def test_has_polling(self):
        """Should have POLLING type"""
        assert hasattr(DetectionType, "POLLING")
        assert DetectionType.POLLING.value == "polling"
    
    def test_has_manual(self):
        """Should have MANUAL type"""
        assert hasattr(DetectionType, "MANUAL")
        assert DetectionType.MANUAL.value == "manual"
    
    def test_detection_type_count(self):
        """Should have 5 types"""
        assert len(DetectionType) == 5


class TestSubstepDataclass:
    """Test Substep dataclass"""
    
    def test_is_dataclass(self):
        """Substep should be a dataclass"""
        assert is_dataclass(Substep)
    
    def test_can_create_minimal(self):
        """Substep should be creatable with minimal fields"""
        substep = Substep(
            id="step-1",
            step_number=1,
            title="First Step"
        )
        assert substep is not None
    
    def test_has_id(self):
        """Should have id"""
        substep = Substep(id="my-id", step_number=1, title="Test")
        assert substep.id == "my-id"
    
    def test_has_step_number(self):
        """Should have step_number"""
        substep = Substep(id="s", step_number=5, title="Test")
        assert substep.step_number == 5
    
    def test_has_title(self):
        """Should have title"""
        substep = Substep(id="s", step_number=1, title="My Title")
        assert substep.title == "My Title"
    
    def test_default_description(self):
        """Default description should be empty"""
        substep = Substep(id="s", step_number=1, title="Test")
        assert substep.description == ""
    
    def test_default_status_is_pending(self):
        """Default status should be PENDING"""
        substep = Substep(id="s", step_number=1, title="Test")
        assert substep.status == SubstepStatus.PENDING
    
    def test_default_progress_weight(self):
        """Default progress_weight should be 10"""
        substep = Substep(id="s", step_number=1, title="Test")
        assert substep.progress_weight == 10
    
    def test_default_detection_type_is_immediate(self):
        """Default detection_type should be IMMEDIATE"""
        substep = Substep(id="s", step_number=1, title="Test")
        assert substep.detection_type == DetectionType.IMMEDIATE
    
    def test_default_depends_on_empty(self):
        """Default depends_on should be empty list"""
        substep = Substep(id="s", step_number=1, title="Test")
        assert substep.depends_on == []


class TestSubstepToDict:
    """Test Substep to_dict method"""
    
    def test_has_to_dict_method(self):
        """Should have to_dict method"""
        substep = Substep(id="s", step_number=1, title="Test")
        assert hasattr(substep, "to_dict")
        assert callable(substep.to_dict)
    
    def test_to_dict_returns_dict(self):
        """to_dict should return dict"""
        substep = Substep(id="s", step_number=1, title="Test")
        result = substep.to_dict()
        assert isinstance(result, dict)
    
    def test_to_dict_has_required_fields(self):
        """to_dict should include required fields"""
        substep = Substep(id="step-1", step_number=2, title="My Step")
        result = substep.to_dict()
        assert result["id"] == "step-1"
        assert result["step_number"] == 2
        assert result["title"] == "My Step"
    
    def test_to_dict_status_is_string(self):
        """to_dict status should be string value"""
        substep = Substep(id="s", step_number=1, title="Test", status=SubstepStatus.COMPLETED)
        result = substep.to_dict()
        assert result["status"] == "completed"


class TestOrchestratedTaskDataclass:
    """Test OrchestratedTask dataclass"""
    
    def test_is_dataclass(self):
        """OrchestratedTask should be a dataclass"""
        assert is_dataclass(OrchestratedTask)
    
    def test_can_create_minimal(self):
        """OrchestratedTask should be creatable with minimal fields"""
        task = OrchestratedTask(
            id="task-1",
            user_id="user-1",
            title="My Task"
        )
        assert task is not None
    
    def test_has_id(self):
        """Should have id"""
        task = OrchestratedTask(id="my-task-id", user_id="u", title="T")
        assert task.id == "my-task-id"
    
    def test_has_user_id(self):
        """Should have user_id"""
        task = OrchestratedTask(id="t", user_id="user-123", title="T")
        assert task.user_id == "user-123"
    
    def test_has_title(self):
        """Should have title"""
        task = OrchestratedTask(id="t", user_id="u", title="Important Task")
        assert task.title == "Important Task"
    
    def test_default_status_is_pending(self):
        """Default status should be PENDING"""
        task = OrchestratedTask(id="t", user_id="u", title="T")
        assert task.status == TaskStatus.PENDING
    
    def test_default_progress_is_zero(self):
        """Default progress_percent should be 0"""
        task = OrchestratedTask(id="t", user_id="u", title="T")
        assert task.progress_percent == 0
    
    def test_default_substeps_empty(self):
        """Default substeps should be empty list"""
        task = OrchestratedTask(id="t", user_id="u", title="T")
        assert task.substeps == []
    
    def test_default_needs_user_input_false(self):
        """Default needs_user_input should be False"""
        task = OrchestratedTask(id="t", user_id="u", title="T")
        assert task.needs_user_input is False


class TestOrchestratedTaskCalculateProgress:
    """Test OrchestratedTask calculate_progress method"""
    
    def test_has_calculate_progress_method(self):
        """Should have calculate_progress method"""
        task = OrchestratedTask(id="t", user_id="u", title="T")
        assert hasattr(task, "calculate_progress")
        assert callable(task.calculate_progress)
    
    def test_returns_zero_with_no_substeps(self):
        """Should return 0 with no substeps"""
        task = OrchestratedTask(id="t", user_id="u", title="T")
        assert task.calculate_progress() == 0
    
    def test_returns_100_when_all_completed(self):
        """Should return 100 when all substeps completed"""
        task = OrchestratedTask(id="t", user_id="u", title="T")
        task.substeps = [
            Substep(id="s1", step_number=1, title="Step 1", status=SubstepStatus.COMPLETED, progress_weight=50),
            Substep(id="s2", step_number=2, title="Step 2", status=SubstepStatus.COMPLETED, progress_weight=50),
        ]
        assert task.calculate_progress() == 100
    
    def test_returns_partial_progress(self):
        """Should return partial progress"""
        task = OrchestratedTask(id="t", user_id="u", title="T")
        task.substeps = [
            Substep(id="s1", step_number=1, title="Step 1", status=SubstepStatus.COMPLETED, progress_weight=25),
            Substep(id="s2", step_number=2, title="Step 2", status=SubstepStatus.PENDING, progress_weight=75),
        ]
        assert task.calculate_progress() == 25


class TestOrchestratedTaskToDict:
    """Test OrchestratedTask to_dict method"""
    
    def test_has_to_dict_method(self):
        """Should have to_dict method"""
        task = OrchestratedTask(id="t", user_id="u", title="T")
        assert hasattr(task, "to_dict")
        assert callable(task.to_dict)
    
    def test_to_dict_returns_dict(self):
        """to_dict should return dict"""
        task = OrchestratedTask(id="t", user_id="u", title="T")
        result = task.to_dict()
        assert isinstance(result, dict)
    
    def test_to_dict_includes_substeps(self):
        """to_dict should include substeps"""
        task = OrchestratedTask(id="t", user_id="u", title="T")
        task.substeps = [Substep(id="s1", step_number=1, title="SubStep 1")]
        result = task.to_dict()
        assert "substeps" in result
        assert len(result["substeps"]) == 1


class TestTaskTemplates:
    """Test TASK_TEMPLATES"""
    
    def test_task_templates_exists(self):
        """TASK_TEMPLATES should exist"""
        assert TASK_TEMPLATES is not None
    
    def test_task_templates_is_dict(self):
        """TASK_TEMPLATES should be dict"""
        assert isinstance(TASK_TEMPLATES, dict)
    
    def test_has_schedule_meeting_template(self):
        """Should have schedule_meeting template"""
        assert "schedule_meeting" in TASK_TEMPLATES
    
    def test_has_send_email_template(self):
        """Should have send_email template"""
        assert "send_email" in TASK_TEMPLATES
    
    def test_has_set_reminder_template(self):
        """Should have set_reminder template"""
        assert "set_reminder" in TASK_TEMPLATES
    
    def test_has_research_template(self):
        """Should have research template"""
        assert "research" in TASK_TEMPLATES
    
    def test_template_has_title_template(self):
        """Each template should have title_template"""
        for name, template in TASK_TEMPLATES.items():
            assert "title_template" in template, f"{name} missing title_template"
    
    def test_template_has_substeps(self):
        """Each template should have substeps"""
        for name, template in TASK_TEMPLATES.items():
            assert "substeps" in template, f"{name} missing substeps"
    
    def test_schedule_meeting_has_many_substeps(self):
        """schedule_meeting should have many substeps"""
        template = TASK_TEMPLATES["schedule_meeting"]
        assert len(template["substeps"]) >= 5


class TestSubstepDependencies:
    """Test Substep dependency handling"""
    
    def test_can_set_depends_on(self):
        """Should accept depends_on list"""
        substep = Substep(
            id="s2",
            step_number=2,
            title="Depends on step 1",
            depends_on=["s1"]
        )
        assert substep.depends_on == ["s1"]
    
    def test_can_have_multiple_dependencies(self):
        """Should accept multiple dependencies"""
        substep = Substep(
            id="s3",
            step_number=3,
            title="Depends on steps 1 and 2",
            depends_on=["s1", "s2"]
        )
        assert len(substep.depends_on) == 2
        assert "s1" in substep.depends_on
        assert "s2" in substep.depends_on


class TestSubstepDetection:
    """Test Substep detection configuration"""
    
    def test_can_set_scheduled_detection(self):
        """Should accept SCHEDULED detection type"""
        substep = Substep(
            id="s",
            step_number=1,
            title="Reminder",
            detection_type=DetectionType.SCHEDULED
        )
        assert substep.detection_type == DetectionType.SCHEDULED
    
    def test_can_set_webhook_detection(self):
        """Should accept WEBHOOK detection type"""
        substep = Substep(
            id="s",
            step_number=1,
            title="Wait for join",
            detection_type=DetectionType.WEBHOOK
        )
        assert substep.detection_type == DetectionType.WEBHOOK
    
    def test_can_set_detection_config(self):
        """Should accept detection_config"""
        substep = Substep(
            id="s",
            step_number=1,
            title="Poll status",
            detection_type=DetectionType.POLLING,
            detection_config={"interval_seconds": 30}
        )
        assert substep.detection_config["interval_seconds"] == 30
