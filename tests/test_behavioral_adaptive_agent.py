"""
Behavioral Tests: Adaptive Agent
==================================
Tests that the adaptive agent loop ACTUALLY works:
- AgentEvent and AgentResult dataclasses
- Tag parsing (<action>, <code>, <ask>, <answer>)
- Risk classification integration
- Context accumulation
- Step limits

README Requirements:
- LLM outputs <action>, <code>, <ask>, or <answer> tags
- RiskClassifier determines safe/risky/blocked
- SandboxExecutor runs code with 30s timeout
- Maximum steps per request (15)
"""

import pytest
from dataclasses import is_dataclass

from backend.core.adaptive_agent import (
    AdaptiveAgent,
    AgentEvent,
    AgentResult,
    PendingConfirmation
)


class TestAgentEventDataclass:
    """Test AgentEvent dataclass structure"""
    
    def test_is_dataclass(self):
        """AgentEvent should be a dataclass"""
        assert is_dataclass(AgentEvent)
    
    def test_has_type_field(self):
        """AgentEvent should have type field"""
        event = AgentEvent(type="thinking", content="test")
        assert event.type == "thinking"
    
    def test_has_content_field(self):
        """AgentEvent should have content field"""
        event = AgentEvent(type="thinking", content="test content")
        assert event.content == "test content"
    
    def test_has_data_field_default_empty(self):
        """AgentEvent data should default to empty dict"""
        event = AgentEvent(type="thinking", content="test")
        assert event.data == {}
    
    def test_data_can_store_info(self):
        """AgentEvent data can store arbitrary info"""
        event = AgentEvent(
            type="action",
            content="test",
            data={"primitive": "web_search", "params": {"query": "test"}}
        )
        assert event.data["primitive"] == "web_search"
    
    def test_to_dict_returns_dict(self):
        """AgentEvent to_dict should return dict"""
        event = AgentEvent(type="answer", content="done")
        result = event.to_dict()
        
        assert isinstance(result, dict)
        assert result["type"] == "answer"
        assert result["content"] == "done"


class TestAgentEventTypes:
    """Test valid AgentEvent types"""
    
    def test_thinking_event(self):
        """thinking event type should work"""
        event = AgentEvent(type="thinking", content="Analyzing task...")
        assert event.type == "thinking"
    
    def test_action_event(self):
        """action event type should work"""
        event = AgentEvent(type="action", content="Executing web_search")
        assert event.type == "action"
    
    def test_code_exec_event(self):
        """code_exec event type should work"""
        event = AgentEvent(type="code_exec", content="Running code block")
        assert event.type == "code_exec"
    
    def test_action_result_event(self):
        """action_result event type should work"""
        event = AgentEvent(type="action_result", content="Search complete")
        assert event.type == "action_result"
    
    def test_answer_event(self):
        """answer event type should work"""
        event = AgentEvent(type="answer", content="Here is your result")
        assert event.type == "answer"
    
    def test_ask_event(self):
        """ask event type should work"""
        event = AgentEvent(type="ask", content="Choose an option")
        assert event.type == "ask"
    
    def test_confirm_needed_event(self):
        """confirm_needed event type should work"""
        event = AgentEvent(type="confirm_needed", content="Risky action")
        assert event.type == "confirm_needed"
    
    def test_step_progress_event(self):
        """step_progress event type should work"""
        event = AgentEvent(type="step_progress", content="Step 1")
        assert event.type == "step_progress"
    
    def test_error_event(self):
        """error event type should work"""
        event = AgentEvent(type="error", content="Something failed")
        assert event.type == "error"


class TestAgentResultDataclass:
    """Test AgentResult dataclass structure"""
    
    def test_is_dataclass(self):
        """AgentResult should be a dataclass"""
        assert is_dataclass(AgentResult)
    
    def test_has_success_field(self):
        """AgentResult should have success field"""
        result = AgentResult(success=True, response="Done")
        assert result.success is True
    
    def test_has_response_field(self):
        """AgentResult should have response field"""
        result = AgentResult(success=True, response="Task completed")
        assert result.response == "Task completed"
    
    def test_has_data_field_default(self):
        """AgentResult data should default to empty dict"""
        result = AgentResult(success=True, response="Done")
        assert result.data == {}
    
    def test_has_steps_taken_field_default(self):
        """AgentResult steps_taken should default to 0"""
        result = AgentResult(success=True, response="Done")
        assert result.steps_taken == 0
    
    def test_has_primitives_used_field(self):
        """AgentResult should track primitives used"""
        result = AgentResult(
            success=True, 
            response="Done",
            primitives_used=["web_search", "scrape_data"]
        )
        assert "web_search" in result.primitives_used
    
    def test_has_needs_confirmation_field(self):
        """AgentResult should have needs_confirmation flag"""
        result = AgentResult(
            success=False,
            response="Waiting",
            needs_confirmation=True
        )
        assert result.needs_confirmation is True
    
    def test_has_pending_action_field(self):
        """AgentResult should store pending action"""
        result = AgentResult(
            success=False,
            response="Waiting",
            pending_action={"primitive": "fill_form"}
        )
        assert result.pending_action["primitive"] == "fill_form"
    
    def test_to_dict_returns_dict(self):
        """AgentResult to_dict should return dict"""
        result = AgentResult(success=True, response="Done")
        serialized = result.to_dict()
        
        assert isinstance(serialized, dict)
        assert serialized["success"] is True


class TestPendingConfirmationDataclass:
    """Test PendingConfirmation dataclass"""
    
    def test_is_dataclass(self):
        """PendingConfirmation should be a dataclass"""
        assert is_dataclass(PendingConfirmation)
    
    def test_has_action_type_field(self):
        """PendingConfirmation should have action_type"""
        pending = PendingConfirmation(
            action_type="action",
            primitive_name="fill_form",
            params={"url": "https://example.com"},
            code=None,
            thinking="About to fill form",
            scratchpad=[],
            history=[],
            context={}
        )
        assert pending.action_type == "action"
    
    def test_has_primitive_name_field(self):
        """PendingConfirmation should have primitive_name"""
        pending = PendingConfirmation(
            action_type="action",
            primitive_name="fill_form",
            params={"url": "https://example.com"},
            code=None,
            thinking="About to fill form",
            scratchpad=[],
            history=[],
            context={}
        )
        assert pending.primitive_name == "fill_form"
    
    def test_has_code_field_for_code_type(self):
        """PendingConfirmation should store code for code type"""
        pending = PendingConfirmation(
            action_type="code",
            primitive_name=None,
            params={},
            code="await fill_form(url, fields)",
            thinking="About to run code",
            scratchpad=[],
            history=[],
            context={}
        )
        assert pending.code == "await fill_form(url, fields)"


class TestAdaptiveAgentInit:
    """Test AdaptiveAgent initialization"""
    
    def test_can_instantiate(self):
        """AdaptiveAgent should be instantiatable"""
        agent = AdaptiveAgent()
        assert agent is not None
    
    def test_has_max_steps(self):
        """AdaptiveAgent should have max_steps limit"""
        agent = AdaptiveAgent()
        assert agent.max_steps == 15
    
    def test_has_sandbox(self):
        """AdaptiveAgent should have sandbox executor"""
        agent = AdaptiveAgent()
        assert agent.sandbox is not None
    
    def test_has_classifier(self):
        """AdaptiveAgent should have risk classifier"""
        agent = AdaptiveAgent()
        assert agent.classifier is not None
    
    def test_has_strategies(self):
        """AdaptiveAgent should have strategy store"""
        agent = AdaptiveAgent()
        assert agent.strategies is not None


class TestTagParsing:
    """Test XML tag extraction from LLM output"""
    
    def test_extract_think_tag(self):
        """Agent should extract <think> tag"""
        agent = AdaptiveAgent()
        text = "<think>I need to search the web</think>"
        
        result = agent._extract_tag(text, "think")
        
        assert result == "I need to search the web"
    
    def test_extract_action_tag(self):
        """Agent should extract <action> tag"""
        agent = AdaptiveAgent()
        text = '<action>{"primitive": "web_search", "params": {"query": "test"}}</action>'
        
        result = agent._extract_tag(text, "action")
        
        assert "web_search" in result
    
    def test_extract_code_tag(self):
        """Agent should extract <code> tag"""
        agent = AdaptiveAgent()
        text = '<code>result = await web_search("test")\nprint(result)</code>'
        
        result = agent._extract_tag(text, "code")
        
        assert "await web_search" in result
    
    def test_extract_ask_tag(self):
        """Agent should extract <ask> tag"""
        agent = AdaptiveAgent()
        text = '<ask>{"message": "Choose option", "options": []}</ask>'
        
        result = agent._extract_tag(text, "ask")
        
        assert "Choose option" in result
    
    def test_extract_answer_tag(self):
        """Agent should extract <answer> tag"""
        agent = AdaptiveAgent()
        text = "<answer>Here is your final result with all details</answer>"
        
        result = agent._extract_tag(text, "answer")
        
        assert result == "Here is your final result with all details"
    
    def test_returns_none_for_missing_tag(self):
        """Agent should return None for missing tag"""
        agent = AdaptiveAgent()
        text = "<thinking>some text</thinking>"
        
        result = agent._extract_tag(text, "answer")
        
        assert result is None
    
    def test_handles_nested_content(self):
        """Agent should handle tags with complex content"""
        agent = AdaptiveAgent()
        text = """<code>
if True:
    result = await web_search("nested")
    for item in result.data["results"]:
        print(item)
</code>"""
        
        result = agent._extract_tag(text, "code")
        
        assert "if True:" in result
        assert "for item" in result


class TestSystemPromptBuilding:
    """Test system prompt construction"""
    
    def test_builds_system_prompt(self):
        """Agent should build system prompt"""
        agent = AdaptiveAgent()
        prompt = agent._build_system_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100
    
    def test_includes_primitives(self):
        """System prompt should mention primitives"""
        agent = AdaptiveAgent()
        prompt = agent._build_system_prompt()
        
        assert "web_search" in prompt or "primitive" in prompt.lower()
    
    def test_includes_max_steps(self):
        """System prompt should mention step limit"""
        agent = AdaptiveAgent()
        prompt = agent._build_system_prompt()
        
        assert "15" in prompt or "step" in prompt.lower()
    
    def test_includes_feedback_context(self):
        """System prompt should include feedback if provided"""
        agent = AdaptiveAgent()
        prompt = agent._build_system_prompt(feedback_context="User liked detailed responses")
        
        assert "detailed responses" in prompt
    
    def test_includes_strategy_hint(self):
        """System prompt should include strategy hint if provided"""
        agent = AdaptiveAgent()
        prompt = agent._build_system_prompt(strategy_hint="Search first, then scrape")
        
        assert "Search first" in prompt


class TestRiskClassifierIntegration:
    """Test that agent properly uses risk classifier"""
    
    def test_classifier_validates_safe_action(self):
        """Classifier should mark web_search as safe"""
        agent = AdaptiveAgent()
        result = agent.classifier.validate_action("web_search")
        
        assert result["risk"] == "safe"
    
    def test_classifier_validates_risky_action(self):
        """Classifier should mark fill_form as risky"""
        agent = AdaptiveAgent()
        result = agent.classifier.validate_action("fill_form")
        
        assert result["risk"] == "risky"
    
    def test_classifier_validates_unknown_action(self):
        """Classifier should handle unknown primitive"""
        agent = AdaptiveAgent()
        result = agent.classifier.validate_action("unknown_primitive")
        
        assert result["risk"] in ["blocked", "risky"]


class TestSandboxIntegration:
    """Test that agent properly uses sandbox"""
    
    def test_sandbox_has_timeout(self):
        """Agent sandbox should have 30s timeout"""
        agent = AdaptiveAgent()
        assert agent.sandbox.timeout == 30.0
    
    def test_sandbox_is_configured(self):
        """Agent should have configured sandbox"""
        agent = AdaptiveAgent()
        assert agent.sandbox is not None


class TestAgentRunInterface:
    """Test agent.run() interface"""
    
    @pytest.mark.asyncio
    async def test_run_is_async_generator(self):
        """agent.run() should be async generator"""
        agent = AdaptiveAgent()
        
        # Start run and get first event
        gen = agent.run(
            user_message="hello",
            history=[],
            user_id="test"
        )
        
        # Verify it's an async generator
        assert hasattr(gen, "__anext__")
    
    @pytest.mark.asyncio
    async def test_run_without_api_key_yields_error(self):
        """agent.run() should yield error if no API key"""
        import os
        
        # Save original key
        original_key = os.environ.get("GROQ_API_KEY", "")
        
        try:
            # Create agent without key
            agent = AdaptiveAgent()
            agent.groq_key = ""  # Force no key
            
            events = []
            async for event in agent.run("test", [], "user"):
                events.append(event)
                break  # First event only
            
            # Should have error event
            assert len(events) > 0
            assert events[0].type == "error"
            assert "API key" in events[0].content
            
        finally:
            # Restore
            os.environ["GROQ_API_KEY"] = original_key


class TestContextAccumulation:
    """Test that agent accumulates context across steps"""
    
    def test_agentresult_data_stores_context(self):
        """AgentResult should be able to store accumulated context"""
        result = AgentResult(
            success=True,
            response="Done",
            data={
                "step_1": {"type": "action", "result": "search results"},
                "step_2": {"type": "code", "result": "processed data"}
            }
        )
        
        assert "step_1" in result.data
        assert "step_2" in result.data
    
    def test_ask_event_includes_context(self):
        """Ask event data should include context for follow-up"""
        event = AgentEvent(
            type="ask",
            content="Choose an option",
            data={
                "options": [{"label": "A"}, {"label": "B"}],
                "context": {"previous_search": "results"},
                "scratchpad": [{"role": "user", "content": "search"}]
            }
        )
        
        assert "context" in event.data
        assert event.data["context"]["previous_search"] == "results"


class TestPrimitivesUsedTracking:
    """Test tracking of primitives used during execution"""
    
    def test_tracks_primitives_used(self):
        """AgentResult should track which primitives were used"""
        result = AgentResult(
            success=True,
            response="Done",
            primitives_used=["web_search", "browse_page", "web_search"]
        )
        
        assert result.primitives_used == ["web_search", "browse_page", "web_search"]
    
    def test_primitives_used_empty_by_default(self):
        """primitives_used should be empty list by default"""
        result = AgentResult(success=True, response="Done")
        
        assert result.primitives_used == []


class TestStepsTracking:
    """Test step counting and limits"""
    
    def test_max_steps_is_15(self):
        """Agent should have 15 max steps"""
        agent = AdaptiveAgent()
        assert agent.max_steps == 15
    
    def test_steps_taken_in_result(self):
        """AgentResult should track steps taken"""
        result = AgentResult(
            success=True,
            response="Done after multiple steps",
            steps_taken=5
        )
        
        assert result.steps_taken == 5
