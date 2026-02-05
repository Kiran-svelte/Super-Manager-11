"""
Task Planning and Execution Engine
"""
import json
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
import os
from datetime import datetime

class TaskPlanner:
    """Advanced task planning with multi-step workflows"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
    
    async def create_plan(self, intent: Dict, context: Dict = None, available_plugins: List[str] = None) -> Dict[str, Any]:
        """Create detailed execution plan"""
        context = context or {}
        available_plugins = available_plugins or []
        
        system_prompt = """You are an expert task planner. Create a detailed, executable plan.
Consider:
- Breaking complex tasks into steps
- Dependencies between steps
- Error handling
- Required plugins/capabilities
- User preferences

Return JSON:
{
    "steps": [
        {
            "id": 1,
            "name": "step name",
            "action": "what to do",
            "plugin": "plugin name",
            "parameters": {},
            "dependencies": [],
            "error_handling": "what to do on failure"
        }
    ],
    "estimated_duration": "time estimate",
    "required_plugins": [],
    "parallelizable": false
}"""
        
        intent_str = json.dumps(intent, indent=2)
        plugins_str = ", ".join(available_plugins) if available_plugins else "all available"
        
        try:
            if not self.api_key:
                # Use fallback plan
                return self._create_fallback_plan(intent)
            
            response = await self._get_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Intent: {intent_str}\n\nAvailable plugins: {plugins_str}\n\nCreate plan."}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            plan = json.loads(response.choices[0].message.content)
            plan["created_at"] = datetime.utcnow().isoformat()
            plan["status"] = "planned"
            return plan
        except Exception as e:
            # Fallback plan
            return self._create_fallback_plan(intent)
    
    def _create_fallback_plan(self, intent: Dict) -> Dict[str, Any]:
        """Create smart fallback plan based on intent"""
        action = intent.get("action", "").lower()
        entities = intent.get("entities", {})
        category = intent.get("category", "general")
        
        # Detect meeting scheduling
        if any(keyword in action for keyword in ["schedule", "meeting", "call", "zoom"]):
            return self._create_meeting_plan(intent)
        
        # Detect planning/research
        if any(keyword in action for keyword in ["plan", "organize", "research", "find"]):
            return self._create_research_plan(intent)

        # Default simple plan
        return {
            "steps": [{
                "id": 1,
                "name": "Execute task",
                "action": intent.get("action", "process"),
                "plugin": "general",
                "parameters": entities,
                "dependencies": [],
                "error_handling": "retry once"
            }],
            "estimated_duration": "unknown",
            "required_plugins": [],
            "parallelizable": False,
            "status": "planned",
            "created_at": datetime.utcnow().isoformat()
        }

    def _create_research_plan(self, intent: Dict) -> Dict[str, Any]:
        """Create a multi-step plan for research/planning"""
        entities = intent.get("entities", {})
        topic = intent.get("action", "").replace("plan", "").replace("research", "").strip()
        
        steps = []
        
        # Step 1: Search for information
        steps.append({
            "id": 1,
            "name": "Research Topic",
            "action": "search",
            "plugin": "search",
            "parameters": {
                "query": f"how to {intent.get('action', 'plan')}"
            },
            "dependencies": [],
            "error_handling": "continue"
        })
        
        # Step 2: Create plan/summary
        steps.append({
            "id": 2,
            "name": "Create Plan",
            "action": "create_plan",
            "plugin": "general", # In real system, this would be a planner plugin
            "parameters": {
                "topic": topic,
                "context": "Based on research results"
            },
            "dependencies": [1],
            "error_handling": "notify user"
        })
        
        return {
            "steps": steps,
            "estimated_duration": "2 minutes",
            "required_plugins": ["search", "general"],
            "parallelizable": False,
            "status": "planned",
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _create_meeting_plan(self, intent: Dict) -> Dict[str, Any]:
        """Create a multi-step plan for meeting scheduling"""
        entities = intent.get("entities", {})
        
        # Extract meeting details from entities or use defaults
        steps = []
        
        # Step 1: Schedule Zoom meeting
        steps.append({
            "id": 1,
            "name": "Schedule Zoom Meeting",
            "action": "Schedule Zoom meeting",
            "plugin": "zoom",
            "parameters": {
                "topic": entities.get("topic", "Meeting"),
                "date": entities.get("date", "tomorrow"),
                "time": entities.get("time", "2pm"),
                "duration": entities.get("duration", 60),
                "attendees": entities.get("attendees", [])
            },
            "dependencies": [],
            "error_handling": "notify user"
        })
        
        # Step 2: Send email invitation (if recipient specified)
        if entities.get("recipient") or entities.get("email"):
            steps.append({
                "id": 2,
                "name": "Send Email Invitation",
                "action": "Send email with meeting details",
                "plugin": "email",
                "parameters": {
                    "to": entities.get("recipient", entities.get("email", "recipient@example.com")),
                    "subject": f"Meeting Invitation: {entities.get('topic', 'Meeting')}",
                    "body": "You've been invited to a meeting. Details will be shared."
                },
                "dependencies": [1],
                "error_handling": "continue"
            })
        
        # Step 3: Send WhatsApp reminder (if phone specified)
        if entities.get("phone") or entities.get("whatsapp"):
            steps.append({
                "id": 3,
                "name": "Send WhatsApp Reminder",
                "action": "Send WhatsApp message",
                "plugin": "whatsapp",
                "parameters": {
                    "to": entities.get("phone", entities.get("whatsapp", "contact")),
                    "message": f"Reminder: Meeting scheduled for {entities.get('date', 'tomorrow')} at {entities.get('time', '2pm')}"
                },
                "dependencies": [1],
                "error_handling": "continue"
            })
        
        # Step 4: Add to calendar
        steps.append({
            "id": len(steps) + 1,
            "name": "Add to Calendar",
            "action": "Add meeting to calendar",
            "plugin": "calendar",
            "parameters": {
                "title": entities.get("topic", "Meeting"),
                "date": entities.get("date", "tomorrow"),
                "time": entities.get("time", "2pm"),
                "duration": entities.get("duration", "1 hour")
            },
            "dependencies": [1],
            "error_handling": "continue"
        })
        
        return {
            "steps": steps,
            "estimated_duration": "30 seconds",
            "required_plugins": ["zoom", "email", "whatsapp", "calendar"],
            "parallelizable": False,
            "status": "planned",
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def execute_plan(self, plan: Dict, plugins: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plan step by step"""
        steps = plan.get("steps", [])
        results = []
        execution_state = {}
        
        for step in steps:
            step_id = step.get("id")
            plugin_name = step.get("plugin", "general")
            
            # Check dependencies
            dependencies = step.get("dependencies", [])
            if not self._check_dependencies(dependencies, results):
                results.append({
                    "step_id": step_id,
                    "status": "blocked",
                    "error": "Dependencies not met"
                })
                continue
            
            # Execute step
            try:
                plugin = plugins.get(plugin_name, plugins.get("general"))
                if plugin:
                    step_result = await plugin.execute(step, execution_state)
                else:
                    step_result = {
                        "status": "failed",
                        "error": f"Plugin {plugin_name} not found"
                    }
                
                step_result["step_id"] = step_id
                step_result["timestamp"] = datetime.utcnow().isoformat()
                results.append(step_result)
                
                # Update execution state
                if step_result.get("status") == "completed":
                    execution_state[f"step_{step_id}"] = step_result.get("result")
                
            except Exception as e:
                results.append({
                    "step_id": step_id,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Determine overall status
        all_completed = all(r.get("status") == "completed" for r in results)
        any_failed = any(r.get("status") == "failed" for r in results)
        
        return {
            "plan_id": plan.get("id"),
            "status": "completed" if all_completed else ("failed" if any_failed else "partial"),
            "steps": results,
            "execution_state": execution_state,
            "completed_at": datetime.utcnow().isoformat()
        }
    
    def _check_dependencies(self, dependencies: List[int], results: List[Dict]) -> bool:
        """Check if all dependencies are satisfied"""
        completed_steps = {r["step_id"] for r in results if r.get("status") == "completed"}
        return all(dep in completed_steps for dep in dependencies)
    
    async def optimize_plan(self, plan: Dict) -> Dict[str, Any]:
        """Optimize plan for better execution"""
        # Reorder steps for parallelization
        steps = plan.get("steps", [])
        optimized_steps = self._topological_sort(steps)
        
        plan["steps"] = optimized_steps
        plan["optimized"] = True
        return plan
    
    def _topological_sort(self, steps: List[Dict]) -> List[Dict]:
        """Sort steps based on dependencies"""
        # Simple topological sort
        sorted_steps = []
        remaining = steps.copy()
        completed_ids = set()
        
        while remaining:
            progress = False
            for step in remaining[:]:
                deps = step.get("dependencies", [])
                if all(dep in completed_ids for dep in deps):
                    sorted_steps.append(step)
                    completed_ids.add(step["id"])
                    remaining.remove(step)
                    progress = True
            
            if not progress:
                # Circular dependency or missing step
                sorted_steps.extend(remaining)
                break
        
        return sorted_steps
