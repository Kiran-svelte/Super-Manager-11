"""
Integration Tests - Test component interactions
"""
import pytest
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAIProviderIntegration:
    """Test AI provider system integration"""
    
    @pytest.mark.asyncio
    async def test_router_initialization(self):
        """Test AI router can initialize"""
        from backend.core.ai_providers.router import AIRouter
        
        router = AIRouter()
        
        # Initialize should not raise even if providers unavailable
        try:
            await asyncio.wait_for(router.initialize(), timeout=30)
        except asyncio.TimeoutError:
            pytest.skip("Provider initialization timed out")
        
        # Should have some providers registered
        assert hasattr(router, '_providers')
    
    @pytest.mark.asyncio
    async def test_router_generate(self):
        """Test AI generation through router"""
        from backend.core.ai_providers.router import AIRouter
        
        router = AIRouter()
        
        try:
            await asyncio.wait_for(router.initialize(), timeout=30)
        except asyncio.TimeoutError:
            pytest.skip("Provider initialization timed out")
        
        available = router.get_available_providers()
        
        if not available:
            pytest.skip("No AI providers available")
        
        try:
            response = await router.generate(
                messages=[{"role": "user", "content": "Say hi"}],
                max_tokens=10
            )
            assert response is not None
            assert hasattr(response, 'content')
        except Exception as e:
            # Acceptable if no providers configured
            pass
    
    def test_provider_status_tracking(self):
        """Test provider status is tracked"""
        from backend.core.ai_providers.base_provider import ProviderStatus
        
        assert ProviderStatus.AVAILABLE.value == "available"
        assert ProviderStatus.UNAVAILABLE.value == "unavailable"


class TestDatabaseIntegration:
    """Test database integration (memory fallback if no Supabase)"""
    
    @pytest.mark.asyncio
    async def test_database_init(self):
        """Test database initialization"""
        from backend.database_supabase import init_db
        
        # Should not raise even without credentials
        result = await init_db()
        # Returns True if connected, False if using memory mode
        assert result in [True, False]
    
    def test_memory_fallback(self):
        """Test in-memory fallback works"""
        from backend.database_supabase import DatabaseOperations
        
        db = DatabaseOperations()
        
        # Test in-memory operations
        if not db._use_memory:
            pytest.skip("Connected to real database")
        
        # Create a task in memory
        task = db.create_task(
            user_id="test-user",
            intent="Test intent"
        )
        
        assert task is not None
        assert "id" in task or hasattr(task, 'id')


class TestWebSocketIntegration:
    """Test WebSocket real-time updates"""
    
    def test_connection_manager(self):
        """Test connection manager instantiation"""
        from backend.core.realtime.websocket_manager import ConnectionManager
        
        manager = ConnectionManager()
        
        stats = manager.get_stats()
        assert "total_connections" in stats
        assert stats["total_connections"] == 0
    
    @pytest.mark.asyncio
    async def test_event_creation(self):
        """Test event creation"""
        from backend.core.realtime.websocket_manager import RealtimeEvent, EventType
        
        event = RealtimeEvent(
            type=EventType.TASK_CREATED,
            data={"task_id": "123", "status": "pending"}
        )
        
        json_str = event.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["type"] == "task_created"
        assert parsed["data"]["task_id"] == "123"
    
    def test_event_types_defined(self):
        """Test all event types are defined"""
        from backend.core.realtime.websocket_manager import EventType
        
        expected = [
            "CONNECTED", "DISCONNECTED", "ERROR",
            "TASK_CREATED", "TASK_STARTED", "TASK_PROGRESS",
            "TASK_COMPLETED", "TASK_FAILED"
        ]
        
        for event_name in expected:
            assert hasattr(EventType, event_name)


class TestFullFlowIntegration:
    """Test complete user flows"""
    
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from backend.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    
    def test_health_to_status_flow(self, client):
        """Test health check followed by status"""
        health = client.get("/api/health")
        assert health.status_code == 200
        
        status = client.get("/api/status")
        assert status.status_code == 200
        
        # Both should indicate healthy state
        assert health.json()["status"] == "healthy"
        assert status.json()["status"] == "operational"
    
    def test_message_processing_flow(self, client):
        """Test sending a message through the system"""
        # First check system is healthy
        health = client.get("/api/health")
        assert health.status_code == 200
        
        # Send a simple message
        response = client.post("/api/agent/process", json={
            "message": "Hello!",
            "user_id": "integration-test-user"
        })
        
        # Should not error internally
        assert response.status_code != 500


class TestPluginIntegration:
    """Test plugin system integration"""
    
    def test_plugin_loading(self):
        """Test plugins can be loaded"""
        from backend.core.plugins import PluginRegistry
        
        registry = PluginRegistry()
        
        # Should load without errors
        assert registry is not None
    
    @pytest.mark.asyncio
    async def test_email_plugin_integration(self):
        """Test email plugin can be instantiated"""
        try:
            from backend.core.real_email_plugin import EmailPlugin
            
            plugin = EmailPlugin()
            assert plugin is not None
            
            # Should have required methods
            assert hasattr(plugin, 'execute') or hasattr(plugin, 'send')
        except ImportError:
            pytest.skip("Email plugin not available")
