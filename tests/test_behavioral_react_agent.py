"""
Behavioral Tests: ReAct Agent
==============================
Tests that the ReAct agent module ACTUALLY works:
- AgentEvent dataclass
- PendingConfirmation dataclass
- ReactAgent class
- GROQ configuration

README Requirements:
- ReAct pattern implementation
- Tool execution
- Agent reasoning
"""

import pytest
from dataclasses import is_dataclass

from backend.core.react_agent import (
    GROQ_URL,
    GROQ_MODEL,
    AgentEvent,
    PendingConfirmation,
    ReactAgent,
)


class TestGroqConfiguration:
    """Test Groq configuration"""
    
    def test_groq_url_is_string(self):
        """GROQ_URL should be string"""
        assert isinstance(GROQ_URL, str)
    
    def test_groq_url_is_groq_endpoint(self):
        """GROQ_URL should be groq endpoint"""
        assert "groq.com" in GROQ_URL
    
    def test_groq_model_is_string(self):
        """GROQ_MODEL should be string"""
        assert isinstance(GROQ_MODEL, str)


class TestAgentEventDataclass:
    """Test AgentEvent dataclass"""
    
    def test_is_dataclass(self):
        """AgentEvent should be a dataclass"""
        assert is_dataclass(AgentEvent)
    
    def test_can_create(self):
        """AgentEvent should be creatable"""
        event = AgentEvent(type="thinking", content="processing...")
        assert event is not None
    
    def test_has_type(self):
        """Should have type"""
        event = AgentEvent(type="tool_call", content="calling tool")
        assert event.type == "tool_call"
    
    def test_has_content(self):
        """Should have content"""
        event = AgentEvent(type="answer", content="Here is the answer")
        assert event.content == "Here is the answer"
    
    def test_default_data_empty(self):
        """Default data should be empty dict"""
        event = AgentEvent(type="test", content="test")
        assert event.data == {}
    
    def test_can_set_data(self):
        """Should accept data dict"""
        event = AgentEvent(type="tool_result", content="result", data={"key": "value"})
        assert event.data == {"key": "value"}


class TestAgentEventTypes:
    """Test common AgentEvent types"""
    
    def test_thinking_type(self):
        """Should support thinking type"""
        event = AgentEvent(type="thinking", content="Reasoning about the task")
        assert event.type == "thinking"
    
    def test_tool_call_type(self):
        """Should support tool_call type"""
        event = AgentEvent(type="tool_call", content="Calling web_search")
        assert event.type == "tool_call"
    
    def test_tool_result_type(self):
        """Should support tool_result type"""
        event = AgentEvent(type="tool_result", content="Search results...")
        assert event.type == "tool_result"
    
    def test_answer_type(self):
        """Should support answer type"""
        event = AgentEvent(type="answer", content="Final answer")
        assert event.type == "answer"
    
    def test_confirm_needed_type(self):
        """Should support confirm_needed type"""
        event = AgentEvent(type="confirm_needed", content="Confirm send email?")
        assert event.type == "confirm_needed"
    
    def test_error_type(self):
        """Should support error type"""
        event = AgentEvent(type="error", content="Something went wrong")
        assert event.type == "error"


class TestAgentEventToDict:
    """Test AgentEvent to_dict method"""
    
    def test_has_to_dict_method(self):
        """Should have to_dict method"""
        event = AgentEvent(type="test", content="test")
        assert hasattr(event, "to_dict")
        assert callable(event.to_dict)
    
    def test_to_dict_returns_dict(self):
        """to_dict should return dict"""
        event = AgentEvent(type="test", content="hello")
        result = event.to_dict()
        assert isinstance(result, dict)
    
    def test_to_dict_includes_all_fields(self):
        """to_dict should include all fields"""
        event = AgentEvent(type="answer", content="result", data={"x": 1})
        result = event.to_dict()
        assert result["type"] == "answer"
        assert result["content"] == "result"
        assert result["data"] == {"x": 1}


class TestPendingConfirmationDataclass:
    """Test PendingConfirmation dataclass"""
    
    def test_is_dataclass(self):
        """PendingConfirmation should be a dataclass"""
        assert is_dataclass(PendingConfirmation)
    
    def test_can_create(self):
        """PendingConfirmation should be creatable"""
        pending = PendingConfirmation(
            tool_name="send_email",
            tool_params={"to": "test@test.com"},
            thinking="Need to send email",
            scratchpad=[],
            history=[]
        )
        assert pending is not None
    
    def test_has_tool_name(self):
        """Should have tool_name"""
        pending = PendingConfirmation(
            tool_name="web_search",
            tool_params={},
            thinking="",
            scratchpad=[],
            history=[]
        )
        assert pending.tool_name == "web_search"
    
    def test_has_tool_params(self):
        """Should have tool_params"""
        pending = PendingConfirmation(
            tool_name="tool",
            tool_params={"query": "test"},
            thinking="",
            scratchpad=[],
            history=[]
        )
        assert pending.tool_params == {"query": "test"}
    
    def test_has_thinking(self):
        """Should have thinking (reasoning)"""
        pending = PendingConfirmation(
            tool_name="tool",
            tool_params={},
            thinking="I need to search for information",
            scratchpad=[],
            history=[]
        )
        assert pending.thinking == "I need to search for information"
    
    def test_has_scratchpad(self):
        """Should have scratchpad"""
        pending = PendingConfirmation(
            tool_name="tool",
            tool_params={},
            thinking="",
            scratchpad=[{"step": "1", "result": "data"}],
            history=[]
        )
        assert len(pending.scratchpad) == 1
    
    def test_has_history(self):
        """Should have history"""
        pending = PendingConfirmation(
            tool_name="tool",
            tool_params={},
            thinking="",
            scratchpad=[],
            history=[{"role": "user", "content": "hello"}]
        )
        assert len(pending.history) == 1


class TestReactAgentInit:
    """Test ReactAgent initialization"""
    
    def test_can_instantiate(self):
        """ReactAgent should be instantiatable"""
        agent = ReactAgent()
        assert agent is not None
    
    def test_has_tools(self):
        """Should have tools attribute"""
        agent = ReactAgent()
        assert hasattr(agent, "tools")
    
    def test_has_max_steps(self):
        """Should have max_steps attribute"""
        agent = ReactAgent()
        assert hasattr(agent, "max_steps")
        assert agent.max_steps == 10
    
    def test_has_groq_key(self):
        """Should have groq_key attribute"""
        agent = ReactAgent()
        assert hasattr(agent, "groq_key")


class TestReactAgentMethods:
    """Test ReactAgent methods"""
    
    def test_has_build_system_prompt_method(self):
        """Should have _build_system_prompt method"""
        agent = ReactAgent()
        assert hasattr(agent, "_build_system_prompt")
        assert callable(agent._build_system_prompt)
    
    def test_has_run_method(self):
        """Should have run method"""
        agent = ReactAgent()
        assert hasattr(agent, "run")
        assert callable(agent.run)
    
    def test_run_is_async_generator(self):
        """run should be async generator"""
        import inspect
        agent = ReactAgent()
        assert inspect.isasyncgenfunction(agent.run)


class TestReactAgentSystemPrompt:
    """Test ReactAgent system prompt generation"""
    
    def test_build_system_prompt_returns_string(self):
        """_build_system_prompt should return string"""
        agent = ReactAgent()
        result = agent._build_system_prompt()
        assert isinstance(result, str)
    
    def test_system_prompt_includes_max_steps(self):
        """System prompt should mention max steps"""
        agent = ReactAgent()
        result = agent._build_system_prompt()
        assert str(agent.max_steps) in result
    
    def test_system_prompt_includes_identity(self):
        """System prompt should include AI identity"""
        agent = ReactAgent()
        result = agent._build_system_prompt()
        assert "Super Manager" in result or "assistant" in result.lower()
    
    def test_system_prompt_with_feedback(self):
        """System prompt should include feedback context"""
        agent = ReactAgent()
        result = agent._build_system_prompt(feedback_context="User liked detailed answers")
        assert "feedback" in result.lower()


class TestReactAgentToolRegistry:
    """Test ReactAgent tool registry integration"""
    
    def test_accepts_custom_registry(self):
        """Should accept custom tool registry"""
        from backend.core.tools import ToolRegistry
        custom_registry = ToolRegistry()
        agent = ReactAgent(tool_registry=custom_registry)
        assert agent.tools is custom_registry
    
    def test_creates_default_registry(self):
        """Should create default registry if none provided"""
        agent = ReactAgent()
        assert agent.tools is not None


class TestAgentEventSerialization:
    """Test AgentEvent serialization for streaming"""
    
    def test_event_json_serializable(self):
        """AgentEvent to_dict should be JSON serializable"""
        import json
        event = AgentEvent(
            type="tool_call",
            content="Calling search",
            data={"tool": "web_search", "query": "test"}
        )
        # Should not raise
        json_str = json.dumps(event.to_dict())
        assert "tool_call" in json_str
    
    def test_nested_data_serializable(self):
        """Nested data should be serializable"""
        import json
        event = AgentEvent(
            type="result",
            content="Done",
            data={
                "results": [{"title": "Test", "url": "http://test.com"}],
                "count": 1
            }
        )
        json_str = json.dumps(event.to_dict())
        assert "results" in json_str
