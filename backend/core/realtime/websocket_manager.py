"""
WebSocket Real-time Updates
Provides live progress updates for task execution
"""
from __future__ import annotations

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of real-time events"""
    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    
    # Task events
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # Workflow events
    WORKFLOW_CREATED = "workflow_created"
    STAGE_STARTED = "stage_started"
    STAGE_WAITING = "stage_waiting"
    STAGE_COMPLETED = "stage_completed"
    
    # Plugin events
    PLUGIN_EXECUTING = "plugin_executing"
    PLUGIN_RESULT = "plugin_result"
    
    # AI events
    AI_THINKING = "ai_thinking"
    AI_STREAMING = "ai_streaming"
    AI_COMPLETE = "ai_complete"


@dataclass
class RealtimeEvent:
    """A real-time event to send to clients"""
    type: EventType
    data: Dict[str, Any]
    timestamp: str = None
    user_id: Optional[str] = None
    task_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "task_id": self.task_id
        })


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    Supports user-specific and broadcast messaging.
    """
    
    def __init__(self):
        # user_id -> set of websockets
        self._user_connections: Dict[str, Set[WebSocket]] = {}
        # All active connections
        self._all_connections: Set[WebSocket] = set()
        # Connection metadata
        self._connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str = "anonymous"
    ) -> bool:
        """Accept a new WebSocket connection"""
        try:
            await websocket.accept()
            
            async with self._lock:
                # Track connection
                self._all_connections.add(websocket)
                
                # Track by user
                if user_id not in self._user_connections:
                    self._user_connections[user_id] = set()
                self._user_connections[user_id].add(websocket)
                
                # Store metadata
                self._connection_info[websocket] = {
                    "user_id": user_id,
                    "connected_at": datetime.utcnow().isoformat()
                }
            
            # Send connection confirmation
            await self.send_to_socket(
                websocket,
                RealtimeEvent(
                    type=EventType.CONNECTED,
                    data={"message": "Connected to Super Manager real-time updates"},
                    user_id=user_id
                )
            )
            
            logger.info(f"[WS] User {user_id} connected. Total: {len(self._all_connections)}")
            return True
            
        except Exception as e:
            logger.error(f"[WS] Connection error: {e}")
            return False
    
    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        async with self._lock:
            # Get user info
            info = self._connection_info.get(websocket, {})
            user_id = info.get("user_id", "anonymous")
            
            # Remove from tracking
            self._all_connections.discard(websocket)
            
            if user_id in self._user_connections:
                self._user_connections[user_id].discard(websocket)
                if not self._user_connections[user_id]:
                    del self._user_connections[user_id]
            
            if websocket in self._connection_info:
                del self._connection_info[websocket]
        
        logger.info(f"[WS] User {user_id} disconnected. Total: {len(self._all_connections)}")
    
    async def send_to_socket(
        self,
        websocket: WebSocket,
        event: RealtimeEvent
    ):
        """Send event to specific socket"""
        try:
            await websocket.send_text(event.to_json())
        except Exception as e:
            logger.warning(f"[WS] Send error: {e}")
            await self.disconnect(websocket)
    
    async def send_to_user(
        self,
        user_id: str,
        event: RealtimeEvent
    ):
        """Send event to all connections of a specific user"""
        event.user_id = user_id
        
        connections = self._user_connections.get(user_id, set()).copy()
        
        if not connections:
            logger.debug(f"[WS] No connections for user {user_id}")
            return
        
        # Send to all user's connections
        tasks = [
            self.send_to_socket(ws, event)
            for ws in connections
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast(self, event: RealtimeEvent):
        """Broadcast event to all connected clients"""
        connections = self._all_connections.copy()
        
        tasks = [
            self.send_to_socket(ws, event)
            for ws in connections
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self._all_connections),
            "unique_users": len(self._user_connections),
            "users": list(self._user_connections.keys())
        }


# Global connection manager
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get connection manager singleton"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


# =============================================================================
# Event Helper Functions
# =============================================================================

async def emit_task_created(user_id: str, task_id: str, intent: str):
    """Emit task created event"""
    manager = get_connection_manager()
    await manager.send_to_user(
        user_id,
        RealtimeEvent(
            type=EventType.TASK_CREATED,
            data={"task_id": task_id, "intent": intent},
            task_id=task_id
        )
    )


async def emit_task_progress(
    user_id: str,
    task_id: str,
    progress: int,
    message: str,
    stage: Optional[str] = None
):
    """Emit task progress update"""
    manager = get_connection_manager()
    await manager.send_to_user(
        user_id,
        RealtimeEvent(
            type=EventType.TASK_PROGRESS,
            data={
                "progress": progress,
                "message": message,
                "stage": stage
            },
            task_id=task_id
        )
    )


async def emit_task_completed(
    user_id: str,
    task_id: str,
    result: Dict[str, Any]
):
    """Emit task completed event"""
    manager = get_connection_manager()
    await manager.send_to_user(
        user_id,
        RealtimeEvent(
            type=EventType.TASK_COMPLETED,
            data={"result": result},
            task_id=task_id
        )
    )


async def emit_task_failed(
    user_id: str,
    task_id: str,
    error: str
):
    """Emit task failed event"""
    manager = get_connection_manager()
    await manager.send_to_user(
        user_id,
        RealtimeEvent(
            type=EventType.TASK_FAILED,
            data={"error": error},
            task_id=task_id
        )
    )


async def emit_ai_thinking(user_id: str, message: str = "Processing..."):
    """Emit AI thinking indicator"""
    manager = get_connection_manager()
    await manager.send_to_user(
        user_id,
        RealtimeEvent(
            type=EventType.AI_THINKING,
            data={"message": message}
        )
    )


async def emit_ai_streaming(user_id: str, chunk: str, task_id: Optional[str] = None):
    """Emit AI streaming chunk"""
    manager = get_connection_manager()
    await manager.send_to_user(
        user_id,
        RealtimeEvent(
            type=EventType.AI_STREAMING,
            data={"chunk": chunk},
            task_id=task_id
        )
    )


async def emit_plugin_executing(
    user_id: str,
    task_id: str,
    plugin: str,
    action: str
):
    """Emit plugin execution started"""
    manager = get_connection_manager()
    await manager.send_to_user(
        user_id,
        RealtimeEvent(
            type=EventType.PLUGIN_EXECUTING,
            data={"plugin": plugin, "action": action},
            task_id=task_id
        )
    )


async def emit_plugin_result(
    user_id: str,
    task_id: str,
    plugin: str,
    success: bool,
    result: Any
):
    """Emit plugin execution result"""
    manager = get_connection_manager()
    await manager.send_to_user(
        user_id,
        RealtimeEvent(
            type=EventType.PLUGIN_RESULT,
            data={
                "plugin": plugin,
                "success": success,
                "result": result
            },
            task_id=task_id
        )
    )


# =============================================================================
# WebSocket Route Handler
# =============================================================================

async def websocket_endpoint(websocket: WebSocket, user_id: str = "anonymous"):
    """
    WebSocket endpoint handler for FastAPI.
    
    Usage in routes:
        @app.websocket("/ws/{user_id}")
        async def ws_route(websocket: WebSocket, user_id: str):
            await websocket_endpoint(websocket, user_id)
    """
    manager = get_connection_manager()
    
    if not await manager.connect(websocket, user_id):
        return
    
    try:
        while True:
            # Receive and handle client messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get("type", "")
                
                # Handle ping/pong for keepalive
                if msg_type == "ping":
                    await manager.send_to_socket(
                        websocket,
                        RealtimeEvent(
                            type=EventType.CONNECTED,
                            data={"pong": True}
                        )
                    )
                
                # Handle subscription changes
                elif msg_type == "subscribe":
                    task_id = message.get("task_id")
                    if task_id:
                        # Add task subscription (could extend for task-specific events)
                        pass
                
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"[WS] Error in websocket handler: {e}")
        await manager.disconnect(websocket)
