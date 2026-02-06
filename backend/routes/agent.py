"""
Enhanced Agent API Routes with Multi-Stage Conversations
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
    """Process user intent with multi-stage conversation support"""
    try:
        intent_classifier = IntentClassifier()
        conversation_manager = get_conversation_manager()
        confirmation_manager = get_confirmation_manager()
        
        # Check for existing session and text input stages
        if request.session_id:
            session = conversation_manager.get_session(request.session_id)
            if session:
                current_stage = session.get_current_stage()
                
                # Handle confirmation stage with text response (yes/no)
                if current_stage and current_stage.data.get("type") == "confirmation":
                    user_response = request.message.lower().strip()
                    if user_response in ["yes", "y", "confirm", "ok", "sure", "proceed"]:
                        # User confirmed - process as approval
                        result = await conversation_manager.process_user_response(
                            request.session_id,
                            {"confirmed": True}
                        )
                        
                        if result.get("status") == "ready_for_execution":
                            plan = result.get("plan", {})
                            actions = plan.get("actions", [])
                            
                            # Store and execute
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
                            
                            # Execute immediately
                            plugin_manager = PluginManager()
                            execution_results = []
                            for action in actions:
                                plugin = plugin_manager.get_plugin(action["plugin"])
                                if plugin:
                                    step = {"action": action["type"], "parameters": action["parameters"]}
                                    exec_result = await plugin.execute(step, {})
                                    execution_results.append(exec_result)
                            
                            return AgentResponse(
                                response="Actions executed successfully!",
                                intent=session.initial_intent,
                                plan=plan,
                                result={"execution_results": execution_results},
                                requires_confirmation=False,
                                session_id=request.session_id,
                                stage_type="completed"
                            )
                    elif user_response in ["no", "n", "cancel", "stop", "abort"]:
                        return AgentResponse(
                            response="Action cancelled.",
                            intent=session.initial_intent,
                            plan={},
                            result={},
                            requires_confirmation=False,
                            session_id=request.session_id,
                            stage_type="cancelled"
                        )
                
                # Handle ANY text_input stage (not just participant_details)
                if current_stage and current_stage.data.get("type") == "text_input":
                    # Process text input for this stage
                    result = await conversation_manager.process_user_response(
                        request.session_id,
                        {"text_input": request.message}
                    )
                    
                    if result.get("status") == "stage_completed":
                        next_stage_data = result.get("next_stage")
                        if next_stage_data:
                            # Refresh session to get updated state
                            session = conversation_manager.get_session(request.session_id)
                            next_stage_type = session.get_current_stage().stage_type
                            
                            # Check if next stage is final_confirmation
                            if next_stage_type == "final_confirmation":
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
                                
                                return AgentResponse(
                                    response=confirmation_message,
                                    intent=session.initial_intent,
                                    plan=plan,
                                    result={},
                                    requires_confirmation=True,
                                    session_id=request.session_id,
                                    pending_actions=[action.to_dict() for action in pending_actions],
                                    stage_type=next_stage_type
                                )

                            return AgentResponse(
                                response=next_stage_data.get("question", "Please make a selection:"),
                                intent=session.initial_intent,
                                plan={},
                                result={},
                                requires_selection=True,
                                session_id=session.session_id,
                                options=next_stage_data.get("options", []),
                                stage_type=next_stage_type
                            )
                    elif result.get("status") == "ready_for_execution":
                        # Create confirmation
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
                        
                        return AgentResponse(
                            response=confirmation_message,
                            intent=session.initial_intent,
                            plan=plan,
                            result={},
                            requires_confirmation=True,
                            session_id=request.session_id,
                            pending_actions=[action.to_dict() for action in pending_actions]
                        )

        # Classify the intent
        classified_intent = intent_classifier.classify(request.message)
        
        # Check if intent requires clarification
        if intent_classifier.requires_clarification(classified_intent):
            clarification_question = intent_classifier.generate_clarification_question(classified_intent)
            
            # Create session with proper stages
            temp_session = await conversation_manager.create_session(classified_intent)
            
            # Get the actual first stage (should be destination_selection)
            first_stage = temp_session.get_current_stage()
            actual_stage_type = first_stage.stage_type if first_stage else "unknown"
            
            # Get options from the stage (AI-generated)
            options = first_stage.data.get("options", []) if first_stage else []
            
            return AgentResponse(
                response=clarification_question,
                intent=classified_intent,
                plan={},
                result={},
                requires_selection=True,
                session_id=temp_session.session_id,
                options=options,
                stage_type=actual_stage_type
            )
        
        # Create multi-stage conversation session
        session = await conversation_manager.create_session(classified_intent)
        
        # Get first stage
        current_stage = session.get_current_stage()
        
        if not current_stage:
            # No stages, create simple confirmation
            return await create_simple_confirmation(
                request.message,
                classified_intent,
                confirmation_manager
            )
        
        # Return first stage to user
        stage_data = current_stage.data
        
        # Check if it's an execution stage (instant meeting)
        if current_stage.stage_type in ["execution", "instant_execution"]:
             # Auto-process this stage
             result = await conversation_manager.process_user_response(
                 session.session_id,
                 {"action": "execute"}
             )
             
             if result.get("status") == "ready_for_execution":
                 # Create confirmation/execution plan
                 plan = result.get("plan", {})
                 actions = plan.get("actions", [])
                 
                 # Store in confirmation manager (even if we auto-execute, we need structure)
                 pending_actions = []
                 for action in actions:
                     pending_action = PendingAction(
                         action_type=action["type"],
                         description=action["description"],
                         parameters=action["parameters"],
                         plugin=action["plugin"]
                     )
                     pending_actions.append(pending_action)
                 
                 confirmation_manager.pending_actions[session.session_id] = pending_actions
                 confirmation_manager.session_plans[session.session_id] = {
                     "plan": plan,
                     "user_input": session.initial_intent.get("original_input", ""),
                     "created_at": session.created_at
                 }
                 
                 # For instant meetings, we might want to skip confirmation and just execute?
                 # The user said "redirect directly to that meeting".
                 # So we should probably return requires_confirmation=True but with a flag or just execute?
                 # If we return requires_confirmation=True, the frontend waits for "Yes".
                 # If we want to skip, we need to execute HERE.
                 
                 # Let's execute here for instant gratification!
                 plugin_manager = PluginManager()
                 execution_results = []
                 for action in actions:
                     plugin = plugin_manager.get_plugin(action["plugin"])
                     if plugin:
                         step = {"action": action["type"], "parameters": action["parameters"]}
                         # Execute!
                         exec_result = await plugin.execute(step, {})
                         execution_results.append(exec_result)
                 
                 # Construct response with execution results
                 return AgentResponse(
                     response="Meeting created! Redirecting you now...",
                     intent=classified_intent,
                     plan=plan,
                     result={"execution_results": execution_results},
                     requires_confirmation=False, # Done!
                     session_id=session.session_id,
                     stage_type="completed"
                 )

        return AgentResponse(
            response=stage_data.get("question", "Please make a selection:"),
            intent=classified_intent,
            plan={},
            result={},
            requires_selection=True,
            session_id=session.session_id,
            options=stage_data.get("options", []),
            stage_type=current_stage.stage_type
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_simple_confirmation(message: str, intent: Dict, confirmation_manager):
    """Create a simple confirmation for non-complex requests"""
    agent_manager = AgentManager()
    result = await agent_manager.process_intent(message, "default", {})
    
    session_id = str(uuid.uuid4())
    confirmation_request = confirmation_manager.create_confirmation_request(
        session_id=session_id,
        plan=result.get("plan", {}),
        user_input=message
    )
    
    return AgentResponse(
        response=confirmation_request["message"],
        intent=intent,
        plan=result.get("plan", {}),
        result={},
        requires_confirmation=True,
        session_id=session_id,
        pending_actions=confirmation_request["actions"]
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
                
                return {
                    "status": "next_stage",
                    "response": next_stage_data.get("question", "Please make a selection:"),
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
    
    message = f"🎉 Great! Here's your complete plan for {destination}:\n\n"
    
    if accommodation:
        message += f"🏨 **Accommodation**: {accommodation.get('name', 'Resort')}\n"
        if accommodation.get('price'):
            message += f"   Price: {accommodation.get('price')}\n"
    
    if activities:
        message += f"\n🎯 **Activities**:\n"
        for activity in activities:
            message += f"   • {activity.get('name', 'Activity')}\n"
    
    message += "\n📋 **I will execute these actions**:\n"
    
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
