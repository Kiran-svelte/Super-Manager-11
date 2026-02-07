"""
Task Orchestrator - Manages complex multi-step tasks with progress tracking
============================================================================

This orchestrator:
1. Breaks down user requests into subtasks
2. Executes subtasks in order (with dependencies)
3. Tracks progress in real-time
4. Schedules future actions (reminders)
5. Detects external events (meeting joins)
6. Sends notifications on progress updates
"""

import os
import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://hpqmcdygbjdmvxfmvucf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubstepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"  # Waiting for external event


class DetectionType(Enum):
    IMMEDIATE = "immediate"  # Execute immediately
    SCHEDULED = "scheduled"  # Execute at specific time
    WEBHOOK = "webhook"      # Wait for webhook callback
    POLLING = "polling"      # Periodically check status
    MANUAL = "manual"        # User must confirm


@dataclass
class Substep:
    """A single step within a task"""
    id: str
    step_number: int
    title: str
    description: str = ""
    status: SubstepStatus = SubstepStatus.PENDING
    progress_weight: int = 10  # Contribution to total progress
    action_type: str = ""  # What action to execute
    action_params: Dict = field(default_factory=dict)
    result: Dict = field(default_factory=dict)
    error_message: str = ""
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    detection_type: DetectionType = DetectionType.IMMEDIATE
    detection_config: Dict = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "step_number": self.step_number,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "progress_weight": self.progress_weight,
            "action_type": self.action_type,
            "action_params": self.action_params,
            "result": self.result,
            "error_message": self.error_message,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "detection_type": self.detection_type.value,
            "detection_config": self.detection_config,
            "depends_on": self.depends_on
        }


@dataclass
class OrchestratedTask:
    """A task with multiple substeps and progress tracking"""
    id: str
    user_id: str
    title: str
    description: str = ""
    task_type: str = "general"
    status: TaskStatus = TaskStatus.PENDING
    progress_percent: int = 0
    substeps: List[Substep] = field(default_factory=list)
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    started_at: Optional[datetime] = None
    needs_user_input: bool = False
    input_prompt: str = ""
    input_options: List[str] = field(default_factory=list)
    user_input_received: Any = None
    meeting_id: Optional[str] = None
    message_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def calculate_progress(self) -> int:
        """Calculate progress based on completed substeps"""
        if not self.substeps:
            return 0
        
        total_weight = sum(s.progress_weight for s in self.substeps)
        if total_weight == 0:
            return 0
        
        completed_weight = sum(
            s.progress_weight for s in self.substeps 
            if s.status == SubstepStatus.COMPLETED
        )
        
        return int((completed_weight / total_weight) * 100)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "substeps": [s.to_dict() for s in self.substeps],
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "actual_completion": self.actual_completion.isoformat() if self.actual_completion else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "needs_user_input": self.needs_user_input,
            "input_prompt": self.input_prompt,
            "input_options": self.input_options,
            "user_input_received": self.user_input_received,
            "meeting_id": self.meeting_id,
            "message_id": self.message_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


# =============================================================================
# TASK TEMPLATES - Pre-defined task structures
# =============================================================================

TASK_TEMPLATES = {
    "schedule_meeting": {
        "title_template": "Meeting: {title}",
        "substeps": [
            {"title": "Parse meeting request", "weight": 5, "action": "parse_request", "detection": "immediate"},
            {"title": "Create meeting link", "weight": 10, "action": "create_meeting_link", "detection": "immediate"},
            {"title": "Save to database", "weight": 5, "action": "save_meeting", "detection": "immediate"},
            {"title": "Send invite email", "weight": 20, "action": "send_invite_email", "detection": "immediate"},
            {"title": "Create calendar event", "weight": 10, "action": "create_calendar_event", "detection": "immediate"},
            {"title": "Send 1hr reminder", "weight": 10, "action": "send_reminder", "detection": "scheduled", "offset_minutes": -60},
            {"title": "Send 10min reminder", "weight": 10, "action": "send_reminder", "detection": "scheduled", "offset_minutes": -10},
            {"title": "Participant joins", "weight": 15, "action": "detect_join", "detection": "webhook"},
            {"title": "Meeting completes", "weight": 15, "action": "detect_completion", "detection": "webhook"},
        ]
    },
    "send_email": {
        "title_template": "Email: {subject}",
        "substeps": [
            {"title": "Compose email", "weight": 20, "action": "compose_email", "detection": "immediate"},
            {"title": "Send email", "weight": 60, "action": "send_email", "detection": "immediate"},
            {"title": "Confirm delivery", "weight": 20, "action": "confirm_delivery", "detection": "immediate"},
        ]
    },
    "set_reminder": {
        "title_template": "Reminder: {title}",
        "substeps": [
            {"title": "Schedule reminder", "weight": 30, "action": "schedule_reminder", "detection": "immediate"},
            {"title": "Send reminder", "weight": 70, "action": "send_reminder", "detection": "scheduled"},
        ]
    },
    "research": {
        "title_template": "Research: {topic}",
        "substeps": [
            {"title": "Search web", "weight": 40, "action": "web_search", "detection": "immediate"},
            {"title": "Analyze results", "weight": 40, "action": "analyze_results", "detection": "immediate"},
            {"title": "Compile report", "weight": 20, "action": "compile_report", "detection": "immediate"},
        ]
    }
}


# =============================================================================
# TASK ORCHESTRATOR
# =============================================================================

class TaskOrchestrator:
    """
    Manages complex tasks with multiple steps and progress tracking.
    
    Features:
    - Creates tasks from templates
    - Executes substeps in order
    - Handles dependencies between substeps
    - Schedules future actions
    - Tracks progress in real-time
    - Persists to Supabase
    - Sends WebSocket updates
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.action_handlers: Dict[str, Callable] = {}
        self.ws_manager = None  # WebSocket for real-time updates
        
        # Initialize Supabase
        if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
            try:
                self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("[ORCHESTRATOR] Connected to Supabase")
            except Exception as e:
                print(f"[ORCHESTRATOR] Supabase connection failed: {e}")
        
        # In-memory cache for active tasks
        self.active_tasks: Dict[str, OrchestratedTask] = {}
    
    def register_action(self, action_name: str, handler: Callable):
        """Register an action handler"""
        self.action_handlers[action_name] = handler
    
    def set_ws_manager(self, manager):
        """Set WebSocket manager for real-time updates"""
        self.ws_manager = manager
    
    async def create_task(
        self,
        user_id: str,
        task_type: str,
        params: Dict,
        meeting_start_time: Optional[datetime] = None
    ) -> OrchestratedTask:
        """Create a new orchestrated task from a template"""
        
        template = TASK_TEMPLATES.get(task_type, TASK_TEMPLATES["send_email"])
        task_id = str(uuid.uuid4())
        
        # Format title
        title = template["title_template"].format(**params) if "title_template" in template else params.get("title", "Task")
        
        # Create substeps
        substeps = []
        for i, step_def in enumerate(template["substeps"]):
            substep_id = str(uuid.uuid4())
            
            # Calculate scheduled time for scheduled steps
            scheduled_at = None
            if step_def.get("detection") == "scheduled" and meeting_start_time:
                offset = step_def.get("offset_minutes", 0)
                scheduled_at = meeting_start_time + timedelta(minutes=offset)
            
            substep = Substep(
                id=substep_id,
                step_number=i + 1,
                title=step_def["title"],
                progress_weight=step_def.get("weight", 10),
                action_type=step_def.get("action", ""),
                action_params=params,
                detection_type=DetectionType(step_def.get("detection", "immediate")),
                scheduled_at=scheduled_at
            )
            substeps.append(substep)
        
        # Calculate estimated completion
        estimated_completion = None
        if meeting_start_time:
            # For meetings, completion is when meeting ends (assume 30 min duration)
            duration = params.get("duration_minutes", 30)
            estimated_completion = meeting_start_time + timedelta(minutes=duration)
        
        # Create task
        task = OrchestratedTask(
            id=task_id,
            user_id=user_id,
            title=title,
            description=params.get("description", ""),
            task_type=task_type,
            substeps=substeps,
            estimated_completion=estimated_completion,
            meeting_id=params.get("meeting_id"),
            metadata=params
        )
        
        # Save to database
        await self._save_task(task)
        
        # Cache locally
        self.active_tasks[task_id] = task
        
        # Send WebSocket update
        await self._notify_task_update(task)
        
        return task
    
    async def execute_task(self, task_id: str) -> OrchestratedTask:
        """Execute all immediate substeps of a task"""
        
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        
        for substep in task.substeps:
            # Skip if not immediate execution
            if substep.detection_type != DetectionType.IMMEDIATE:
                continue
            
            # Skip if already completed
            if substep.status == SubstepStatus.COMPLETED:
                continue
            
            # Check dependencies
            if not self._check_dependencies(task, substep):
                continue
            
            # Execute the substep
            await self._execute_substep(task, substep)
            
            # Update progress
            task.progress_percent = task.calculate_progress()
            await self._save_task(task)
            await self._notify_task_update(task)
        
        # Check if all immediate steps are done
        immediate_steps = [s for s in task.substeps if s.detection_type == DetectionType.IMMEDIATE]
        if all(s.status == SubstepStatus.COMPLETED for s in immediate_steps):
            # Schedule future steps
            await self._schedule_future_steps(task)
        
        return task
    
    async def _execute_substep(self, task: OrchestratedTask, substep: Substep):
        """Execute a single substep"""
        
        substep.status = SubstepStatus.IN_PROGRESS
        substep.started_at = datetime.now()
        
        try:
            # Get handler
            handler = self.action_handlers.get(substep.action_type)
            
            if handler:
                # Execute action
                result = await handler(substep.action_params)
                substep.result = result if isinstance(result, dict) else {"result": result}
                substep.status = SubstepStatus.COMPLETED
            else:
                # No handler - mark as completed (placeholder)
                substep.result = {"message": f"Action {substep.action_type} executed"}
                substep.status = SubstepStatus.COMPLETED
            
            substep.completed_at = datetime.now()
            
        except Exception as e:
            substep.status = SubstepStatus.FAILED
            substep.error_message = str(e)
            print(f"[ORCHESTRATOR] Substep {substep.title} failed: {e}")
    
    def _check_dependencies(self, task: OrchestratedTask, substep: Substep) -> bool:
        """Check if all dependencies are completed"""
        if not substep.depends_on:
            return True
        
        for dep_id in substep.depends_on:
            dep_step = next((s for s in task.substeps if s.id == dep_id), None)
            if dep_step and dep_step.status != SubstepStatus.COMPLETED:
                return False
        
        return True
    
    async def _schedule_future_steps(self, task: OrchestratedTask):
        """Schedule substeps that need to run later"""
        
        for substep in task.substeps:
            if substep.detection_type == DetectionType.SCHEDULED and substep.scheduled_at:
                # Create scheduled job
                await self._create_scheduled_job(
                    job_type="execute_substep",
                    scheduled_for=substep.scheduled_at,
                    job_params={
                        "task_id": task.id,
                        "substep_id": substep.id,
                        "user_id": task.user_id
                    },
                    task_id=task.id,
                    substep_id=substep.id,
                    user_id=task.user_id
                )
                print(f"[ORCHESTRATOR] Scheduled: {substep.title} at {substep.scheduled_at}")
    
    async def complete_substep(
        self, 
        task_id: str, 
        substep_id: str, 
        result: Dict = None
    ) -> OrchestratedTask:
        """Mark a substep as completed (called by webhooks, polling, etc.)"""
        
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        substep = next((s for s in task.substeps if s.id == substep_id), None)
        if not substep:
            raise ValueError(f"Substep {substep_id} not found")
        
        substep.status = SubstepStatus.COMPLETED
        substep.completed_at = datetime.now()
        substep.result = result or {}
        
        # Update task progress
        task.progress_percent = task.calculate_progress()
        
        # Check if task is complete
        if task.progress_percent == 100:
            task.status = TaskStatus.COMPLETED
            task.actual_completion = datetime.now()
        
        # Save and notify
        await self._save_task(task)
        await self._notify_task_update(task)
        
        # Send notification
        await self._send_notification(
            user_id=task.user_id,
            title=f"Task Update: {task.title}",
            body=f"{substep.title} completed. Progress: {task.progress_percent}%",
            task_id=task.id
        )
        
        return task
    
    async def get_task(self, task_id: str) -> Optional[OrchestratedTask]:
        """Get a task by ID"""
        
        # Check cache first
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        
        # Load from database
        if self.client:
            try:
                result = self.client.table("orchestrated_tasks").select("*").eq("id", task_id).execute()
                if result.data:
                    task_data = result.data[0]
                    
                    # Load substeps
                    substeps_result = self.client.table("task_substeps").select("*").eq("task_id", task_id).order("step_number").execute()
                    
                    substeps = []
                    for s in substeps_result.data or []:
                        substep = Substep(
                            id=s["id"],
                            step_number=s["step_number"],
                            title=s["title"],
                            description=s.get("description", ""),
                            status=SubstepStatus(s["status"]),
                            progress_weight=s.get("progress_weight", 10),
                            action_type=s.get("action_type", ""),
                            action_params=s.get("action_params", {}),
                            result=s.get("result", {}),
                            error_message=s.get("error_message", ""),
                            detection_type=DetectionType(s.get("detection_type", "immediate")),
                            detection_config=s.get("detection_config", {})
                        )
                        substeps.append(substep)
                    
                    task = OrchestratedTask(
                        id=task_data["id"],
                        user_id=task_data["user_id"],
                        title=task_data["title"],
                        description=task_data.get("description", ""),
                        task_type=task_data["task_type"],
                        status=TaskStatus(task_data["status"]),
                        progress_percent=task_data.get("progress_percent", 0),
                        substeps=substeps,
                        metadata=task_data.get("metadata", {})
                    )
                    
                    self.active_tasks[task_id] = task
                    return task
            except Exception as e:
                print(f"[ORCHESTRATOR] Error loading task: {e}")
        
        return None
    
    async def get_user_tasks(self, user_id: str, status: str = None) -> List[Dict]:
        """Get all tasks for a user"""
        
        if self.client:
            try:
                query = self.client.table("orchestrated_tasks").select("*").eq("user_id", user_id)
                if status:
                    query = query.eq("status", status)
                result = query.order("created_at", desc=True).execute()
                
                tasks = []
                for t in result.data or []:
                    # Get substeps
                    substeps_result = self.client.table("task_substeps").select("*").eq("task_id", t["id"]).order("step_number").execute()
                    t["substeps"] = substeps_result.data or []
                    tasks.append(t)
                
                return tasks
            except Exception as e:
                print(f"[ORCHESTRATOR] Error getting user tasks: {e}")
        
        # Return from cache
        return [t.to_dict() for t in self.active_tasks.values() if t.user_id == user_id]
    
    async def _save_task(self, task: OrchestratedTask):
        """Save task and substeps to database"""
        
        if not self.client:
            return
        
        try:
            # Save main task
            task_data = {
                "id": task.id,
                "user_id": task.user_id,
                "title": task.title,
                "description": task.description,
                "task_type": task.task_type,
                "status": task.status.value,
                "progress_percent": task.progress_percent,
                "estimated_completion": task.estimated_completion.isoformat() if task.estimated_completion else None,
                "actual_completion": task.actual_completion.isoformat() if task.actual_completion else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "needs_user_input": task.needs_user_input,
                "input_prompt": task.input_prompt,
                "input_options": task.input_options,
                "user_input_received": task.user_input_received,
                "meeting_id": task.meeting_id,
                "message_id": task.message_id,
                "metadata": task.metadata
            }
            
            self.client.table("orchestrated_tasks").upsert(task_data).execute()
            
            # Save substeps
            for substep in task.substeps:
                substep_data = {
                    "id": substep.id,
                    "task_id": task.id,
                    "step_number": substep.step_number,
                    "title": substep.title,
                    "description": substep.description,
                    "status": substep.status.value,
                    "progress_weight": substep.progress_weight,
                    "action_type": substep.action_type,
                    "action_params": substep.action_params,
                    "result": substep.result,
                    "error_message": substep.error_message,
                    "scheduled_at": substep.scheduled_at.isoformat() if substep.scheduled_at else None,
                    "started_at": substep.started_at.isoformat() if substep.started_at else None,
                    "completed_at": substep.completed_at.isoformat() if substep.completed_at else None,
                    "detection_type": substep.detection_type.value,
                    "detection_config": substep.detection_config,
                    "depends_on": substep.depends_on
                }
                
                self.client.table("task_substeps").upsert(substep_data).execute()
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Error saving task: {e}")
    
    async def _create_scheduled_job(
        self,
        job_type: str,
        scheduled_for: datetime,
        job_params: Dict,
        task_id: str = None,
        substep_id: str = None,
        user_id: str = None
    ):
        """Create a scheduled job in the database"""
        
        if not self.client:
            return
        
        try:
            job_data = {
                "id": str(uuid.uuid4()),
                "job_type": job_type,
                "job_params": job_params,
                "scheduled_for": scheduled_for.isoformat(),
                "status": "pending",
                "task_id": task_id,
                "substep_id": substep_id,
                "user_id": user_id
            }
            
            self.client.table("scheduled_jobs").insert(job_data).execute()
        except Exception as e:
            print(f"[ORCHESTRATOR] Error creating scheduled job: {e}")
    
    async def _notify_task_update(self, task: OrchestratedTask):
        """Send real-time update via WebSocket"""
        
        if self.ws_manager:
            await self.ws_manager.send_to_user(
                task.user_id,
                {
                    "type": "task_update",
                    "task": task.to_dict()
                }
            )
    
    async def _send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        task_id: str = None,
        priority: str = "normal"
    ):
        """Send a notification to the user"""
        
        if not self.client:
            return
        
        try:
            notification_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": title,
                "body": body,
                "notification_type": "task_update",
                "priority": priority,
                "task_id": task_id,
                "channels": ["in_app", "push"]
            }
            
            self.client.table("notifications").insert(notification_data).execute()
            
            # Also send via WebSocket
            if self.ws_manager:
                await self.ws_manager.send_to_user(
                    user_id,
                    {
                        "type": "notification",
                        "notification": notification_data
                    }
                )
        except Exception as e:
            print(f"[ORCHESTRATOR] Error sending notification: {e}")


# =============================================================================
# SINGLETON
# =============================================================================

_orchestrator: Optional[TaskOrchestrator] = None

def get_orchestrator() -> TaskOrchestrator:
    """Get the singleton TaskOrchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TaskOrchestrator()
    return _orchestrator
