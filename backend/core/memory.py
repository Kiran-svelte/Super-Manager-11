"""
Memory and Personalization System
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# Try Supabase first, fall back to Firebase
try:
    from ..database_supabase import (
        get_memory_by_key, get_memories_by_user, create_memory, 
        update_memory, search_memories as db_search_memories, Memory
    )
except ImportError:
    from ..database import (
        get_memory_by_key, get_memories_by_user, create_memory, 
        update_memory, search_memories as db_search_memories, Memory
    )

class MemoryManager:
    """Manages user memory and personalization"""
    
    def __init__(self):
        self.cache = {}
    
    async def get_memory(self, user_id: str, key: str) -> Optional[Any]:
        """Retrieve memory by key"""
        # Check cache first
        cache_key = f"{user_id}:{key}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Query Firestore
        memory = await get_memory_by_key(user_id, key)
        
        if memory:
            try:
                value = json.loads(memory.value) if isinstance(memory.value, str) else memory.value
            except:
                value = memory.value
            self.cache[cache_key] = value
            return value
        
        return None
    
    async def set_memory(self, user_id: str, key: str, value: Any, context: Dict = None):
        """Store memory"""
        context = context or {}
        
        # Check if exists
        existing = await get_memory_by_key(user_id, key)
        
        if existing:
            # Update existing
            value_str = json.dumps(value) if not isinstance(value, str) else value
            await update_memory(existing.id, {
                'value': value_str,
                'context': context
            })
        else:
            # Create new
            memory = Memory(
                user_id=user_id,
                key=key,
                value=value,
                context=context
            )
            await create_memory(memory)
        
        # Update cache
        cache_key = f"{user_id}:{key}"
        self.cache[cache_key] = value
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all user preferences"""
        memories = await get_memories_by_user(user_id)
        
        preferences = {}
        for memory in memories:
            try:
                value = json.loads(memory.value) if isinstance(memory.value, str) else memory.value
                preferences[memory.key] = value
            except:
                preferences[memory.key] = memory.value
        
        return preferences
    
    async def search_memories(self, user_id: str, query: str) -> List[Dict]:
        """Search memories by query"""
        matching = await db_search_memories(user_id, query)
        
        results = []
        for memory in matching:
            try:
                value = json.loads(memory.value) if isinstance(memory.value, str) else memory.value
            except:
                value = memory.value
            
            results.append({
                "key": memory.key,
                "value": value,
                "context": memory.context,
                "updated_at": memory.updated_at.isoformat()
            })
        
        return results
    
    async def get_context(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get recent context for user"""
        try:
            preferences = await self.get_user_preferences(user_id)
            
            # Get recent memories
            all_memories = await get_memories_by_user(user_id)
            recent = sorted(all_memories, key=lambda m: m.updated_at, reverse=True)[:limit]
            
            return {
                "preferences": preferences,
                "recent_memories": [
                    {
                        "key": m.key,
                        "value": json.loads(m.value) if isinstance(m.value, str) else m.value,
                        "updated_at": m.updated_at.isoformat()
                    }
                    for m in recent
                ]
            }
        except Exception as e:
            # If Firebase not available, return empty context
            return {"preferences": {}, "recent_memories": []}
