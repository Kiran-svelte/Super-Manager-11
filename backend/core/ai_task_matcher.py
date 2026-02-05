"""
AI-Powered Task Matcher
Uses AI to match user input to available tasks
"""
from typing import Dict, Any, Optional
from .task_registry import get_task_registry
from .self_healing_ai import get_ai_manager
import asyncio

class AITaskMatcher:
    """Uses AI to match user requests to available tasks"""
    
    def __init__(self):
        self.task_registry = get_task_registry()
        self.ai_manager = get_ai_manager()
    
    async def match_task(self, user_input: str) -> Dict[str, Any]:
        """
        Use AI to determine which task the user wants to perform
        Returns: {
            "task_id": "schedule_meeting",
            "confidence": "high",
            "extracted_info": {"time": "tomorrow at 2pm", ...}
        }
        """
        # Get all available tasks
        available_tasks = self.task_registry.get_task_descriptions_for_ai()
        
        # Ask AI to match the user input to a task
        prompt = f"""User request: "{user_input}"

Available tasks:
{available_tasks}

Analyze the user's request and determine which task they want to perform.
Also extract any information they've already provided.

Return JSON:
{{
  "task_id": "task_id_from_list",
  "confidence": "high" or "medium" or "low",
  "reasoning": "why you chose this task",
  "extracted_info": {{
    "key": "value for any information mentioned"
  }}
}}

If no task matches well, use task_id: "general" with low confidence."""

        try:
            print(f"[AI_TASK_MATCHER] Sending prompt to AI: {prompt[:100]}...")
            result = await self.ai_manager.generate_dynamic_response(
                context=user_input,
                data_type="task_match",
                schema_description=prompt
            )
            
            print(f"[AI_TASK_MATCHER] Raw AI result: {result}")
            
            if isinstance(result, dict):
                # Validate the task_id exists
                task_id = result.get("task_id", "general")
                if task_id != "general" and not self.task_registry.get_task(task_id):
                    print(f"[AI_TASK_MATCHER] Invalid task_id: {task_id}")
                    result["task_id"] = "general"
                    result["confidence"] = "low"
                
                return result
            else:
                print(f"[AI_TASK_MATCHER] Result is not dict: {type(result)}")
                return {
                    "task_id": "general",
                    "confidence": "low",
                    "reasoning": "Could not parse AI response",
                    "extracted_info": {}
                }
                
        except Exception as e:
            print(f"[AI_TASK_MATCHER] Error: {e}")
            return {
                "task_id": "general",
                "confidence": "low",
                "reasoning": f"Error: {str(e)}",
                "extracted_info": {}
            }
    
    async def get_missing_info(self, task_id: str, already_have: Dict[str, Any]) -> Optional[str]:
        """
        Determine what information is still needed for a task
        Returns the next question to ask the user, or None if we have everything
        """
        task = self.task_registry.get_task(task_id)
        if not task:
            return None
        
        # Find what's missing
        missing = []
        for required in task.required_info:
            if required not in already_have or not already_have[required]:
                missing.append(required)
        
        if not missing:
            return None  # We have everything
        
        # Ask AI to generate a natural question for the next missing piece
        next_needed = missing[0]
        prompt = f"""The user wants to {task.description}.
We need to ask them for: {next_needed}

Generate a natural, friendly question to ask for this information.
Return just the question text, nothing else."""

        try:
            question = await self.ai_manager.generate_dynamic_response(
                context=f"Task: {task.name}, Need: {next_needed}",
                data_type="question",
                schema_description=prompt
            )
            
            if isinstance(question, str):
                return question
            elif isinstance(question, dict) and "question" in question:
                return question["question"]
            else:
                # Fallback
                return f"What {next_needed.replace('_', ' ')} would you like?"
                
        except Exception as e:
            print(f"[AI_TASK_MATCHER] Error generating question: {e}")
            return f"Please provide the {next_needed.replace('_', ' ')}."

# Global instance
_task_matcher = None

def get_task_matcher() -> AITaskMatcher:
    global _task_matcher
    if _task_matcher is None:
        _task_matcher = AITaskMatcher()
    return _task_matcher
