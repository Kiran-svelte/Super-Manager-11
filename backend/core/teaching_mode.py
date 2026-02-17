"""
Teaching Mode - User-Taught Workflow System
============================================
v6 NEW - Record user actions and create reusable workflows.

Features:
- Record user interactions (clicks, fills, navigation)
- Analyze recordings to extract workflow patterns
- Save workflows with parameters
- Replay workflows with different inputs
- Register workflows as tools in ToolRegistry

Workflow naming: workflow__{name}
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime

from .primitives import PrimitiveResult

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """
    Single action in a workflow.
    
    Action types:
    - navigate: Go to URL
    - click: Click element
    - fill: Fill input field
    - wait: Wait for duration
    - screenshot: Take screenshot
    - extract: Extract data from page
    """
    action: str  # "navigate", "click", "fill", "wait", "screenshot", "extract"
    selector: str = ""  # CSS selector (if applicable)
    value: str = ""  # Value to fill or extract (if applicable)
    wait_ms: int = 0  # Wait duration in milliseconds
    url: str = ""  # URL for navigate action
    description: str = ""  # Human-readable description
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowDef:
    """
    Complete workflow definition.
    
    Parameters are placeholders like {{email}}, {{name}} that can be replaced
    during replay with user-provided values.
    """
    name: str
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)  # e.g., ["email", "name"]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    success_count: int = 0  # Number of successful replays
    failure_count: int = 0  # Number of failed replays
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "parameters": self.parameters,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowDef":
        steps = [WorkflowStep(**step) for step in data.get("steps", [])]
        return cls(
            name=data["name"],
            description=data["description"],
            steps=steps,
            parameters=data.get("parameters", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
        )


class TeachingMode:
    """
    Workflow recording and replay system.
    """
    
    def __init__(self, storage_path: str = "workflows.json"):
        self.storage_path = storage_path
        self.active_recordings: Dict[str, List[Dict[str, Any]]] = {}
        self.workflows: Dict[str, WorkflowDef] = {}
        self._load_workflows()
    
    def _load_workflows(self):
        """Load saved workflows from storage"""
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                for name, workflow_data in data.items():
                    self.workflows[name] = WorkflowDef.from_dict(workflow_data)
            logger.info(f"Loaded {len(self.workflows)} workflows from {self.storage_path}")
        except FileNotFoundError:
            logger.info(f"No workflows file found at {self.storage_path}, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load workflows: {e}")
    
    def _save_workflows(self):
        """Save workflows to storage"""
        try:
            data = {name: workflow.to_dict() for name, workflow in self.workflows.items()}
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.workflows)} workflows to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save workflows: {e}")
    
    async def start_recording(self, session_id: str) -> Dict[str, Any]:
        """
        Start recording user actions.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            Dict with recording_id and status
        """
        if session_id in self.active_recordings:
            return {
                "success": False,
                "error": "Recording already active for this session",
            }
        
        self.active_recordings[session_id] = []
        logger.info(f"Started recording for session {session_id}")
        
        return {
            "success": True,
            "recording_id": session_id,
            "status": "recording",
            "message": "Recording started. Perform your actions in the browser.",
        }
    
    async def stop_recording(self, session_id: str, actions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Stop recording and save actions.
        
        Args:
            session_id: Session identifier
            actions: Optional list of actions (if provided, replaces recorded actions)
        
        Returns:
            Dict with recorded actions and status
        """
        if session_id not in self.active_recordings and not actions:
            return {
                "success": False,
                "error": "No active recording for this session",
            }
        
        if actions:
            recorded_actions = actions
        else:
            recorded_actions = self.active_recordings.get(session_id, [])
            del self.active_recordings[session_id]
        
        logger.info(f"Stopped recording for session {session_id}, captured {len(recorded_actions)} actions")
        
        return {
            "success": True,
            "recording_id": session_id,
            "action_count": len(recorded_actions),
            "actions": recorded_actions,
            "message": f"Recording stopped. Captured {len(recorded_actions)} actions.",
        }
    
    async def analyze_recording(self, actions: List[Dict[str, Any]]) -> WorkflowDef:
        """
        Analyze recorded actions and extract workflow pattern.
        
        Args:
            actions: List of recorded actions
        
        Returns:
            WorkflowDef extracted from actions
        """
        if not actions:
            raise ValueError("No actions to analyze")
        
        steps = []
        parameters = set()
        
        for action in actions:
            action_type = action.get("type", "")
            
            if action_type == "navigate":
                steps.append(WorkflowStep(
                    action="navigate",
                    url=action.get("url", ""),
                    description=f"Navigate to {action.get('url', '')}",
                ))
            
            elif action_type == "click":
                steps.append(WorkflowStep(
                    action="click",
                    selector=action.get("selector", ""),
                    description=f"Click {action.get('selector', '')}",
                ))
            
            elif action_type == "fill":
                value = action.get("value", "")
                selector = action.get("selector", "")
                
                # Check if value should be parameterized
                if self._should_parameterize(value):
                    param_name = self._extract_parameter_name(selector)
                    parameters.add(param_name)
                    value = f"{{{{{param_name}}}}}"  # {{param_name}}
                
                steps.append(WorkflowStep(
                    action="fill",
                    selector=selector,
                    value=value,
                    description=f"Fill {selector}",
                ))
            
            elif action_type == "wait":
                steps.append(WorkflowStep(
                    action="wait",
                    wait_ms=action.get("duration_ms", 1000),
                    description=f"Wait {action.get('duration_ms', 1000)}ms",
                ))
            
            elif action_type == "screenshot":
                steps.append(WorkflowStep(
                    action="screenshot",
                    description="Take screenshot",
                ))
            
            elif action_type == "extract":
                steps.append(WorkflowStep(
                    action="extract",
                    selector=action.get("selector", ""),
                    description=f"Extract data from {action.get('selector', '')}",
                ))
        
        # Generate workflow name and description
        workflow_name = self._generate_workflow_name(steps)
        workflow_description = self._generate_workflow_description(steps)
        
        workflow = WorkflowDef(
            name=workflow_name,
            description=workflow_description,
            steps=steps,
            parameters=list(parameters),
        )
        
        logger.info(f"Analyzed recording into workflow: {workflow_name} with {len(steps)} steps")
        
        return workflow
    
    def _should_parameterize(self, value: str) -> bool:
        """Check if a value should be parameterized (replaced with {{param}})"""
        # Parameterize if value looks like:
        # - Email address
        # - Name (multiple words)
        # - Phone number
        # - Long text (>20 chars)
        if not value:
            return False
        
        if "@" in value:  # Email
            return True
        if len(value.split()) > 1:  # Multiple words (name)
            return True
        if len(value) > 20:  # Long text
            return True
        if value.replace("-", "").replace(" ", "").isdigit():  # Phone
            return True
        
        return False
    
    def _extract_parameter_name(self, selector: str) -> str:
        """Extract parameter name from selector (e.g., #email → email)"""
        # Try to extract from selector
        if "#" in selector:
            return selector.split("#")[1].split(".")[0].split("[")[0]
        if 'name="' in selector or "name='" in selector:
            # Extract name attribute value
            import re
            match = re.search(r'name=["\']([^"\']+)["\']', selector)
            if match:
                return match.group(1)
        
        # Default to generic names
        return "input_value"
    
    def _generate_workflow_name(self, steps: List[WorkflowStep]) -> str:
        """Generate a workflow name from steps"""
        # Extract key actions
        actions = [step.action for step in steps]
        
        if "navigate" in actions and "fill" in actions:
            return "form_fill_workflow"
        elif "navigate" in actions and "extract" in actions:
            return "data_extraction_workflow"
        elif "click" in actions and "fill" in actions:
            return "interactive_form_workflow"
        else:
            return f"custom_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _generate_workflow_description(self, steps: List[WorkflowStep]) -> str:
        """Generate a workflow description from steps"""
        step_summaries = []
        for step in steps[:5]:  # First 5 steps
            step_summaries.append(step.description)
        
        description = " → ".join(step_summaries)
        if len(steps) > 5:
            description += f" ... ({len(steps) - 5} more steps)"
        
        return description
    
    async def save_workflow(self, name: str, workflow: WorkflowDef) -> None:
        """
        Save a workflow.
        
        Args:
            name: Workflow name (used as key)
            workflow: WorkflowDef to save
        """
        workflow.name = name
        workflow.updated_at = datetime.now().isoformat()
        
        self.workflows[name] = workflow
        self._save_workflows()
        
        # Register as tool in ToolRegistry
        await self._register_workflow_tool(workflow)
        
        logger.info(f"Saved workflow: {name}")
    
    async def _register_workflow_tool(self, workflow: WorkflowDef):
        """Register workflow as a tool in ToolRegistry"""
        try:
            from .tool_registry import get_tool_registry, ToolDef
            
            registry = get_tool_registry()
            
            # Create handler function for this workflow
            async def workflow_handler(**params) -> PrimitiveResult:
                return await self.replay_workflow(workflow.name, params)
            
            tool_name = f"workflow__{workflow.name}"
            
            # Build parameters schema
            parameters = {}
            for param in workflow.parameters:
                parameters[param] = {"type": "string", "description": f"Value for {param}"}
            
            # Determine risk level based on workflow actions
            risky_actions = ["fill", "click"]
            risk_level = "risky" if any(step.action in risky_actions for step in workflow.steps) else "safe"
            
            tool = ToolDef(
                name=tool_name,
                description=workflow.description,
                parameters=parameters,
                risk_level=risk_level,
                source="workflow",
                handler=workflow_handler,
            )
            
            registry.register(tool)
            logger.info(f"Registered workflow tool: {tool_name}")
        
        except Exception as e:
            logger.error(f"Failed to register workflow tool: {e}")
    
    async def replay_workflow(self, name: str, params: Dict[str, Any]) -> PrimitiveResult:
        """
        Replay a saved workflow with given parameters.
        
        Args:
            name: Workflow name
            params: Parameter values (e.g., {"email": "test@example.com"})
        
        Returns:
            PrimitiveResult with replay status
        """
        if name not in self.workflows:
            return PrimitiveResult(
                success=False,
                output=f"Workflow '{name}' not found. Available workflows: {', '.join(self.workflows.keys())}",
                error="workflow_not_found",
            )
        
        workflow = self.workflows[name]
        
        # Validate parameters
        missing_params = [p for p in workflow.parameters if p not in params]
        if missing_params:
            return PrimitiveResult(
                success=False,
                output=f"Missing required parameters: {', '.join(missing_params)}",
                error="missing_parameters",
            )
        
        try:
            # Use stealth browser for replay
            from .stealth_browser import StealthBrowser
            
            browser = StealthBrowser()
            await browser.launch()
            
            results = []
            
            for step in workflow.steps:
                # Replace parameters in values
                value = step.value
                for param_name, param_value in params.items():
                    value = value.replace(f"{{{{{param_name}}}}}", str(param_value))
                
                if step.action == "navigate":
                    await browser.navigate(step.url)
                    results.append(f"Navigated to {step.url}")
                
                elif step.action == "click":
                    element = await browser.page.query_selector(step.selector)
                    if element:
                        await element.click()
                        results.append(f"Clicked {step.selector}")
                    else:
                        results.append(f"Failed to click {step.selector} (not found)")
                
                elif step.action == "fill":
                    element = await browser.page.query_selector(step.selector)
                    if element:
                        await element.fill(value)
                        results.append(f"Filled {step.selector} = {value}")
                    else:
                        results.append(f"Failed to fill {step.selector} (not found)")
                
                elif step.action == "wait":
                    await browser.page.wait_for_timeout(step.wait_ms)
                    results.append(f"Waited {step.wait_ms}ms")
                
                elif step.action == "screenshot":
                    screenshot = await browser.screenshot()
                    results.append(f"Screenshot captured ({len(screenshot)} bytes)")
                
                elif step.action == "extract":
                    element = await browser.page.query_selector(step.selector)
                    if element:
                        extracted = await element.text_content()
                        results.append(f"Extracted from {step.selector}: {extracted}")
                    else:
                        results.append(f"Failed to extract from {step.selector} (not found)")
            
            await browser.close()
            
            # Update success count
            workflow.success_count += 1
            workflow.updated_at = datetime.now().isoformat()
            self._save_workflows()
            
            output = f"Workflow '{name}' completed successfully!\n\n" + "\n".join(results)
            
            return PrimitiveResult(
                success=True,
                output=output,
                data={
                    "workflow_name": name,
                    "steps_executed": len(workflow.steps),
                    "results": results,
                },
            )
        
        except Exception as e:
            # Update failure count
            workflow.failure_count += 1
            workflow.updated_at = datetime.now().isoformat()
            self._save_workflows()
            
            return PrimitiveResult(
                success=False,
                output=f"Workflow '{name}' failed: {str(e)}",
                error=str(e),
            )
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all saved workflows"""
        return [workflow.to_dict() for workflow in self.workflows.values()]
    
    def get_workflow(self, name: str) -> Optional[WorkflowDef]:
        """Get a workflow by name"""
        return self.workflows.get(name)
    
    def delete_workflow(self, name: str) -> bool:
        """Delete a workflow"""
        if name in self.workflows:
            del self.workflows[name]
            self._save_workflows()
            
            # Unregister from ToolRegistry
            try:
                from .tool_registry import get_tool_registry
                registry = get_tool_registry()
                registry.unregister(f"workflow__{name}")
            except Exception as e:
                logger.warning(f"Failed to unregister workflow tool: {e}")
            
            logger.info(f"Deleted workflow: {name}")
            return True
        
        return False


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_teaching_mode: Optional[TeachingMode] = None


def get_teaching_mode(storage_path: str = "workflows.json") -> TeachingMode:
    """Get global TeachingMode instance (singleton)"""
    global _teaching_mode
    if _teaching_mode is None:
        _teaching_mode = TeachingMode(storage_path)
    return _teaching_mode
