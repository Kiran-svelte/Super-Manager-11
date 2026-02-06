"""
Enhanced Agent API Routes with Multi-Stage Conversations
NOW POWERED BY TRUE AI CHAT - No more hardcoded responses!
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid

from ..database_supabase import get_db, Task, create_task
from ..core.agent import AgentManager
from ..core.intent_parser import IntentParser
from ..core.task_planner import TaskPlanner
from ..core.plugins import PluginManager
from ..core.memory import MemoryManager
from ..core.confirmation_manager import get_confirmation_manager, PendingAction
from ..core.intent_classifier import IntentClassifier
from ..core.conversation_manager import get_conversation_manager
# NEW: Import true AI chat
from ..core.true_ai_chat import chat as true_ai_chat, get_conversation

router = APIRouter()

class AgentRequest(BaseModel):
    message: str
    user_id: str = "default"
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

class AgentResponse(BaseModel):
    response: str
    intent: Dict[str, Any]
    plan: Dict[str, Any]
    result: Dict[str, Any]
    task_id: Optional[str] = None
    requires_confirmation: bool = False
    requires_selection: bool = False
    session_id: Optional[str] = None
    pending_actions: Optional[List[Dict[str, Any]]] = None
    options: Optional[List[Dict[str, Any]]] = None
    stage_type: Optional[str] = None
    meeting_url: Optional[str] = None  # NEW: For meeting links

class SelectionRequest(BaseModel):
    session_id: str
    selection: Optional[str] = None  # For single choice
    selections: Optional[List[str]] = None  # For multiple choice

class ConfirmationRequest(BaseModel):
    session_id: str
    action: str  # "approve_all", "reject_all", "approve", "reject"
    action_id: Optional[str] = None

@router.post("/process", response_model=AgentResponse)
async def process_intent(
    request: AgentRequest,
    app_request: Request
):
    """
    Process user intent using TRUE AI CHAT.
    
    ALL responses now come from the LLM (Groq) - no hardcoded text!
    The AI understands context, remembers conversation, and decides what to do.
    """
    try:
        # Get or create session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Use the new TRUE AI Chat system
        result = await true_ai_chat(session_id, request.message)
        
        # Ensure result is always a dict (not list)
        results_data = result.get("results")
        if isinstance(results_data, list):
            results_dict = {"results": results_data}
        elif results_data:
            results_dict = results_data
        else:
            results_dict = {}
        
        # Build response
        response = AgentResponse(
            response=result.get("response", ""),
            intent={"type": "ai_determined", "raw_input": request.message},
            plan={},
            result=results_dict,
            requires_confirmation=result.get("requires_confirmation", False),
            session_id=session_id,
            meeting_url=result.get("meeting_url")
        )
        
        # If action was completed, include results
        if result.get("action_completed"):
            response.result = {"action_completed": True, "data": result.get("results", [])}
        
        return response
        
    except Exception as e:
        print(f"[AGENT ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        # Even errors should be friendly
        return AgentResponse(
            response="Oops! Something went wrong on my end. Could you try that again? 😅",
            intent={"type": "error"},
            plan={},
            result={"error": str(e)},
            session_id=request.session_id or str(uuid.uuid4())
        )


# Keep the old endpoints for backward compatibility but they redirect to true AI
@router.post("/process_legacy", response_model=AgentResponse)
async def process_intent_legacy(
    request: AgentRequest,
    app_request: Request
):
    """Legacy endpoint - redirects to true AI chat for compatibility"""
    # Just use the new AI chat system
    session_id = request.session_id or str(uuid.uuid4())
    result = await true_ai_chat(session_id, request.message)
    return AgentResponse(
        response=result.get("response", ""),
        intent={"type": "ai_determined"},
        plan={},
        result=result.get("results", {}) if result.get("results") else {},
        requires_confirmation=result.get("requires_confirmation", False),
        session_id=session_id,
        meeting_url=result.get("meeting_url")
    )


def get_destination_options() -> List[Dict[str, Any]]:
    """Get destination options for selection"""
    return [
        {"id": "goa", "name": "Goa", "description": "Beach paradise with nightlife"},
        {"id": "manali", "name": "Manali", "description": "Mountain retreat with adventure"},
        {"id": "udaipur", "name": "Udaipur", "description": "Royal palaces and lakes"},
        {"id": "kerala", "name": "Kerala", "description": "Backwaters and nature"}
    ]

@router.post("/select")
async def handle_selection(request: SelectionRequest):
    """Handle user selection in multi-stage conversation"""
    try:
        conversation_manager = get_conversation_manager()
        confirmation_manager = get_confirmation_manager()
        
        session = conversation_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Process the selection
        result = await conversation_manager.process_user_response(
            request.session_id,
            {
                "selection": request.selection,
                "selections": request.selections
            }
        )
        
        # print(f"[DEBUG] Selection result: {result}")  # Debug logging - Commented out to prevent encoding errors
        
        if result.get("status") == "ready_for_execution":
            # All stages complete, create final confirmation
            plan = result.get("plan", {})
            actions = plan.get("actions", [])
            
            # Store in confirmation manager
            pending_actions = []
            for action in actions:
                pending_action = PendingAction(
                    action_type=action["type"],
                    description=action["description"],
                    parameters=action["parameters"],
                    plugin=action["plugin"]
                )
                pending_actions.append(pending_action)
            
            confirmation_manager.pending_actions[request.session_id] = pending_actions
            confirmation_manager.session_plans[request.session_id] = {
                "plan": plan,
                "user_input": session.initial_intent.get("original_input", ""),
                "created_at": session.created_at
            }
            
            confirmation_message = generate_final_confirmation_message(plan)
            
            return {
                "status": "ready_for_confirmation",
                "response": confirmation_message,
                "requires_confirmation": True,
                "pending_actions": [action.to_dict() for action in pending_actions],
                "session_id": request.session_id
            }
        
        elif result.get("status") == "stage_completed":
            # Move to next stage
            next_stage_data = result.get("next_stage")
            if next_stage_data:
                # Get the current stage to determine stage_type
                session = conversation_manager.get_session(request.session_id)
                current_stage = session.get_current_stage() if session else None
                stage_type = current_stage.stage_type if current_stage else "unknown"
                
                # Check if next stage is final_confirmation
                if stage_type == "final_confirmation":
                    # Generate plan and request confirmation
                    plan = conversation_manager.generate_execution_plan(session)
                    actions = plan.get("actions", [])
                    
                    # Store in confirmation manager
                    pending_actions = []
                    for action in actions:
                        pending_action = PendingAction(
                            action_type=action["type"],
                            description=action["description"],
                            parameters=action["parameters"],
                            plugin=action["plugin"]
                        )
                        pending_actions.append(pending_action)
                    
                    confirmation_manager.pending_actions[request.session_id] = pending_actions
                    confirmation_manager.session_plans[request.session_id] = {
                        "plan": plan,
                        "user_input": session.initial_intent.get("original_input", ""),
                        "created_at": session.created_at
                    }
                    
                    confirmation_message = generate_final_confirmation_message(plan)
                    
                    return {
                        "status": "ready_for_confirmation",
                        "response": confirmation_message,
                        "requires_confirmation": True,
                        "pending_actions": [action.to_dict() for action in pending_actions],
                        "session_id": request.session_id,
                        "stage_type": stage_type
                    }
                
                # Get human-like question
                from ..core.human_ai import generate_stage_question
                q = next_stage_data.get("question") or generate_stage_question(stage_type)
                return {
                    "status": "next_stage",
                    "response": q,
                    "requires_selection": True,
                    "options": next_stage_data.get("options", []),
                    "session_id": request.session_id,
                    "stage_type": stage_type
                }
        
        return result
    
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        error_msg = f"[ERROR] Exception in handle_selection: {e}\n{traceback.format_exc()}"
        with open("debug_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {error_msg}\n")
        raise HTTPException(status_code=500, detail=str(e))

def generate_final_confirmation_message(plan: Dict[str, Any]) -> str:
    """Generate final confirmation message from plan"""
    destination = plan.get("destination", "your destination")
    accommodation = plan.get("accommodation", {})
    activities = plan.get("activities", [])
    
    message = f"🎉 Awesome! Here's your plan for {destination}:\n\n"
    
    if accommodation:
        message += f"🏨 **Stay at**: {accommodation.get('name', 'Resort')}\n"
        if accommodation.get('price'):
            message += f"   ({accommodation.get('price')})\n"
    
    if activities:
        message += f"\n🎯 **Activities lined up**:\n"
        for activity in activities:
            message += f"   • {activity.get('name', 'Activity')}\n"
    
    message += "\n📋 **Here's what I'll do**:\n"
    
    return message

@router.post("/confirm")
async def confirm_actions(request: ConfirmationRequest):
    """Handle user confirmation of actions"""
    try:
        confirmation_manager = get_confirmation_manager()
        plugin_manager = PluginManager()
        
        # Handle confirmation action
        if request.action == "approve_all":
            confirmation_manager.approve_all(request.session_id)
        elif request.action == "reject_all":
            confirmation_manager.reject_all(request.session_id)
            return {
                "status": "cancelled",
                "message": "All actions have been cancelled."
            }
        
        # Get approved actions
        approved_actions = confirmation_manager.get_approved_actions(request.session_id)
        
        cm = get_conversation_manager()
        cm.log_debug(f"Executing actions for session {request.session_id}")
        cm.log_debug(f"Approved actions: {[a.to_dict() for a in approved_actions]}")
        
        if not approved_actions:
            return {
                "status": "waiting",
                "message": "Waiting for approval of actions."
            }
        
        # Execute approved actions
        results = []
        meeting_link = None
        
        # First pass: Execute meeting creation to get link
        for action in approved_actions:
            if action.plugin == "zoom" or "schedule" in action.action_type.lower():
                plugin = plugin_manager.get_plugin(action.plugin)
                if plugin:
                    step = {
                        "action": action.action_type,
                        "parameters": action.parameters,
                        "plugin": action.plugin
                    }
                    cm.log_debug(f"Executing meeting plugin {action.plugin} with step: {step}")
                    result = await plugin.execute(step, {})
                    
                    # Extract meeting link
                    if result.get("status") == "completed":
                        meeting_output = result.get("output", {})
                        meeting_link = meeting_output.get("join_url", "")
                        cm.log_debug(f"Meeting link generated: {meeting_link}")
                    
                    results.append({
                        "action": action.description,
                        "result": result.get("result", ""),
                        "status": result.get("status", "completed"),
                        "details": result.get("output", {})
                    })
        
        # Second pass: Execute other actions (including email with meeting link)
        for action in approved_actions:
            if action.plugin != "zoom" and "schedule" not in action.action_type.lower():
                plugin = plugin_manager.get_plugin(action.plugin)
                if plugin:
                    step = {
                        "action": action.action_type,
                        "parameters": action.parameters.copy(),
                        "plugin": action.plugin
                    }
                    
                    # Add meeting link to email parameters
                    if action.plugin == "email" and meeting_link:
                        step["parameters"]["meeting_link"] = meeting_link
                        cm.log_debug(f"Adding meeting link to email: {meeting_link}")
                    
                    cm.log_debug(f"Executing plugin {action.plugin} with step: {step}")
                    # Pass meeting_link in state for plugins like Telegram to use
                    result = await plugin.execute(step, {"meeting_link": meeting_link})
                    results.append({
                        "action": action.description,
                        "result": result.get("result", ""),
                        "status": result.get("status", "completed"),
                        "details": result.get("output", {})
                })
        
        # Clear session
        confirmation_manager.clear_session(request.session_id)
        
        # Generate response
        response_text = "✅ All actions completed successfully!\n\n"
        for i, res in enumerate(results, 1):
            response_text += f"{i}. {res['action']}: {res['result']}\n"
            
            # Add specific details
            if res.get('details'):
                details = res['details']
                if 'booking_reference' in details:
                    response_text += f"   📋 Booking Reference: {details['booking_reference']}\n"
                if 'join_url' in details:
                    response_text += f"   📹 Join URL: {details['join_url']}\n"
                if 'password' in details:
                    response_text += f"   🔐 Password: {details['password']}\n"
                if 'order_number' in details:
                    response_text += f"   🎂 Order Number: {details['order_number']}\n"
        
        return {
            "status": "completed",
            "message": response_text,
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_agent_status(app_request: Request):
    """Get agent status"""
    return {
        "status": "operational",
        "capabilities": PluginManager().get_available_capabilities()
    }
