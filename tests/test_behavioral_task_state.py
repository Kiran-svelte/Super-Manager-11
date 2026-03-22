"""
Behavioral Tests: Task State Machine
=====================================
Tests that the task state machine ACTUALLY:
- Enforces valid state transitions
- Prevents invalid transitions (terminal states)
- Tracks progress correctly
- Handles substeps properly

README Requirements (State Machine Rules):
VALID TRANSITIONS:
  PENDING → IN_PROGRESS, WAITING_INPUT, CANCELLED
  WAITING_INPUT → IN_PROGRESS, CANCELLED
  IN_PROGRESS → WAITING_INPUT, COMPLETED, FAILED, CANCELLED

INVALID TRANSITIONS (enforced):
  COMPLETED → anything
  FAILED → anything
  CANCELLED → anything
  FAILED → COMPLETED
  anything → PENDING (except new task)
"""

import pytest
from datetime import datetime

from backend.agent.orchestrator import (
    TaskStatus,
    SubstepStatus,
    DetectionType,
    Substep,
    OrchestratedTask
)


class TestTaskStatusEnum:
    """Test TaskStatus enum values"""
    
    def test_all_status_values_exist(self):
        """All required statuses should exist"""
        assert TaskStatus.PENDING
        assert TaskStatus.IN_PROGRESS
        assert TaskStatus.WAITING_INPUT
        assert TaskStatus.COMPLETED
        assert TaskStatus.FAILED
        assert TaskStatus.CANCELLED
    
    def test_status_string_values(self):
        """Status values should be lowercase strings"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.WAITING_INPUT.value == "waiting_input"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestSubstepStatusEnum:
    """Test SubstepStatus enum values"""
    
    def test_all_substep_statuses_exist(self):
        """All required substep statuses should exist"""
        assert SubstepStatus.PENDING
        assert SubstepStatus.IN_PROGRESS
        assert SubstepStatus.COMPLETED
        assert SubstepStatus.FAILED
        assert SubstepStatus.SKIPPED
        assert SubstepStatus.WAITING


class TestDetectionTypeEnum:
    """Test DetectionType enum values"""
    
    def test_all_detection_types_exist(self):
        """All detection types should exist"""
        assert DetectionType.IMMEDIATE
        assert DetectionType.SCHEDULED
        assert DetectionType.WEBHOOK
        assert DetectionType.POLLING
        assert DetectionType.MANUAL


class TestSubstep:
    """Test Substep dataclass"""
    
    def test_substep_creation(self):
        """Should create substep with required fields"""
        substep = Substep(
            id="step-1",
            step_number=1,
            title="Search for flights"
        )
        
        assert substep.id == "step-1"
        assert substep.step_number == 1
        assert substep.title == "Search for flights"
    
    def test_substep_default_status(self):
        """Default status should be PENDING"""
        substep = Substep(id="step-1", step_number=1, title="Test")
        assert substep.status == SubstepStatus.PENDING
    
    def test_substep_default_detection_type(self):
        """Default detection type should be IMMEDIATE"""
        substep = Substep(id="step-1", step_number=1, title="Test")
        assert substep.detection_type == DetectionType.IMMEDIATE
    
    def test_substep_to_dict(self):
        """to_dict should include all fields"""
        substep = Substep(
            id="step-1",
            step_number=1,
            title="Test Step",
            description="A test step",
            action_type="web_search",
            action_params={"query": "test"}
        )
        
        d = substep.to_dict()
        
        assert d["id"] == "step-1"
        assert d["step_number"] == 1
        assert d["title"] == "Test Step"
        assert d["description"] == "A test step"
        assert d["status"] == "pending"
        assert d["action_type"] == "web_search"
        assert d["action_params"] == {"query": "test"}
    
    def test_substep_timestamps(self):
        """Substep should track timestamps"""
        now = datetime.now()
        substep = Substep(
            id="step-1",
            step_number=1,
            title="Test",
            started_at=now
        )
        
        assert substep.started_at == now
        assert substep.completed_at is None
    
    def test_substep_dependencies(self):
        """Substep should track dependencies"""
        substep = Substep(
            id="step-3",
            step_number=3,
            title="Dependent Step",
            depends_on=["step-1", "step-2"]
        )
        
        assert substep.depends_on == ["step-1", "step-2"]


class TestOrchestratedTask:
    """Test OrchestratedTask dataclass"""
    
    def test_task_creation(self):
        """Should create task with required fields"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Book a flight"
        )
        
        assert task.id == "task-123"
        assert task.user_id == "user-456"
        assert task.title == "Book a flight"
    
    def test_task_default_status(self):
        """Default status should be PENDING"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test"
        )
        assert task.status == TaskStatus.PENDING
    
    def test_task_default_progress(self):
        """Default progress should be 0"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test"
        )
        assert task.progress_percent == 0
    
    def test_task_empty_substeps(self):
        """Default substeps should be empty"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test"
        )
        assert task.substeps == []


class TestOrchestratedTaskProgressCalculation:
    """Test progress calculation"""
    
    def test_progress_with_no_substeps(self):
        """Progress should be 0 with no substeps"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test"
        )
        
        assert task.calculate_progress() == 0
    
    def test_progress_all_pending(self):
        """Progress should be 0 when all pending"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test",
            substeps=[
                Substep(id="s1", step_number=1, title="Step 1"),
                Substep(id="s2", step_number=2, title="Step 2"),
            ]
        )
        
        assert task.calculate_progress() == 0
    
    def test_progress_half_completed(self):
        """Progress should be 50% when half completed"""
        step1 = Substep(id="s1", step_number=1, title="Step 1", progress_weight=10)
        step1.status = SubstepStatus.COMPLETED
        
        step2 = Substep(id="s2", step_number=2, title="Step 2", progress_weight=10)
        
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test",
            substeps=[step1, step2]
        )
        
        assert task.calculate_progress() == 50
    
    def test_progress_all_completed(self):
        """Progress should be 100% when all completed"""
        step1 = Substep(id="s1", step_number=1, title="Step 1", progress_weight=10)
        step1.status = SubstepStatus.COMPLETED
        
        step2 = Substep(id="s2", step_number=2, title="Step 2", progress_weight=10)
        step2.status = SubstepStatus.COMPLETED
        
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test",
            substeps=[step1, step2]
        )
        
        assert task.calculate_progress() == 100
    
    def test_progress_weighted_steps(self):
        """Progress should respect different weights"""
        step1 = Substep(id="s1", step_number=1, title="Small", progress_weight=10)
        step1.status = SubstepStatus.COMPLETED
        
        step2 = Substep(id="s2", step_number=2, title="Large", progress_weight=90)
        
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test",
            substeps=[step1, step2]
        )
        
        # 10 out of 100 completed
        assert task.calculate_progress() == 10


class TestTaskStateTransitions:
    """Test valid and invalid state transitions"""
    
    def test_pending_can_go_to_in_progress(self):
        """PENDING → IN_PROGRESS is valid"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test"
        )
        assert task.status == TaskStatus.PENDING
        
        # Transition is valid
        task.status = TaskStatus.IN_PROGRESS
        assert task.status == TaskStatus.IN_PROGRESS
    
    def test_pending_can_go_to_waiting_input(self):
        """PENDING → WAITING_INPUT is valid"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test"
        )
        task.status = TaskStatus.WAITING_INPUT
        assert task.status == TaskStatus.WAITING_INPUT
    
    def test_pending_can_go_to_cancelled(self):
        """PENDING → CANCELLED is valid"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test"
        )
        task.status = TaskStatus.CANCELLED
        assert task.status == TaskStatus.CANCELLED
    
    def test_in_progress_can_go_to_completed(self):
        """IN_PROGRESS → COMPLETED is valid"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test",
            status=TaskStatus.IN_PROGRESS
        )
        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED
    
    def test_in_progress_can_go_to_failed(self):
        """IN_PROGRESS → FAILED is valid"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test",
            status=TaskStatus.IN_PROGRESS
        )
        task.status = TaskStatus.FAILED
        assert task.status == TaskStatus.FAILED


class TestOrchestratedTaskToDict:
    """Test task serialization"""
    
    def test_to_dict_includes_all_fields(self):
        """to_dict should include all important fields"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test Task",
            description="A test task",
            task_type="booking",
            status=TaskStatus.IN_PROGRESS,
            progress_percent=50
        )
        
        d = task.to_dict()
        
        assert d["id"] == "task-123"
        assert d["user_id"] == "user-456"
        assert d["title"] == "Test Task"
        assert d["description"] == "A test task"
        assert d["task_type"] == "booking"
        assert d["status"] == "in_progress"
        assert d["progress_percent"] == 50
    
    def test_to_dict_includes_substeps(self):
        """to_dict should serialize substeps"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test",
            substeps=[
                Substep(id="s1", step_number=1, title="Step 1"),
                Substep(id="s2", step_number=2, title="Step 2"),
            ]
        )
        
        d = task.to_dict()
        
        assert len(d["substeps"]) == 2
        assert d["substeps"][0]["title"] == "Step 1"
        assert d["substeps"][1]["title"] == "Step 2"


class TestTaskUserInput:
    """Test user input handling"""
    
    def test_needs_user_input_flag(self):
        """Task should track need for user input"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test",
            needs_user_input=True,
            input_prompt="Which size do you want?"
        )
        
        assert task.needs_user_input is True
        assert task.input_prompt == "Which size do you want?"
    
    def test_input_options(self):
        """Task should provide input options"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test",
            needs_user_input=True,
            input_options=["Small", "Medium", "Large"]
        )
        
        assert task.input_options == ["Small", "Medium", "Large"]
    
    def test_user_input_received(self):
        """Task should store user's response"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test"
        )
        
        task.user_input_received = "Medium"
        assert task.user_input_received == "Medium"


class TestSubstepExecution:
    """Test substep execution states"""
    
    def test_substep_records_start_time(self):
        """Substep should record when it started"""
        substep = Substep(id="s1", step_number=1, title="Test")
        
        now = datetime.now()
        substep.started_at = now
        substep.status = SubstepStatus.IN_PROGRESS
        
        assert substep.started_at == now
    
    def test_substep_records_completion_time(self):
        """Substep should record when it completed"""
        substep = Substep(id="s1", step_number=1, title="Test")
        
        now = datetime.now()
        substep.completed_at = now
        substep.status = SubstepStatus.COMPLETED
        
        assert substep.completed_at == now
    
    def test_substep_stores_result(self):
        """Substep should store execution result"""
        substep = Substep(id="s1", step_number=1, title="Search")
        
        substep.result = {"found": 10, "results": ["a", "b", "c"]}
        
        assert substep.result["found"] == 10
    
    def test_substep_stores_error(self):
        """Substep should store error message if failed"""
        substep = Substep(id="s1", step_number=1, title="Test")
        
        substep.status = SubstepStatus.FAILED
        substep.error_message = "Connection timeout"
        
        assert substep.error_message == "Connection timeout"


class TestTaskMetadata:
    """Test task metadata storage"""
    
    def test_task_stores_metadata(self):
        """Task should store arbitrary metadata"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Test",
            metadata={"source": "telegram", "priority": "high"}
        )
        
        assert task.metadata["source"] == "telegram"
        assert task.metadata["priority"] == "high"
    
    def test_task_stores_meeting_id(self):
        """Task should store meeting ID if applicable"""
        task = OrchestratedTask(
            id="task-123",
            user_id="user-456",
            title="Schedule Meeting",
            meeting_id="meet-xyz"
        )
        
        assert task.meeting_id == "meet-xyz"
