"""
Memory API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional, Dict, List

from ..core.memory import MemoryManager

router = APIRouter()

class MemoryRequest(BaseModel):
    key: str
    value: Any
    context: Optional[Dict] = None

class MemoryResponse(BaseModel):
    key: str
    value: Any
    context: Dict
    updated_at: str

@router.post("/", response_model=MemoryResponse)
async def set_memory(
    user_id: str,
    request: MemoryRequest
):
    """Store memory"""
    memory_manager = MemoryManager()
    await memory_manager.set_memory(user_id, request.key, request.value, request.context or {})
    
    memory = await memory_manager.get_memory(user_id, request.key)
    
    return MemoryResponse(
        key=request.key,
        value=memory,
        context=request.context or {},
        updated_at="now"
    )

@router.get("/{key}")
async def get_memory(
    user_id: str,
    key: str
):
    """Get memory by key"""
    memory_manager = MemoryManager()
    memory = await memory_manager.get_memory(user_id, key)
    
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"key": key, "value": memory}

@router.get("/")
async def get_all_memories(
    user_id: str
):
    """Get all user memories"""
    memory_manager = MemoryManager()
    preferences = await memory_manager.get_user_preferences(user_id)
    return preferences

@router.get("/search/{query}")
async def search_memories(
    user_id: str,
    query: str
):
    """Search memories"""
    memory_manager = MemoryManager()
    results = await memory_manager.search_memories(user_id, query)
    return results
