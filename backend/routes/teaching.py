"""
Teaching Mode Routes - Learn Workflows from User Demonstrations
================================================================
Exposes the TeachingMode functionality via REST API.

Endpoints:
- POST /api/teach/record - Save a recorded workflow
- GET /api/teach/workflows - List all saved workflows
- POST /api/teach/replay - Replay a saved workflow
- DELETE /api/teach/workflow/{name} - Delete a workflow
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.core.teaching_mode import get_teaching_mode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teach", tags=["teaching"])


# =============================================================================
# Pydantic Models
# =============================================================================

class RecordWorkflowRequest(BaseModel):
    """Request to save a recorded workflow"""
    session_id: str = Field(..., min_length=1)
    task_description: str = Field(default="Recorded workflow")
    actions: List[Dict[str, Any]] = Field(default_factory=list)


class ReplayWorkflowRequest(BaseModel):
    """Request to replay a saved workflow"""
    workflow_name: str = Field(..., min_length=1)
    params: Dict[str, str] = Field(default_factory=dict)


# =============================================================================
# Routes
# =============================================================================

@router.post("/record")
async def record_workflow(request: RecordWorkflowRequest):
    """
    Save a recorded workflow from frontend action recorder.
    
    The frontend captures user actions (clicks, inputs, navigations)
    and sends them here to be analyzed and saved as a replayable workflow.
    """
    try:
        teaching_mode = get_teaching_mode()
        
        # First start a recording session (if not already started)
        teaching_mode.start_recording(request.session_id, request.task_description)
        
        # Then stop and process the recorded actions
        result = teaching_mode.stop_recording(request.session_id, request.actions)
        
        logger.info(f"[TEACH] Workflow recorded: {result.get('workflow_name', 'unknown')}")
        
        return result
        
    except Exception as e:
        logger.error(f"[TEACH] Record error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows")
async def list_workflows():
    """
    List all saved workflows.
    """
    try:
        teaching_mode = get_teaching_mode()
        workflows = teaching_mode.get_workflows()
        
        return {
            "status": "ok",
            "count": len(workflows),
            "workflows": workflows
        }
        
    except Exception as e:
        logger.error(f"[TEACH] List error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/{name}")
async def get_workflow(name: str):
    """
    Get details of a specific workflow.
    """
    try:
        teaching_mode = get_teaching_mode()
        workflow = teaching_mode.get_workflow(name)
        
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")
        
        return {
            "status": "ok",
            "workflow": workflow
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TEACH] Get workflow error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/replay")
async def replay_workflow(request: ReplayWorkflowRequest):
    """
    Replay a saved workflow with given parameters.
    """
    try:
        teaching_mode = get_teaching_mode()
        result = await teaching_mode.replay_workflow(request.workflow_name, request.params)
        
        if not result.success:
            return {
                "status": "error",
                "error": result.error,
                "message": result.output
            }
        
        return {
            "status": "completed",
            "output": result.output,
            "data": result.data
        }
        
    except Exception as e:
        logger.error(f"[TEACH] Replay error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/workflow/{name}")
async def delete_workflow(name: str):
    """
    Delete a saved workflow.
    """
    try:
        teaching_mode = get_teaching_mode()
        deleted = teaching_mode.delete_workflow(name)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")
        
        return {
            "status": "ok",
            "message": f"Workflow '{name}' deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TEACH] Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
