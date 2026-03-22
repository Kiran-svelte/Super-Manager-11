"""
Behavioral Tests: Agent Core
==============================
Tests that the agent core module ACTUALLY works:
- AgentConfig dataclass
- MessageRole enum
- ActionStatus enum
- Message, Action, Conversation dataclasses
- AIProvider and subclasses

README Requirements:
- Intent detection
- Expert selection
- Action planning and execution
- Conversation context management
"""

import pytest
from datetime import datetime

from backend.agent.core import (
    AgentConfig,
    MessageRole,
    ActionStatus,
    Message,
    Action,
    Conversation,
    AIProvider,
    GroqProvider,
    OpenAIProvider,
)


class TestMessageRoleEnum:
    """Test MessageRole enum"""
    
    def test_user_value(self):
        """USER should have correct value"""
        assert MessageRole.USER == "user"
    
    def test_assistant_value(self):
        """ASSISTANT should have correct value"""
        assert MessageRole.ASSISTANT == "assistant"
    
    def test_system_value(self):
        """SYSTEM should have correct value"""
        assert MessageRole.SYSTEM == "system"
    
    def test_tool_value(self):
        """TOOL should have correct value"""
        assert MessageRole.TOOL == "tool"
    
    def test_all_roles(self):
        """Should have exactly 4 roles"""
        roles = list(MessageRole)
        assert len(roles) == 4


class TestActionStatusEnum:
    """Test ActionStatus enum"""
    
    def test_pending_value(self):
        """PENDING should have correct value"""
        assert ActionStatus.PENDING == "pending"
    
    def test_executing_value(self):
        """EXECUTING should have correct value"""
        assert ActionStatus.EXECUTING == "executing"
    
    def test_completed_value(self):
        """COMPLETED should have correct value"""
        assert ActionStatus.COMPLETED == "completed"
    
    def test_failed_value(self):
        """FAILED should have correct value"""
        assert ActionStatus.FAILED == "failed"
    
    def test_all_statuses(self):
        """Should have exactly 4 statuses"""
        statuses = list(ActionStatus)
        assert len(statuses) == 4


class TestAgentConfig:
    """Test AgentConfig dataclass"""
    
    def test_can_create(self):
        """AgentConfig should be creatable"""
        config = AgentConfig()
        assert config is not None
    
    def test_has_groq_api_key(self):
        """Should have groq_api_key"""
        config = AgentConfig()
        assert hasattr(config, "groq_api_key")
    
    def test_has_openai_api_key(self):
        """Should have openai_api_key"""
        config = AgentConfig()
        assert hasattr(config, "openai_api_key")
    
    def test_has_anthropic_api_key(self):
        """Should have anthropic_api_key"""
        config = AgentConfig()
        assert hasattr(config, "anthropic_api_key")
    
    def test_has_google_ai_key(self):
        """Should have google_ai_key"""
        config = AgentConfig()
        assert hasattr(config, "google_ai_key")
    
    def test_default_model(self):
        """Default model should be groq"""
        config = AgentConfig()
        assert config.default_model == "groq"
    
    def test_autonomous_mode_default(self):
        """autonomous_mode should default to True"""
        config = AgentConfig()
        assert config.autonomous_mode is True
    
    def test_max_actions_per_turn(self):
        """max_actions_per_turn should default to 5"""
        config = AgentConfig()
        assert config.max_actions_per_turn == 5
    
    def test_context_window(self):
        """context_window should default to 20"""
        config = AgentConfig()
        assert config.context_window == 20
    
    def test_ai_timeout(self):
        """ai_timeout should default to 30.0"""
        config = AgentConfig()
        assert config.ai_timeout == 30.0
    
    def test_action_timeout(self):
        """action_timeout should default to 60.0"""
        config = AgentConfig()
        assert config.action_timeout == 60.0


class TestMessage:
    """Test Message dataclass"""
    
    def test_can_create(self):
        """Message should be creatable"""
        msg = Message(role=MessageRole.USER, content="Hello")
        assert msg is not None
    
    def test_has_role(self):
        """Message should have role"""
        msg = Message(role=MessageRole.ASSISTANT, content="Hi there")
        assert msg.role == MessageRole.ASSISTANT
    
    def test_has_content(self):
        """Message should have content"""
        msg = Message(role=MessageRole.USER, content="Test content")
        assert msg.content == "Test content"
    
    def test_has_timestamp(self):
        """Message should have timestamp"""
        msg = Message(role=MessageRole.USER, content="Test")
        assert hasattr(msg, "timestamp")
        assert isinstance(msg.timestamp, datetime)
    
    def test_has_metadata(self):
        """Message should have metadata dict"""
        msg = Message(role=MessageRole.USER, content="Test")
        assert hasattr(msg, "metadata")
        assert isinstance(msg.metadata, dict)
    
    def test_custom_metadata(self):
        """Should accept custom metadata"""
        msg = Message(
            role=MessageRole.USER,
            content="Test",
            metadata={"source": "api"}
        )
        assert msg.metadata["source"] == "api"


class TestAction:
    """Test Action dataclass"""
    
    def test_can_create(self):
        """Action should be creatable"""
        action = Action(
            id="act-1",
            type="email",
            description="Send email",
            parameters={"to": "test@example.com"}
        )
        assert action is not None
    
    def test_has_id(self):
        """Action should have id"""
        action = Action(id="act-123", type="search", description="Search", parameters={})
        assert action.id == "act-123"
    
    def test_has_type(self):
        """Action should have type"""
        action = Action(id="1", type="calendar", description="Book", parameters={})
        assert action.type == "calendar"
    
    def test_has_description(self):
        """Action should have description"""
        action = Action(id="1", type="zoom", description="Create Zoom meeting", parameters={})
        assert action.description == "Create Zoom meeting"
    
    def test_has_parameters(self):
        """Action should have parameters"""
        action = Action(
            id="1",
            type="telegram",
            description="Send message",
            parameters={"chat_id": "123", "text": "Hello"}
        )
        assert action.parameters["chat_id"] == "123"
    
    def test_default_status_pending(self):
        """Default status should be PENDING"""
        action = Action(id="1", type="test", description="Test", parameters={})
        assert action.status == ActionStatus.PENDING
    
    def test_default_result_none(self):
        """Default result should be None"""
        action = Action(id="1", type="test", description="Test", parameters={})
        assert action.result is None
    
    def test_default_error_none(self):
        """Default error should be None"""
        action = Action(id="1", type="test", description="Test", parameters={})
        assert action.error is None
    
    def test_to_dict(self):
        """to_dict should return dictionary"""
        action = Action(
            id="act-1",
            type="email",
            description="Send email",
            parameters={"to": "test@example.com"}
        )
        result = action.to_dict()
        
        assert isinstance(result, dict)
        assert result["id"] == "act-1"
        assert result["type"] == "email"
        assert result["status"] == "pending"


class TestConversation:
    """Test Conversation dataclass"""
    
    def test_can_create(self):
        """Conversation should be creatable"""
        conv = Conversation(id="conv-1", user_id="user-1")
        assert conv is not None
    
    def test_has_id(self):
        """Conversation should have id"""
        conv = Conversation(id="conv-123", user_id="user-1")
        assert conv.id == "conv-123"
    
    def test_has_user_id(self):
        """Conversation should have user_id"""
        conv = Conversation(id="conv-1", user_id="user-456")
        assert conv.user_id == "user-456"
    
    def test_default_messages_empty(self):
        """Default messages should be empty list"""
        conv = Conversation(id="conv-1", user_id="user-1")
        assert conv.messages == []
    
    def test_default_context_empty(self):
        """Default context should be empty dict"""
        conv = Conversation(id="conv-1", user_id="user-1")
        assert conv.context == {}
    
    def test_default_active_expert_none(self):
        """Default active_expert should be None"""
        conv = Conversation(id="conv-1", user_id="user-1")
        assert conv.active_expert is None
    
    def test_default_pending_actions_empty(self):
        """Default pending_actions should be empty list"""
        conv = Conversation(id="conv-1", user_id="user-1")
        assert conv.pending_actions == []
    
    def test_has_created_at(self):
        """Conversation should have created_at"""
        conv = Conversation(id="conv-1", user_id="user-1")
        assert isinstance(conv.created_at, datetime)


class TestConversationMethods:
    """Test Conversation methods"""
    
    def test_add_message(self):
        """add_message should add message to list"""
        conv = Conversation(id="conv-1", user_id="user-1")
        
        conv.add_message(MessageRole.USER, "Hello")
        
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Hello"
    
    def test_add_multiple_messages(self):
        """Should add multiple messages"""
        conv = Conversation(id="conv-1", user_id="user-1")
        
        conv.add_message(MessageRole.USER, "Hi")
        conv.add_message(MessageRole.ASSISTANT, "Hello!")
        conv.add_message(MessageRole.USER, "How are you?")
        
        assert len(conv.messages) == 3
    
    def test_get_messages_for_api(self):
        """get_messages_for_api should return formatted list"""
        conv = Conversation(id="conv-1", user_id="user-1")
        conv.add_message(MessageRole.USER, "Hello")
        conv.add_message(MessageRole.ASSISTANT, "Hi there")
        
        result = conv.get_messages_for_api()
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"
    
    def test_get_messages_for_api_limit(self):
        """get_messages_for_api should respect limit"""
        conv = Conversation(id="conv-1", user_id="user-1")
        
        for i in range(30):
            conv.add_message(MessageRole.USER, f"Message {i}")
        
        result = conv.get_messages_for_api(limit=10)
        
        assert len(result) == 10


class TestAIProvider:
    """Test AIProvider base class"""
    
    def test_has_complete_method(self):
        """AIProvider should have complete method"""
        assert hasattr(AIProvider, "complete")
    
    @pytest.mark.asyncio
    async def test_complete_raises_not_implemented(self):
        """Base complete should raise NotImplementedError"""
        provider = AIProvider()
        
        with pytest.raises(NotImplementedError):
            await provider.complete([])


class TestGroqProvider:
    """Test GroqProvider class"""
    
    def test_can_instantiate(self):
        """GroqProvider should be instantiatable"""
        provider = GroqProvider(api_key="test-key")
        assert provider is not None
    
    def test_has_api_key(self):
        """Should store api_key"""
        provider = GroqProvider(api_key="my-api-key")
        assert provider.api_key == "my-api-key"
    
    def test_default_model(self):
        """Should have default model"""
        provider = GroqProvider(api_key="test")
        assert provider.model is not None
        assert "llama" in provider.model.lower()
    
    def test_has_base_url(self):
        """Should have base_url"""
        provider = GroqProvider(api_key="test")
        assert hasattr(provider, "base_url")
        assert "groq" in provider.base_url.lower()
    
    def test_complete_is_async(self):
        """complete should be async"""
        import inspect
        provider = GroqProvider(api_key="test")
        assert inspect.iscoroutinefunction(provider.complete)


class TestOpenAIProvider:
    """Test OpenAIProvider class"""
    
    def test_can_instantiate(self):
        """OpenAIProvider should be instantiatable"""
        provider = OpenAIProvider(api_key="test-key")
        assert provider is not None
    
    def test_has_api_key(self):
        """Should store api_key"""
        provider = OpenAIProvider(api_key="my-api-key")
        assert provider.api_key == "my-api-key"
    
    def test_default_model(self):
        """Should have default model"""
        provider = OpenAIProvider(api_key="test")
        assert provider.model is not None
        assert "gpt" in provider.model.lower()
    
    def test_has_base_url(self):
        """Should have base_url"""
        provider = OpenAIProvider(api_key="test")
        assert hasattr(provider, "base_url")
        assert "openai" in provider.base_url.lower()
    
    def test_complete_is_async(self):
        """complete should be async"""
        import inspect
        provider = OpenAIProvider(api_key="test")
        assert inspect.iscoroutinefunction(provider.complete)


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_content_message(self):
        """Should handle empty content"""
        msg = Message(role=MessageRole.USER, content="")
        assert msg.content == ""
    
    def test_empty_parameters_action(self):
        """Should handle empty parameters"""
        action = Action(id="1", type="test", description="Test", parameters={})
        assert action.parameters == {}
    
    def test_conversation_context_modification(self):
        """Should allow context modification"""
        conv = Conversation(id="conv-1", user_id="user-1")
        
        conv.context["user_preferences"] = {"language": "en"}
        
        assert conv.context["user_preferences"]["language"] == "en"
