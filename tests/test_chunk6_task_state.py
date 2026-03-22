"""
Chunk 6: Task State Machine Tests
=================================

Tests for README requirements:
- PENDING → IN_PROGRESS → COMPLETED task states
- Task substeps with progress tracking
- State transitions and validation
"""

import pytest
from datetime import datetime


# =============================================================================
# TaskStatus Enum Tests
# =============================================================================

class TestTaskStatusEnum:
    """Test TaskStatus enum exists and has expected values"""
    
    def test_task_status_enum_exists(self):
        """TaskStatus enum should exist"""
        from backend.agent.orchestrator import TaskStatus
        assert TaskStatus is not None
    
    def test_task_status_has_pending(self):
        """TaskStatus should have PENDING state"""
        from backend.agent.orchestrator import TaskStatus
        assert hasattr(TaskStatus, 'PENDING')
        assert TaskStatus.PENDING.value == "pending"
    
    def test_task_status_has_in_progress(self):
        """TaskStatus should have IN_PROGRESS state"""
        from backend.agent.orchestrator import TaskStatus
        assert hasattr(TaskStatus, 'IN_PROGRESS')
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
    
    def test_task_status_has_completed(self):
        """TaskStatus should have COMPLETED state"""
        from backend.agent.orchestrator import TaskStatus
        assert hasattr(TaskStatus, 'COMPLETED')
        assert TaskStatus.COMPLETED.value == "completed"
    
    def test_task_status_has_failed(self):
        """TaskStatus should have FAILED state"""
        from backend.agent.orchestrator import TaskStatus
        assert hasattr(TaskStatus, 'FAILED')
        assert TaskStatus.FAILED.value == "failed"
    
    def test_task_status_has_cancelled(self):
        """TaskStatus should have CANCELLED state"""
        from backend.agent.orchestrator import TaskStatus
        assert hasattr(TaskStatus, 'CANCELLED')
        assert TaskStatus.CANCELLED.value == "cancelled"
    
    def test_task_status_has_waiting_input(self):
        """TaskStatus should have WAITING_INPUT state"""
        from backend.agent.orchestrator import TaskStatus
        assert hasattr(TaskStatus, 'WAITING_INPUT')
        assert TaskStatus.WAITING_INPUT.value == "waiting_input"


# =============================================================================
# SubstepStatus Enum Tests
# =============================================================================

class TestSubstepStatusEnum:
    """Test SubstepStatus enum"""
    
    def test_substep_status_enum_exists(self):
        """SubstepStatus enum should exist"""
        from backend.agent.orchestrator import SubstepStatus
        assert SubstepStatus is not None
    
    def test_substep_status_has_expected_states(self):
        """SubstepStatus should have expected states"""
        from backend.agent.orchestrator import SubstepStatus
        
        assert hasattr(SubstepStatus, 'PENDING')
        assert hasattr(SubstepStatus, 'IN_PROGRESS')
        assert hasattr(SubstepStatus, 'COMPLETED')
        assert hasattr(SubstepStatus, 'FAILED')


# =============================================================================
# OrchestratedTask Tests
# =============================================================================

class TestOrchestratedTask:
    """Test OrchestratedTask dataclass"""
    
    def test_orchestrated_task_exists(self):
        """OrchestratedTask class should exist"""
        from backend.agent.orchestrator import OrchestratedTask
        assert OrchestratedTask is not None
    
    def test_task_has_required_fields(self):
        """OrchestratedTask should have required fields"""
        from backend.agent.orchestrator import OrchestratedTask, TaskStatus
        
        task = OrchestratedTask(
            id="test-task-1",
            user_id="user-1",
            title="Test Task"
        )
        
        assert task.id == "test-task-1"
        assert task.user_id == "user-1"
        assert task.title == "Test Task"
        assert task.status == TaskStatus.PENDING  # Default status
    
    def test_task_default_status_is_pending(self):
        """Task should default to PENDING status"""
        from backend.agent.orchestrator import OrchestratedTask, TaskStatus
        
        task = OrchestratedTask(
            id="test-task",
            user_id="user-1",
            title="Test"
        )
        
        assert task.status == TaskStatus.PENDING
    
    def test_task_has_substeps_list(self):
        """Task should have substeps list"""
        from backend.agent.orchestrator import OrchestratedTask
        
        task = OrchestratedTask(
            id="test-task",
            user_id="user-1",
            title="Test"
        )
        
        assert hasattr(task, 'substeps')
        assert isinstance(task.substeps, list)
    
    def test_task_has_progress_percent(self):
        """Task should have progress_percent field"""
        from backend.agent.orchestrator import OrchestratedTask
        
        task = OrchestratedTask(
            id="test-task",
            user_id="user-1",
            title="Test"
        )
        
        assert hasattr(task, 'progress_percent')
        assert task.progress_percent == 0


# =============================================================================
# Substep Tests
# =============================================================================

class TestSubstep:
    """Test Substep dataclass"""
    
    def test_substep_exists(self):
        """Substep class should exist"""
        from backend.agent.orchestrator import Substep
        assert Substep is not None
    
    def test_substep_has_required_fields(self):
        """Substep should have required fields"""
        from backend.agent.orchestrator import Substep, SubstepStatus
        
        step = Substep(
            id="step-1",
            step_number=1,
            title="First Step"
        )
        
        assert step.id == "step-1"
        assert step.step_number == 1
        assert step.title == "First Step"
        assert step.status == SubstepStatus.PENDING
    
    def test_substep_has_progress_weight(self):
        """Substep should have progress_weight"""
        from backend.agent.orchestrator import Substep
        
        step = Substep(
            id="step-1",
            step_number=1,
            title="First Step"
        )
        
        assert hasattr(step, 'progress_weight')
        assert step.progress_weight > 0


# =============================================================================
# Progress Calculation Tests
# =============================================================================

class TestProgressCalculation:
    """Test progress calculation logic"""
    
    def test_task_has_calculate_progress_method(self):
        """Task should have calculate_progress method"""
        from backend.agent.orchestrator import OrchestratedTask
        
        task = OrchestratedTask(
            id="test-task",
            user_id="user-1",
            title="Test"
        )
        
        assert hasattr(task, 'calculate_progress')
    
    def test_empty_task_progress_is_zero(self):
        """Empty task (no substeps) should have 0% progress"""
        from backend.agent.orchestrator import OrchestratedTask
        
        task = OrchestratedTask(
            id="test-task",
            user_id="user-1",
            title="Test"
        )
        
        assert task.calculate_progress() == 0
    
    def test_completed_substeps_increase_progress(self):
        """Completed substeps should increase progress"""
        from backend.agent.orchestrator import OrchestratedTask, Substep, SubstepStatus
        
        task = OrchestratedTask(
            id="test-task",
            user_id="user-1",
            title="Test"
        )
        
        # Add two substeps with equal weight
        task.substeps = [
            Substep(id="step-1", step_number=1, title="Step 1", progress_weight=50),
            Substep(id="step-2", step_number=2, title="Step 2", progress_weight=50)
        ]
        
        # Complete first step
        task.substeps[0].status = SubstepStatus.COMPLETED
        
        progress = task.calculate_progress()
        assert progress == 50
    
    def test_all_completed_gives_100_percent(self):
        """All completed substeps should give 100% progress"""
        from backend.agent.orchestrator import OrchestratedTask, Substep, SubstepStatus
        
        task = OrchestratedTask(
            id="test-task",
            user_id="user-1",
            title="Test"
        )
        
        task.substeps = [
            Substep(id="step-1", step_number=1, title="Step 1", progress_weight=50, status=SubstepStatus.COMPLETED),
            Substep(id="step-2", step_number=2, title="Step 2", progress_weight=50, status=SubstepStatus.COMPLETED)
        ]
        
        progress = task.calculate_progress()
        assert progress == 100


# =============================================================================
# Task Serialization Tests
# =============================================================================

class TestTaskSerialization:
    """Test task serialization"""
    
    def test_task_has_to_dict_method(self):
        """Task should have to_dict method"""
        from backend.agent.orchestrator import OrchestratedTask
        
        task = OrchestratedTask(
            id="test-task",
            user_id="user-1",
            title="Test"
        )
        
        assert hasattr(task, 'to_dict')
    
    def test_to_dict_includes_status(self):
        """to_dict should include status"""
        from backend.agent.orchestrator import OrchestratedTask
        
        task = OrchestratedTask(
            id="test-task",
            user_id="user-1",
            title="Test"
        )
        
        data = task.to_dict()
        assert 'status' in data
        assert data['status'] == 'pending'
    
    def test_substep_has_to_dict_method(self):
        """Substep should have to_dict method"""
        from backend.agent.orchestrator import Substep
        
        step = Substep(
            id="step-1",
            step_number=1,
            title="Step 1"
        )
        
        assert hasattr(step, 'to_dict')
        data = step.to_dict()
        assert 'status' in data


# =============================================================================
# Orchestrator Tests
# =============================================================================

class TestOrchestrator:
    """Test TaskOrchestrator class"""
    
    def test_orchestrator_exists(self):
        """TaskOrchestrator class should exist"""
        from backend.agent.orchestrator import TaskOrchestrator
        assert TaskOrchestrator is not None
    
    def test_get_orchestrator_function_exists(self):
        """get_orchestrator function should exist"""
        from backend.agent.orchestrator import get_orchestrator
        assert get_orchestrator is not None


# =============================================================================
# State Transition Tests
# =============================================================================

class TestStateTransitions:
    """Test valid state transitions"""
    
    def test_pending_to_in_progress(self):
        """Should be able to transition from PENDING to IN_PROGRESS"""
        from backend.agent.orchestrator import OrchestratedTask, TaskStatus
        
        task = OrchestratedTask(
            id="test-task",
            user_id="user-1",
            title="Test"
        )
        
        assert task.status == TaskStatus.PENDING
        task.status = TaskStatus.IN_PROGRESS
        assert task.status == TaskStatus.IN_PROGRESS
    
    def test_in_progress_to_completed(self):
        """Should be able to transition from IN_PROGRESS to COMPLETED"""
        from backend.agent.orchestrator import OrchestratedTask, TaskStatus
        
        task = OrchestratedTask(
            id="test-task",
            user_id="user-1",
            title="Test",
            status=TaskStatus.IN_PROGRESS
        )
        
        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED
    
    def test_in_progress_to_failed(self):
        """Should be able to transition from IN_PROGRESS to FAILED"""
        from backend.agent.orchestrator import OrchestratedTask, TaskStatus
        
        task = OrchestratedTask(
            id="test-task",
            user_id="user-1",
            title="Test",
            status=TaskStatus.IN_PROGRESS
        )
        
        task.status = TaskStatus.FAILED
        assert task.status == TaskStatus.FAILED
