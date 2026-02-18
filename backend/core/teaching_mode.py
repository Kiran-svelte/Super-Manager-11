"""
Teaching Mode - Learn Workflows from User Demonstrations
=========================================================
Users can demonstrate a task by recording their browser actions.
The agent analyzes the recording and saves it as a replayable workflow.

Flow:
1. User says "teach me how to do X" or "let me show you"
2. Frontend starts recording user actions (clicks, inputs, navigations)
3. User performs the task and clicks "Done Recording"
4. Backend analyzes actions and creates a WorkflowDef
5. Workflow is saved and registered as a new tool in ToolRegistry
"""

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime

from .primitives import PrimitiveResult

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """A single step in a learned workflow"""
    action: str          # "navigate", "click", "fill", "select", "wait", "screenshot"
    selector: str = ""   # CSS selector for the target element
    value: str = ""      # Input value, URL, or wait duration
    wait_ms: int = 500   # Delay before this action


@dataclass
class WorkflowDef:
    """A replayable workflow learned from user demonstration"""
    name: str
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)  # e.g., ["{{email}}", "{{name}}"]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    replay_count: int = 0


class TeachingMode:
    """
    Manages workflow recording, analysis, and replay.
    Workflows are stored in-memory (can be extended to Supabase).
    """

    def __init__(self):
        self._workflows: Dict[str, WorkflowDef] = {}
        self._active_recordings: Dict[str, Dict] = {}  # session_id -> recording state

    def start_recording(self, session_id: str, task_description: str = "") -> Dict[str, Any]:
        """Start a recording session. Returns config for the frontend."""
        self._active_recordings[session_id] = {
            "started_at": datetime.now().isoformat(),
            "task_description": task_description,
            "actions": [],
        }

        return {
            "status": "recording",
            "session_id": session_id,
            "task_description": task_description,
            "instructions": "Perform the task in your browser. Click 'Done Recording' when finished.",
        }

    def stop_recording(self, session_id: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Stop recording and process captured actions.
        Actions come from the frontend action recorder.
        """
        recording = self._active_recordings.pop(session_id, None)

        if not recording:
            return {"status": "error", "message": "No active recording for this session"}

        task_description = recording.get("task_description", "Recorded workflow")

        # Analyze and convert actions to workflow
        workflow = self._analyze_actions(actions, task_description)

        if not workflow.steps:
            return {
                "status": "error",
                "message": "No actionable steps were recorded. Try again with more interactions.",
            }

        # Save workflow
        self._workflows[workflow.name] = workflow

        # Register as a tool
        self._register_workflow_tool(workflow)

        return {
            "status": "saved",
            "workflow_name": workflow.name,
            "steps_count": len(workflow.steps),
            "parameters": workflow.parameters,
            "description": workflow.description,
        }

    def _analyze_actions(self, actions: List[Dict[str, Any]], task_description: str) -> WorkflowDef:
        """
        Convert raw browser actions into a structured WorkflowDef.
        Detects patterns, extracts selectors, identifies parameters.
        """
        steps: List[WorkflowStep] = []
        parameters: List[str] = []

        for action in actions:
            action_type = action.get("type", "")
            target = action.get("selector", action.get("target", ""))
            value = action.get("value", "")
            url = action.get("url", "")
            timestamp = action.get("timestamp", 0)

            if action_type == "navigate" or action_type == "pageload":
                steps.append(WorkflowStep(
                    action="navigate",
                    value=url or value,
                    wait_ms=1000,
                ))

            elif action_type == "click":
                if target:
                    steps.append(WorkflowStep(
                        action="click",
                        selector=target,
                        wait_ms=500,
                    ))

            elif action_type in ("input", "change", "fill"):
                if target and value:
                    # Detect if this looks like a parameter (email, name, etc.)
                    param_name = self._detect_parameter(target, value)
                    if param_name:
                        param_placeholder = f"{{{{{param_name}}}}}"
                        if param_placeholder not in parameters:
                            parameters.append(param_placeholder)
                        steps.append(WorkflowStep(
                            action="fill",
                            selector=target,
                            value=param_placeholder,
                            wait_ms=300,
                        ))
                    else:
                        steps.append(WorkflowStep(
                            action="fill",
                            selector=target,
                            value=value,
                            wait_ms=300,
                        ))

            elif action_type == "select":
                if target and value:
                    steps.append(WorkflowStep(
                        action="select",
                        selector=target,
                        value=value,
                        wait_ms=300,
                    ))

            elif action_type == "submit":
                steps.append(WorkflowStep(
                    action="click",
                    selector=target or 'button[type="submit"]',
                    wait_ms=1000,
                ))

        # Generate workflow name from task description
        name = self._generate_name(task_description)

        return WorkflowDef(
            name=name,
            description=task_description or f"Workflow with {len(steps)} steps",
            steps=steps,
            parameters=parameters,
        )

    def _detect_parameter(self, selector: str, value: str) -> Optional[str]:
        """Detect if a form field value should be a parameter."""
        selector_lower = selector.lower()
        value_lower = value.lower()

        # Common parameter patterns
        patterns = {
            "email": [r"email", r"mail", r"e-mail"],
            "name": [r"name", r"full.?name", r"first.?name"],
            "phone": [r"phone", r"tel", r"mobile"],
            "address": [r"address", r"street", r"city"],
            "password": [r"password", r"passwd", r"pass"],
            "date": [r"date", r"check.?in", r"check.?out", r"arrival"],
            "amount": [r"amount", r"price", r"cost", r"payment"],
        }

        for param_name, param_patterns in patterns.items():
            for pattern in param_patterns:
                if re.search(pattern, selector_lower):
                    return param_name

        # If value looks like an email
        if re.match(r"[^@]+@[^@]+\.[^@]+", value):
            return "email"

        # If value looks like a phone number
        if re.match(r"[\d\s\+\-\(\)]{7,}", value):
            return "phone"

        return None

    def _generate_name(self, description: str) -> str:
        """Generate a clean workflow name from description"""
        # Remove common words, keep meaningful ones
        stop_words = {"i", "want", "to", "a", "the", "in", "for", "my", "me", "please", "can", "you", "help", "how", "do"}
        words = description.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        name = "_".join(keywords[:4]) if keywords else f"workflow_{len(self._workflows) + 1}"
        # Sanitize
        name = re.sub(r"[^a-z0-9_]", "", name)
        return name or f"workflow_{len(self._workflows) + 1}"

    def _register_workflow_tool(self, workflow: WorkflowDef):
        """Register a workflow as a tool in the ToolRegistry"""
        try:
            from .tool_registry import get_tool_registry, ToolDef

            registry = get_tool_registry()
            tool_name = f"workflow__{workflow.name}"

            # Build params description from workflow parameters
            params_desc = "no parameters"
            if workflow.parameters:
                clean_params = [p.strip("{}") for p in workflow.parameters]
                params_desc = ", ".join(f"{p} (str)" for p in clean_params)

            async def replay_handler(**kwargs):
                return await self.replay_workflow(workflow.name, kwargs)

            registry.register(ToolDef(
                name=tool_name,
                description=f"Learned workflow: {workflow.description}",
                parameters=params_desc,
                returns=f"Result of replaying {len(workflow.steps)}-step workflow",
                risk_level="risky",
                source="workflow",
                handler=replay_handler,
            ))

            logger.info(f"[TEACHING] Registered workflow tool: {tool_name}")

        except Exception as e:
            logger.warning(f"[TEACHING] Failed to register workflow: {e}")

    async def replay_workflow(self, name: str, params: Dict[str, str] = None) -> PrimitiveResult:
        """Replay a saved workflow with given parameters"""
        workflow = self._workflows.get(name)
        if not workflow:
            return PrimitiveResult(
                success=False,
                output=f"Workflow '{name}' not found. Available: {', '.join(self._workflows.keys())}",
                error="workflow_not_found",
            )

        params = params or {}

        try:
            from .stealth_browser import StealthBrowser
            import asyncio

            browser = StealthBrowser()
            await browser.launch()

            results = []
            for i, step in enumerate(workflow.steps):
                # Substitute parameters
                value = step.value
                selector = step.selector
                for param_placeholder, param_value in params.items():
                    placeholder = f"{{{{{param_placeholder}}}}}"
                    value = value.replace(placeholder, param_value)
                    selector = selector.replace(placeholder, param_value)

                # Wait before action
                if step.wait_ms > 0:
                    await asyncio.sleep(step.wait_ms / 1000)

                if step.action == "navigate":
                    await browser.navigate(value)
                    results.append(f"Step {i+1}: Navigated to {value}")

                elif step.action == "click":
                    if browser._page:
                        element = await browser._page.query_selector(selector)
                        if element:
                            await element.click()
                            results.append(f"Step {i+1}: Clicked {selector}")
                        else:
                            results.append(f"Step {i+1}: Element not found: {selector}")

                elif step.action == "fill":
                    if browser._page:
                        element = await browser._page.query_selector(selector)
                        if element:
                            await element.fill(value)
                            results.append(f"Step {i+1}: Filled {selector} = {value}")
                        else:
                            results.append(f"Step {i+1}: Element not found: {selector}")

                elif step.action == "select":
                    if browser._page:
                        element = await browser._page.query_selector(selector)
                        if element:
                            await element.select_option(value=value)
                            results.append(f"Step {i+1}: Selected {value} in {selector}")
                        else:
                            results.append(f"Step {i+1}: Element not found: {selector}")

            await browser.close()

            workflow.replay_count += 1

            return PrimitiveResult(
                success=True,
                output=f"Workflow '{name}' replayed ({len(workflow.steps)} steps):\n" + "\n".join(results),
                data={
                    "workflow_name": name,
                    "steps_executed": len(results),
                    "results": results,
                    "params_used": params,
                },
            )

        except Exception as e:
            return PrimitiveResult(
                success=False,
                output=f"Workflow replay failed: {str(e)}",
                error=str(e),
            )

    def get_workflows(self) -> List[Dict[str, Any]]:
        """Get all saved workflows"""
        return [
            {
                "name": w.name,
                "description": w.description,
                "steps_count": len(w.steps),
                "parameters": w.parameters,
                "created_at": w.created_at,
                "replay_count": w.replay_count,
            }
            for w in self._workflows.values()
        ]

    def get_workflow(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific workflow with full details"""
        workflow = self._workflows.get(name)
        if not workflow:
            return None
        return asdict(workflow)

    def delete_workflow(self, name: str) -> bool:
        """Delete a workflow and unregister its tool"""
        if name not in self._workflows:
            return False

        del self._workflows[name]

        try:
            from .tool_registry import get_tool_registry
            registry = get_tool_registry()
            registry.unregister(f"workflow__{name}")
        except Exception:
            pass

        return True


# Global singleton
_teaching_mode: Optional[TeachingMode] = None


def get_teaching_mode() -> TeachingMode:
    """Get or create the global teaching mode instance"""
    global _teaching_mode
    if _teaching_mode is None:
        _teaching_mode = TeachingMode()
    return _teaching_mode
