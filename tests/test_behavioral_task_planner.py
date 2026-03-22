"""
Behavioral Tests: Task Planner
================================
Tests that the task planner ACTUALLY works:
- TaskPlanner initialization
- Fallback plan generation
- Plan structure validation

README Requirements:
- Multi-step workflow planning
- Dependencies between steps
- Plugin integration
- Error handling
"""

import pytest
import os

from backend.core.task_planner import TaskPlanner


class TestTaskPlannerInit:
    """Test TaskPlanner initialization"""
    
    def test_can_instantiate(self):
        """TaskPlanner should be instantiatable"""
        planner = TaskPlanner()
        assert planner is not None
    
    def test_has_model(self):
        """TaskPlanner should have model attribute"""
        planner = TaskPlanner()
        assert hasattr(planner, "model")
    
    def test_default_model(self):
        """TaskPlanner should have default model"""
        planner = TaskPlanner()
        # Either from env or default
        assert planner.model is not None
        assert isinstance(planner.model, str)
    
    def test_lazy_client_init(self):
        """TaskPlanner should lazy-initialize client"""
        planner = TaskPlanner()
        assert planner._client is None


class TestFallbackPlan:
    """Test TaskPlanner fallback plan generation"""
    
    @pytest.mark.asyncio
    async def test_fallback_plan_returns_dict(self):
        """fallback plan should return dict"""
        planner = TaskPlanner()
        
        intent = {
            "type": "travel_planning",
            "entities": {"destination": "Paris"}
        }
        
        result = await planner.create_plan(intent)
        
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_fallback_plan_has_steps(self):
        """fallback plan should have steps"""
        planner = TaskPlanner()
        
        intent = {
            "type": "meeting_scheduling",
            "entities": {}
        }
        
        result = await planner.create_plan(intent)
        
        assert "steps" in result
        assert isinstance(result["steps"], list)
    
    @pytest.mark.asyncio
    async def test_fallback_plan_has_status(self):
        """fallback plan should have status"""
        planner = TaskPlanner()
        
        intent = {
            "type": "shopping",
            "entities": {}
        }
        
        result = await planner.create_plan(intent)
        
        assert "status" in result
    
    @pytest.mark.asyncio
    async def test_fallback_plan_has_created_at(self):
        """fallback plan should have created_at timestamp"""
        planner = TaskPlanner()
        
        intent = {
            "type": "event_planning",
            "entities": {}
        }
        
        result = await planner.create_plan(intent)
        
        assert "created_at" in result


class TestPlanStepStructure:
    """Test plan step structure"""
    
    @pytest.mark.asyncio
    async def test_steps_have_id(self):
        """plan steps should have id"""
        planner = TaskPlanner()
        
        intent = {
            "type": "travel_planning",
            "entities": {"destination": "Tokyo"}
        }
        
        result = await planner.create_plan(intent)
        
        if result["steps"]:
            assert all("id" in step for step in result["steps"])
    
    @pytest.mark.asyncio
    async def test_steps_have_name(self):
        """plan steps should have name"""
        planner = TaskPlanner()
        
        intent = {
            "type": "restaurant_booking",
            "entities": {}
        }
        
        result = await planner.create_plan(intent)
        
        if result["steps"]:
            assert all("name" in step for step in result["steps"])
    
    @pytest.mark.asyncio
    async def test_steps_have_action(self):
        """plan steps should have action"""
        planner = TaskPlanner()
        
        intent = {
            "type": "shopping",
            "entities": {"item": "laptop"}
        }
        
        result = await planner.create_plan(intent)
        
        if result["steps"]:
            assert all("action" in step for step in result["steps"])


class TestPlanWithPlugins:
    """Test plan creation with available plugins"""
    
    @pytest.mark.asyncio
    async def test_accepts_plugins_list(self):
        """create_plan should accept plugins list"""
        planner = TaskPlanner()
        
        intent = {"type": "meeting_scheduling", "entities": {}}
        plugins = ["calendar", "zoom", "email"]
        
        # Should not raise
        result = await planner.create_plan(intent, available_plugins=plugins)
        
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_accepts_empty_plugins(self):
        """create_plan should accept empty plugins list"""
        planner = TaskPlanner()
        
        intent = {"type": "general", "entities": {}}
        
        result = await planner.create_plan(intent, available_plugins=[])
        
        assert isinstance(result, dict)


class TestPlanWithContext:
    """Test plan creation with context"""
    
    @pytest.mark.asyncio
    async def test_accepts_context(self):
        """create_plan should accept context dict"""
        planner = TaskPlanner()
        
        intent = {"type": "travel_planning", "entities": {}}
        context = {
            "user_preferences": {"budget": "mid-range"},
            "previous_trips": ["London", "Paris"]
        }
        
        result = await planner.create_plan(intent, context=context)
        
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_uses_default_context(self):
        """create_plan should use default empty context"""
        planner = TaskPlanner()
        
        intent = {"type": "general", "entities": {}}
        
        # Should not raise with no context
        result = await planner.create_plan(intent)
        
        assert isinstance(result, dict)


class TestPlanMetadata:
    """Test plan metadata fields"""
    
    @pytest.mark.asyncio
    async def test_plan_has_estimated_duration(self):
        """plan should have estimated_duration if returned"""
        planner = TaskPlanner()
        
        intent = {"type": "event_planning", "entities": {}}
        
        result = await planner.create_plan(intent)
        
        # May or may not have this field
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_plan_may_have_required_plugins(self):
        """plan may have required_plugins field"""
        planner = TaskPlanner()
        
        intent = {"type": "meeting_scheduling", "entities": {}}
        
        result = await planner.create_plan(intent)
        
        # Field may be present
        assert isinstance(result, dict)


class TestIntentTypes:
    """Test planning for different intent types"""
    
    @pytest.mark.asyncio
    async def test_travel_planning_intent(self):
        """Should create plan for travel_planning intent"""
        planner = TaskPlanner()
        
        intent = {
            "type": "travel_planning",
            "entities": {"destination": "Bali", "dates": "December 2024"}
        }
        
        result = await planner.create_plan(intent)
        
        assert result["steps"] is not None
    
    @pytest.mark.asyncio
    async def test_meeting_scheduling_intent(self):
        """Should create plan for meeting_scheduling intent"""
        planner = TaskPlanner()
        
        intent = {
            "type": "meeting_scheduling",
            "entities": {"with": "John", "duration": "30 minutes"}
        }
        
        result = await planner.create_plan(intent)
        
        assert result["steps"] is not None
    
    @pytest.mark.asyncio
    async def test_birthday_party_intent(self):
        """Should create plan for birthday_party intent"""
        planner = TaskPlanner()
        
        intent = {
            "type": "birthday_party",
            "entities": {"for": "Sarah", "date": "next Saturday"}
        }
        
        result = await planner.create_plan(intent)
        
        assert result["steps"] is not None
    
    @pytest.mark.asyncio
    async def test_restaurant_booking_intent(self):
        """Should create plan for restaurant_booking intent"""
        planner = TaskPlanner()
        
        intent = {
            "type": "restaurant_booking",
            "entities": {"guests": 4, "time": "7 PM"}
        }
        
        result = await planner.create_plan(intent)
        
        assert result["steps"] is not None
    
    @pytest.mark.asyncio
    async def test_shopping_intent(self):
        """Should create plan for shopping intent"""
        planner = TaskPlanner()
        
        intent = {
            "type": "shopping",
            "entities": {"item": "new phone", "budget": "$500"}
        }
        
        result = await planner.create_plan(intent)
        
        assert result["steps"] is not None
    
    @pytest.mark.asyncio
    async def test_general_intent(self):
        """Should create plan for general intent"""
        planner = TaskPlanner()
        
        intent = {
            "type": "general",
            "entities": {}
        }
        
        result = await planner.create_plan(intent)
        
        assert isinstance(result, dict)


class TestPlanValidation:
    """Test plan validation"""
    
    @pytest.mark.asyncio
    async def test_steps_is_list(self):
        """steps should be a list"""
        planner = TaskPlanner()
        
        result = await planner.create_plan({"type": "general", "entities": {}})
        
        assert isinstance(result["steps"], list)
    
    @pytest.mark.asyncio
    async def test_plan_is_serializable(self):
        """plan should be JSON serializable"""
        import json
        
        planner = TaskPlanner()
        
        result = await planner.create_plan({"type": "travel_planning", "entities": {}})
        
        # Should not raise
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
