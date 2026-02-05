"""
Core Agent Framework with Reasoning Loop
"""
import json
import asyncio
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
import os
from datetime import datetime

class AgentManager:
    """Main agent manager with reasoning capabilities"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.max_iterations = 10
        self.memory_store = {}
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
        
    async def process_intent(self, user_input: str, user_id: str = "default", context: Dict = None) -> Dict[str, Any]:
        """
        Main reasoning loop for processing user intent
        """
        context = context or {}
        
        # Step 1: Parse intent
        intent_data = await self._parse_intent(user_input, context)
        
        # Step 2: Plan task
        plan = await self._create_plan(intent_data, context)
        
        # Step 3: Execute reasoning loop
        result = await self._reasoning_loop(plan, user_input, user_id, context)
        
        return {
            "intent": intent_data,
            "plan": plan,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _parse_intent(self, user_input: str, context: Dict) -> Dict[str, Any]:
        """Parse user intent using LLM"""
        system_prompt = """You are an intent parser for Super Manager. Analyze user input and extract:
1. Primary intent/action
2. Entities (dates, times, locations, people, etc.)
3. Constraints and preferences
4. Priority level
5. Required capabilities/plugins

Return JSON format:
{
    "action": "main action verb",
    "category": "task category",
    "entities": {},
    "constraints": [],
    "priority": "high/medium/low",
    "capabilities": []
}"""
        
        try:
            if not self.api_key:
                # Fallback parsing
                from .intent_parser import IntentParser
                parser = IntentParser()
                return await parser.parse(user_input, context)
            
            response = await self._get_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            intent_data = json.loads(response.choices[0].message.content)
            return intent_data
        except Exception as e:
            # Fallback parsing
            return {
                "action": "unknown",
                "category": "general",
                "entities": {},
                "constraints": [],
                "priority": "medium",
                "capabilities": []
            }
    
    async def _create_plan(self, intent_data: Dict, context: Dict) -> Dict[str, Any]:
        """Create execution plan from intent"""
        system_prompt = """You are a task planner for Super Manager. Create a detailed execution plan.
Return JSON format:
{
    "steps": [
        {
            "id": 1,
            "action": "action description",
            "plugin": "plugin name",
            "parameters": {},
            "dependencies": []
        }
    ],
    "estimated_time": "time estimate",
    "required_resources": []
}"""
        
        intent_str = json.dumps(intent_data, indent=2)
        
        try:
            if not self.api_key:
                # Use fallback plan
                from .task_planner import TaskPlanner
                planner = TaskPlanner()
                return await planner.create_plan(intent_data, context)
            
            response = await self._get_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Intent: {intent_str}\n\nCreate execution plan."}
                ],
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            plan = json.loads(response.choices[0].message.content)
            return plan
        except Exception as e:
            # Fallback plan
            return {
                "steps": [{
                    "id": 1,
                    "action": "Execute task",
                    "plugin": "general",
                    "parameters": {},
                    "dependencies": []
                }],
                "estimated_time": "unknown",
                "required_resources": []
            }
    
    async def _reasoning_loop(self, plan: Dict, user_input: str, user_id: str, context: Dict) -> Dict[str, Any]:
        """Main reasoning loop with iterative refinement"""
        steps = plan.get("steps", [])
        results = []
        current_state = context.copy()
        
        for iteration in range(self.max_iterations):
            for step in steps:
                if step.get("status") == "completed":
                    continue
                
                # Execute step
                step_result = await self._execute_step(step, current_state, user_id)
                step["status"] = step_result.get("status", "completed")
                step["result"] = step_result.get("result")
                results.append(step_result)
                
                # Update state
                current_state.update(step_result.get("state_updates", {}))
                
                # Check if we need to replan
                if step_result.get("needs_replanning"):
                    new_plan = await self._replan(plan, results, user_input)
                    steps = new_plan.get("steps", [])
                    break
            
            # Check if all steps completed
            if all(s.get("status") == "completed" for s in steps):
                break
            
            # Reasoning check
            if iteration < self.max_iterations - 1:
                reasoning = await self._reason_about_progress(plan, results, user_input)
                if reasoning.get("should_stop"):
                    break
        
        return {
            "status": "completed",
            "steps": results,
            "final_state": current_state,
            "iterations": iteration + 1
        }
    
    async def _execute_step(self, step: Dict, state: Dict, user_id: str) -> Dict[str, Any]:
        """Execute a single step in the plan"""
        from .plugins import PluginManager
        
        plugin_name = step.get("plugin", "general")
        action = step.get("action", "")
        parameters = step.get("parameters", {})
        
        # Get plugin manager and execute
        plugin_manager = PluginManager()
        plugin = plugin_manager.get_plugin(plugin_name)
        
        if plugin:
            try:
                result = await plugin.execute(step, state)
                # Create base response
                response = {
                    "status": result.get("status", "completed"),
                    "result": result.get("result", result.get("error", "")),
                    "state_updates": result.get("output", {}),
                    "needs_replanning": result.get("status") == "failed",
                    "plugin": plugin_name,
                    "action": action
                }
                # Merge original result to keep extra data (like 'event', 'email')
                response.update(result)
                return response
            except Exception as e:
                return {
                    "status": "failed",
                    "result": f"Error: {str(e)}",
                    "state_updates": {},
                    "needs_replanning": True,
                    "plugin": plugin_name,
                    "action": action
                }
        else:
            # Fallback execution
            await asyncio.sleep(0.1)
            return {
                "status": "completed",
                "result": f"Executed: {action}",
                "state_updates": {},
                "needs_replanning": False,
                "plugin": plugin_name,
                "action": action
            }
    
    async def _replan(self, current_plan: Dict, results: List[Dict], user_input: str) -> Dict[str, Any]:
        """Replan based on current results"""
        # Simplified replanning - in production, use LLM
        return current_plan
    
    async def _reason_about_progress(self, plan: Dict, results: List[Dict], user_input: str) -> Dict[str, Any]:
        """Reason about progress and decide next actions"""
        return {
            "should_stop": len(results) > 0,
            "reasoning": "Progress made"
        }
    
    async def get_memory(self, user_id: str, key: str) -> Optional[Any]:
        """Retrieve memory for user"""
        memory_key = f"{user_id}:{key}"
        return self.memory_store.get(memory_key)
    
    async def set_memory(self, user_id: str, key: str, value: Any):
        """Store memory for user"""
        memory_key = f"{user_id}:{key}"
        self.memory_store[memory_key] = value

