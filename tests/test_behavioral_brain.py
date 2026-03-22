"""
Behavioral Tests: AI Brain
===========================
Tests that the AI brain module ACTUALLY works:
- MessageType enum
- Message dataclass
- Session dataclass
- Database class
- AIBrain class
- Confirmation keywords

README Requirements:
- AI brain
- Session management
- Feedback system
"""

import pytest
from dataclasses import is_dataclass
from datetime import datetime

from backend.core.brain import (
    MessageType,
    Message,
    Session,
    Database,
    AIBrain,
    CONFIRM_YES,
    CONFIRM_NO,
    _is_confirmation,
)


class TestMessageTypeEnum:
    """Test MessageType enum"""
    
    def test_has_user(self):
        """Should have USER type"""
        assert hasattr(MessageType, "USER")
        assert MessageType.USER.value == "user"
    
    def test_has_ai(self):
        """Should have AI type"""
        assert hasattr(MessageType, "AI")
        assert MessageType.AI.value == "ai"
    
    def test_has_system(self):
        """Should have SYSTEM type"""
        assert hasattr(MessageType, "SYSTEM")
        assert MessageType.SYSTEM.value == "system"


class TestMessageDataclass:
    """Test Message dataclass"""
    
    def test_is_dataclass(self):
        """Message should be a dataclass"""
        assert is_dataclass(Message)
    
    def test_can_create(self):
        """Message should be creatable"""
        msg = Message(role=MessageType.USER, content="Hello")
        assert msg is not None
    
    def test_has_role(self):
        """Should have role"""
        msg = Message(role=MessageType.AI, content="Hi")
        assert msg.role == MessageType.AI
    
    def test_has_content(self):
        """Should have content"""
        msg = Message(role=MessageType.USER, content="Test message")
        assert msg.content == "Test message"
    
    def test_has_timestamp(self):
        """Should have timestamp"""
        msg = Message(role=MessageType.USER, content="Test")
        assert isinstance(msg.timestamp, datetime)


class TestSessionDataclass:
    """Test Session dataclass"""
    
    def test_is_dataclass(self):
        """Session should be a dataclass"""
        assert is_dataclass(Session)
    
    def test_can_create(self):
        """Session should be creatable"""
        session = Session(id="sess-123")
        assert session is not None
    
    def test_has_id(self):
        """Should have id"""
        session = Session(id="my-session")
        assert session.id == "my-session"
    
    def test_default_messages_empty(self):
        """Default messages should be empty list"""
        session = Session(id="s")
        assert session.messages == []
    
    def test_default_user_data_empty(self):
        """Default user_data should be empty dict"""
        session = Session(id="s")
        assert session.user_data == {}
    
    def test_default_pending_confirmation_none(self):
        """Default pending_confirmation should be None"""
        session = Session(id="s")
        assert session.pending_confirmation is None
    
    def test_default_feedback_history_empty(self):
        """Default feedback_history should be empty list"""
        session = Session(id="s")
        assert session.feedback_history == []


class TestDatabaseClass:
    """Test Database class"""
    
    def test_class_exists(self):
        """Database class should exist"""
        assert Database is not None
    
    def test_can_instantiate(self):
        """Database should be instantiable"""
        db = Database()
        assert db is not None
    
    def test_has_sessions(self):
        """Should have sessions dict"""
        db = Database()
        assert hasattr(db, "sessions")
        assert isinstance(db.sessions, dict)
    
    def test_has_users(self):
        """Should have users dict"""
        db = Database()
        assert hasattr(db, "users")
        assert isinstance(db.users, dict)
    
    def test_has_feedback(self):
        """Should have feedback dict"""
        db = Database()
        assert hasattr(db, "feedback")
        assert isinstance(db.feedback, dict)
    
    def test_has_memory(self):
        """Should have memory dict"""
        db = Database()
        assert hasattr(db, "memory")
        assert isinstance(db.memory, dict)


class TestDatabaseGetSession:
    """Test Database get_session method"""
    
    def test_has_get_session_method(self):
        """Should have get_session method"""
        db = Database()
        assert hasattr(db, "get_session")
        assert callable(db.get_session)
    
    def test_get_session_creates_new(self):
        """get_session should create new session if not exists"""
        db = Database()
        session = db.get_session("new-session-123")
        assert session is not None
        assert session.id == "new-session-123"
    
    def test_get_session_returns_existing(self):
        """get_session should return existing session"""
        db = Database()
        session1 = db.get_session("test-session")
        session1.messages.append(Message(role=MessageType.USER, content="Test"))
        session2 = db.get_session("test-session")
        assert len(session2.messages) == 1


class TestDatabaseUserMethods:
    """Test Database user methods"""
    
    def test_has_save_user_method(self):
        """Should have save_user method"""
        db = Database()
        assert hasattr(db, "save_user")
        assert callable(db.save_user)
    
    def test_has_get_user_method(self):
        """Should have get_user method"""
        db = Database()
        assert hasattr(db, "get_user")
        assert callable(db.get_user)
    
    def test_save_and_get_user(self):
        """Should save and retrieve user data"""
        db = Database()
        db.save_user("user-123", {"name": "John"})
        user = db.get_user("user-123")
        assert user["name"] == "John"
    
    def test_get_user_returns_none_if_not_exists(self):
        """get_user should return None if user doesn't exist"""
        db = Database()
        user = db.get_user("nonexistent")
        assert user is None


class TestDatabaseFeedbackMethods:
    """Test Database feedback methods"""
    
    def test_has_add_feedback_method(self):
        """Should have add_feedback method"""
        db = Database()
        assert hasattr(db, "add_feedback")
        assert callable(db.add_feedback)
    
    def test_has_get_feedback_method(self):
        """Should have get_feedback method"""
        db = Database()
        assert hasattr(db, "get_feedback")
        assert callable(db.get_feedback)
    
    def test_add_and_get_feedback(self):
        """Should add and retrieve feedback"""
        db = Database()
        db.add_feedback("user-1", {"rating": "positive"})
        feedback = db.get_feedback("user-1")
        assert len(feedback) == 1
        assert feedback[0]["rating"] == "positive"


class TestDatabaseMemoryMethods:
    """Test Database memory methods"""
    
    def test_has_get_memory_method(self):
        """Should have get_memory method"""
        db = Database()
        assert hasattr(db, "get_memory")
        assert callable(db.get_memory)
    
    def test_has_save_memory_method(self):
        """Should have save_memory method"""
        db = Database()
        assert hasattr(db, "save_memory")
        assert callable(db.save_memory)
    
    def test_save_and_get_memory(self):
        """Should save and retrieve memory"""
        db = Database()
        db.save_memory("user-1", "name", "Alice")
        memory = db.get_memory("user-1")
        assert memory["name"] == "Alice"


class TestConfirmYesKeywords:
    """Test CONFIRM_YES keywords"""
    
    def test_exists(self):
        """CONFIRM_YES should exist"""
        assert CONFIRM_YES is not None
    
    def test_is_set(self):
        """CONFIRM_YES should be a set"""
        assert isinstance(CONFIRM_YES, set)
    
    def test_includes_yes(self):
        """Should include 'yes'"""
        assert "yes" in CONFIRM_YES
    
    def test_includes_confirm(self):
        """Should include 'confirm'"""
        assert "confirm" in CONFIRM_YES
    
    def test_includes_ok(self):
        """Should include 'ok' or 'okay'"""
        assert "ok" in CONFIRM_YES or "okay" in CONFIRM_YES
    
    def test_includes_proceed(self):
        """Should include 'proceed'"""
        assert "proceed" in CONFIRM_YES


class TestConfirmNoKeywords:
    """Test CONFIRM_NO keywords"""
    
    def test_exists(self):
        """CONFIRM_NO should exist"""
        assert CONFIRM_NO is not None
    
    def test_is_set(self):
        """CONFIRM_NO should be a set"""
        assert isinstance(CONFIRM_NO, set)
    
    def test_includes_no(self):
        """Should include 'no'"""
        assert "no" in CONFIRM_NO
    
    def test_includes_cancel(self):
        """Should include 'cancel'"""
        assert "cancel" in CONFIRM_NO
    
    def test_includes_stop(self):
        """Should include 'stop'"""
        assert "stop" in CONFIRM_NO


class TestIsConfirmationFunction:
    """Test _is_confirmation function"""
    
    def test_function_exists(self):
        """_is_confirmation function should exist"""
        assert _is_confirmation is not None
        assert callable(_is_confirmation)
    
    def test_returns_true_for_yes(self):
        """Should return True for 'yes'"""
        result = _is_confirmation("yes", CONFIRM_YES)
        assert result is True
    
    def test_returns_true_for_confirm(self):
        """Should return True for 'confirm'"""
        result = _is_confirmation("confirm", CONFIRM_YES)
        assert result is True
    
    def test_returns_false_for_random(self):
        """Should return False for random text"""
        result = _is_confirmation("hello there", CONFIRM_YES)
        assert result is False
    
    def test_case_insensitive(self):
        """Should be case insensitive"""
        result = _is_confirmation("YES", CONFIRM_YES)
        assert result is True


class TestAIBrainClass:
    """Test AIBrain class"""
    
    def test_class_exists(self):
        """AIBrain class should exist"""
        assert AIBrain is not None
    
    def test_can_instantiate(self):
        """AIBrain should be instantiable"""
        brain = AIBrain()
        assert brain is not None
    
    def test_has_agent(self):
        """Should have agent"""
        brain = AIBrain()
        assert hasattr(brain, "agent")
