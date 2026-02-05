"""
Dynamic Workflow Engine
AI-driven workflow planning that creates custom stages based on user intent
Instead of hardcoded flows, AI decides what steps are needed
"""
from __future__ import annotations

import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from ..ai_providers import get_ai_router, AIResponse


class StageType(Enum):
    """Types of workflow stages"""
    CLARIFICATION = "clarification"      # Ask for missing info
    SELECTION = "selection"              # Choose from options  
    MULTI_SELECT = "multi_select"        # Choose multiple options
    CONFIRMATION = "confirmation"        # Confirm before action
    EXECUTION = "execution"              # Execute plugin action
    PARALLEL = "parallel"                # Execute multiple in parallel
    CONDITIONAL = "conditional"          # Branch based on condition
    WAIT = "wait"                        # Wait for external event


class StageStatus(Enum):
    """Stage execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStage:
    """A single stage in a workflow"""
    id: str
    type: StageType
    name: str
    description: str
    status: StageStatus = StageStatus.PENDING
    
    # For selection stages
    options: List[Dict[str, Any]] = field(default_factory=list)
    allow_multiple: bool = False
    
    # For execution stages
    plugin: Optional[str] = None
    action: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Stage flow control
    dependencies: List[str] = field(default_factory=list)  # Stage IDs that must complete first
    condition: Optional[str] = None  # Condition expression for conditional stages
    
    # Results
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "options": self.options,
            "allow_multiple": self.allow_multiple,
            "plugin": self.plugin,
            "action": self.action,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "condition": self.condition,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStage":
        return cls(
            id=data["id"],
            type=StageType(data["type"]),
            name=data["name"],
            description=data["description"],
            status=StageStatus(data.get("status", "pending")),
            options=data.get("options", []),
            allow_multiple=data.get("allow_multiple", False),
            plugin=data.get("plugin"),
            action=data.get("action"),
            parameters=data.get("parameters", {}),
            dependencies=data.get("dependencies", []),
            condition=data.get("condition"),
            result=data.get("result"),
            error=data.get("error"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at")
        )


@dataclass
class Workflow:
    """A complete workflow with multiple stages"""
    id: str
    user_id: str
    intent: str
    original_input: str
    
    stages: List[WorkflowStage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)  # Accumulated data
    
    current_stage_index: int = 0
    status: str = "active"  # active, completed, failed, cancelled
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def get_current_stage(self) -> Optional[WorkflowStage]:
        """Get the stage currently awaiting action"""
        if self.current_stage_index < len(self.stages):
            return self.stages[self.current_stage_index]
        return None
    
    def advance_stage(self):
        """Move to next stage"""
        if self.current_stage_index < len(self.stages):
            self.current_stage_index += 1
            self.updated_at = datetime.utcnow().isoformat()
    
    def is_complete(self) -> bool:
        """Check if all stages are complete"""
        return all(s.status in [StageStatus.COMPLETED, StageStatus.SKIPPED] for s in self.stages)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "intent": self.intent,
            "original_input": self.original_input,
            "stages": [s.to_dict() for s in self.stages],
            "context": self.context,
            "current_stage_index": self.current_stage_index,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        workflow = cls(
            id=data["id"],
            user_id=data["user_id"],
            intent=data["intent"],
            original_input=data["original_input"],
            context=data.get("context", {}),
            current_stage_index=data.get("current_stage_index", 0),
            status=data.get("status", "active"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat())
        )
        workflow.stages = [WorkflowStage.from_dict(s) for s in data.get("stages", [])]
        return workflow


class DynamicWorkflowPlanner:
    """
    AI-powered workflow planner.
    Creates custom workflows based on user intent instead of hardcoded templates.
    """
    
    # Available plugins and their capabilities
    PLUGIN_CAPABILITIES = {
        "telegram": {
            "actions": ["send_message", "send_notification"],
            "description": "Send messages via Telegram"
        },
        "email": {
            "actions": ["send_email", "send_invitation"],
            "description": "Send emails with SMTP"
        },
        "meeting": {
            "actions": ["create_meeting", "schedule_call"],
            "description": "Create video meeting links (Jitsi, Google Meet)"
        },
        "calendar": {
            "actions": ["schedule_event", "check_availability", "list_events"],
            "description": "Calendar management"
        },
        "search": {
            "actions": ["search_web", "find_places", "search_flights", "search_hotels"],
            "description": "Search for information"
        },
        "booking": {
            "actions": ["book_hotel", "book_flight", "book_restaurant"],
            "description": "Make reservations"
        }
    }
    
    WORKFLOW_PLANNING_PROMPT = """You are a workflow planner for an AI assistant that executes real actions.

User's request: "{user_input}"
Parsed intent: {intent}

Available plugins and their capabilities:
{plugins}

Create a workflow to fulfill this request. Consider:
1. What information is missing that we need to ask the user?
2. What can be done in parallel vs sequential?
3. What needs user confirmation before executing?
4. What's the most efficient order of operations?

Return a JSON object with this structure:
{{
    "workflow_name": "Short descriptive name",
    "stages": [
        {{
            "type": "clarification|selection|multi_select|execution|confirmation",
            "name": "Stage name",
            "description": "What this stage does",
            "options": [  // For selection stages
                {{"id": "opt1", "name": "Option 1", "description": "..."}},
            ],
            "allow_multiple": false,  // For multi_select
            "plugin": "plugin_name",  // For execution stages
            "action": "action_name",
            "parameters": {{}},  // Parameters for the action
            "dependencies": [],  // Stage indices that must complete first
            "requires_confirmation": true  // If user should confirm
        }}
    ],
    "estimated_time": "X minutes"
}}

Be specific and practical. Only include stages that are actually needed.
"""

    def __init__(self):
        self._ai_router = None
    
    @property
    def ai_router(self):
        if self._ai_router is None:
            self._ai_router = get_ai_router()
        return self._ai_router
    
    async def create_workflow(
        self,
        user_input: str,
        intent: Dict[str, Any],
        user_id: str
    ) -> Workflow:
        """
        Create a dynamic workflow based on user intent.
        Uses AI to plan the optimal sequence of stages.
        """
        
        # Format plugin capabilities for the prompt
        plugins_str = "\n".join([
            f"- {name}: {info['description']}\n  Actions: {', '.join(info['actions'])}"
            for name, info in self.PLUGIN_CAPABILITIES.items()
        ])
        
        # Build the planning prompt
        prompt = self.WORKFLOW_PLANNING_PROMPT.format(
            user_input=user_input,
            intent=json.dumps(intent, indent=2),
            plugins=plugins_str
        )
        
        try:
            # Get workflow plan from AI
            response = await self.ai_router.generate(
                messages=[
                    {"role": "system", "content": "You are a precise workflow planner. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                json_mode=True,
                temperature=0.3  # Lower temperature for more consistent planning
            )
            
            if isinstance(response, AIResponse):
                plan_data = json.loads(response.content)
            else:
                # Streaming - collect all
                chunks = []
                async for chunk in response:
                    chunks.append(chunk)
                plan_data = json.loads("".join(chunks))
            
            # Build workflow from AI plan
            workflow = self._build_workflow_from_plan(
                plan_data=plan_data,
                user_input=user_input,
                intent=intent,
                user_id=user_id
            )
            
            return workflow
            
        except Exception as e:
            print(f"[WORKFLOW] AI planning failed: {e}")
            # Fallback to simple default workflow
            return self._create_fallback_workflow(user_input, intent, user_id)
    
    def _build_workflow_from_plan(
        self,
        plan_data: Dict[str, Any],
        user_input: str,
        intent: Dict[str, Any],
        user_id: str
    ) -> Workflow:
        """Build a Workflow object from AI-generated plan"""
        
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            id=workflow_id,
            user_id=user_id,
            intent=intent.get("type", "general"),
            original_input=user_input,
            context={"intent_data": intent}
        )
        
        # Convert plan stages to WorkflowStage objects
        for i, stage_data in enumerate(plan_data.get("stages", [])):
            stage_type = StageType(stage_data.get("type", "execution"))
            
            stage = WorkflowStage(
                id=f"{workflow_id}_stage_{i}",
                type=stage_type,
                name=stage_data.get("name", f"Stage {i+1}"),
                description=stage_data.get("description", ""),
                options=stage_data.get("options", []),
                allow_multiple=stage_data.get("allow_multiple", False),
                plugin=stage_data.get("plugin"),
                action=stage_data.get("action"),
                parameters=stage_data.get("parameters", {}),
                dependencies=[f"{workflow_id}_stage_{d}" for d in stage_data.get("dependencies", [])]
            )
            
            # Add confirmation stage if needed
            if stage_data.get("requires_confirmation") and stage_type == StageType.EXECUTION:
                # Insert confirmation before execution
                confirm_stage = WorkflowStage(
                    id=f"{workflow_id}_confirm_{i}",
                    type=StageType.CONFIRMATION,
                    name=f"Confirm {stage.name}",
                    description=f"Confirm before: {stage.description}",
                    dependencies=[s.id for s in workflow.stages] if workflow.stages else []
                )
                workflow.stages.append(confirm_stage)
                stage.dependencies.append(confirm_stage.id)
            
            workflow.stages.append(stage)
        
        return workflow
    
    def _create_fallback_workflow(
        self,
        user_input: str,
        intent: Dict[str, Any],
        user_id: str
    ) -> Workflow:
        """Create a simple fallback workflow when AI planning fails"""
        
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            id=workflow_id,
            user_id=user_id,
            intent=intent.get("type", "general"),
            original_input=user_input,
            context={"intent_data": intent, "fallback": True}
        )
        
        # Simple clarification -> confirmation -> response flow
        workflow.stages = [
            WorkflowStage(
                id=f"{workflow_id}_clarify",
                type=StageType.CLARIFICATION,
                name="Clarify Request",
                description="Please provide more details about your request"
            ),
            WorkflowStage(
                id=f"{workflow_id}_confirm",
                type=StageType.CONFIRMATION,
                name="Confirm Action",
                description="Confirm you want to proceed"
            )
        ]
        
        return workflow
    
    async def generate_stage_options(
        self,
        workflow: Workflow,
        stage: WorkflowStage
    ) -> List[Dict[str, Any]]:
        """
        Dynamically generate options for a selection stage using AI.
        """
        if stage.options:
            return stage.options
        
        prompt = f"""Generate options for the user to select from.

Context:
- Original request: {workflow.original_input}
- Current stage: {stage.name}
- Stage description: {stage.description}
- Collected data so far: {json.dumps(workflow.context)}

Generate 3-5 specific, relevant options. Return JSON array:
[
    {{"id": "option_id", "name": "Option Name", "description": "Brief description", "metadata": {{}}}}
]
"""
        
        try:
            response = await self.ai_router.generate(
                messages=[
                    {"role": "system", "content": "Generate helpful selection options. Return only valid JSON array."},
                    {"role": "user", "content": prompt}
                ],
                json_mode=True,
                temperature=0.7
            )
            
            if isinstance(response, AIResponse):
                options = json.loads(response.content)
            else:
                chunks = []
                async for chunk in response:
                    chunks.append(chunk)
                options = json.loads("".join(chunks))
            
            # Ensure it's a list
            if isinstance(options, dict) and "options" in options:
                options = options["options"]
            
            stage.options = options
            return options
            
        except Exception as e:
            print(f"[WORKFLOW] Option generation failed: {e}")
            return []


# Singleton planner
_workflow_planner: Optional[DynamicWorkflowPlanner] = None


def get_workflow_planner() -> DynamicWorkflowPlanner:
    """Get workflow planner singleton"""
    global _workflow_planner
    if _workflow_planner is None:
        _workflow_planner = DynamicWorkflowPlanner()
    return _workflow_planner
