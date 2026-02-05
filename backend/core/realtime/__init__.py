"""
Realtime Module - WebSocket support for live updates
"""
from .websocket_manager import (
    ConnectionManager,
    RealtimeEvent,
    EventType,
    get_connection_manager,
    websocket_endpoint,
    emit_task_created,
    emit_task_progress,
    emit_task_completed,
    emit_task_failed,
    emit_ai_thinking,
    emit_ai_streaming,
    emit_plugin_executing,
    emit_plugin_result
)

__all__ = [
    'ConnectionManager',
    'RealtimeEvent',
    'EventType',
    'get_connection_manager',
    'websocket_endpoint',
    'emit_task_created',
    'emit_task_progress',
    'emit_task_completed',
    'emit_task_failed',
    'emit_ai_thinking',
    'emit_ai_streaming',
    'emit_plugin_executing',
    'emit_plugin_result'
]
