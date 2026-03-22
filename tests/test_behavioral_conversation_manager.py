"""
Behavioral Tests: Conversation Manager
========================================
Tests that the conversation manager ACTUALLY works:
- ConversationStage class
- ConversationSession class
- Serialization/deserialization
- Stage progression

README Requirements:
- Multi-stage conversations
- Stage types: clarification, option_selection, confirmation, execution
- Session context management
"""

import pytest
from datetime import datetime

from backend.core.conversation_manager import (
    ConversationStage,
    ConversationSession,
)


class TestConversationStageInit:
    """Test ConversationStage initialization"""
    
    def test_can_create_stage(self):
        """ConversationStage should be creatable"""
        stage = ConversationStage("clarification", {"question": "Which date?"})
        assert stage is not None
    
    def test_has_id(self):
        """ConversationStage should have id"""
        stage = ConversationStage("confirmation", {})
        assert hasattr(stage, "id")
        assert len(stage.id) > 0
    
    def test_id_is_uuid(self):
        """ConversationStage id should be UUID"""
        import uuid
        stage = ConversationStage("execution", {})
        # Should not raise
        uuid.UUID(stage.id)
    
    def test_unique_ids(self):
        """Each stage should have unique id"""
        stage1 = ConversationStage("clarification", {})
        stage2 = ConversationStage("clarification", {})
        assert stage1.id != stage2.id
    
    def test_has_stage_type(self):
        """ConversationStage should have stage_type"""
        stage = ConversationStage("option_selection", {"options": []})
        assert stage.stage_type == "option_selection"
    
    def test_has_data(self):
        """ConversationStage should have data"""
        data = {"question": "Choose a time", "options": ["9 AM", "10 AM"]}
        stage = ConversationStage("option_selection", data)
        assert stage.data == data
    
    def test_completed_initially_false(self):
        """ConversationStage should not be completed initially"""
        stage = ConversationStage("confirmation", {})
        assert stage.completed is False
    
    def test_has_created_at(self):
        """ConversationStage should have created_at"""
        stage = ConversationStage("clarification", {})
        assert hasattr(stage, "created_at")
        assert isinstance(stage.created_at, str)


class TestConversationStageTypes:
    """Test different stage types"""
    
    def test_clarification_stage(self):
        """Should create clarification stage"""
        stage = ConversationStage("clarification", {"question": "What date?"})
        assert stage.stage_type == "clarification"
    
    def test_option_selection_stage(self):
        """Should create option_selection stage"""
        stage = ConversationStage("option_selection", {"options": ["A", "B", "C"]})
        assert stage.stage_type == "option_selection"
    
    def test_confirmation_stage(self):
        """Should create confirmation stage"""
        stage = ConversationStage("confirmation", {"summary": "Book meeting for Monday"})
        assert stage.stage_type == "confirmation"
    
    def test_execution_stage(self):
        """Should create execution stage"""
        stage = ConversationStage("execution", {"action": "book_meeting"})
        assert stage.stage_type == "execution"


class TestConversationStageSerialization:
    """Test ConversationStage serialization"""
    
    def test_to_dict_returns_dict(self):
        """to_dict should return dictionary"""
        stage = ConversationStage("clarification", {"key": "value"})
        result = stage.to_dict()
        assert isinstance(result, dict)
    
    def test_to_dict_has_id(self):
        """to_dict should include id"""
        stage = ConversationStage("test", {})
        result = stage.to_dict()
        assert "id" in result
    
    def test_to_dict_has_stage_type(self):
        """to_dict should include stage_type"""
        stage = ConversationStage("confirmation", {})
        result = stage.to_dict()
        assert result["stage_type"] == "confirmation"
    
    def test_to_dict_has_data(self):
        """to_dict should include data"""
        data = {"question": "test?"}
        stage = ConversationStage("clarification", data)
        result = stage.to_dict()
        assert result["data"] == data
    
    def test_to_dict_has_completed(self):
        """to_dict should include completed"""
        stage = ConversationStage("test", {})
        result = stage.to_dict()
        assert "completed" in result
    
    def test_to_dict_has_created_at(self):
        """to_dict should include created_at"""
        stage = ConversationStage("test", {})
        result = stage.to_dict()
        assert "created_at" in result


class TestConversationStageDeserialization:
    """Test ConversationStage deserialization"""
    
    def test_from_dict_creates_stage(self):
        """from_dict should create stage"""
        data = {
            "id": "test-id",
            "stage_type": "clarification",
            "data": {"question": "What date?"},
            "completed": False,
            "created_at": "2024-01-01T00:00:00"
        }
        stage = ConversationStage.from_dict(data)
        assert stage is not None
    
    def test_from_dict_preserves_id(self):
        """from_dict should preserve id"""
        data = {
            "id": "custom-id-123",
            "stage_type": "test",
            "data": {},
            "completed": False,
            "created_at": "2024-01-01T00:00:00"
        }
        stage = ConversationStage.from_dict(data)
        assert stage.id == "custom-id-123"
    
    def test_from_dict_preserves_completed(self):
        """from_dict should preserve completed"""
        data = {
            "id": "id",
            "stage_type": "test",
            "data": {},
            "completed": True,
            "created_at": "2024-01-01T00:00:00"
        }
        stage = ConversationStage.from_dict(data)
        assert stage.completed is True
    
    def test_roundtrip_serialization(self):
        """Serialization should be reversible"""
        original = ConversationStage("option_selection", {"options": [1, 2, 3]})
        original.completed = True
        
        serialized = original.to_dict()
        restored = ConversationStage.from_dict(serialized)
        
        assert restored.id == original.id
        assert restored.stage_type == original.stage_type
        assert restored.data == original.data
        assert restored.completed == original.completed


class TestConversationSessionInit:
    """Test ConversationSession initialization"""
    
    def test_can_create_session(self):
        """ConversationSession should be creatable"""
        session = ConversationSession("sess-123", {"type": "meeting"})
        assert session is not None
    
    def test_has_session_id(self):
        """ConversationSession should have session_id"""
        session = ConversationSession("my-session", {})
        assert session.session_id == "my-session"
    
    def test_has_initial_intent(self):
        """ConversationSession should have initial_intent"""
        intent = {"type": "restaurant_booking", "guests": 4}
        session = ConversationSession("sess", intent)
        assert session.initial_intent == intent
    
    def test_stages_initially_empty(self):
        """ConversationSession stages should be empty initially"""
        session = ConversationSession("sess", {})
        assert len(session.stages) == 0
    
    def test_context_initially_empty(self):
        """ConversationSession context should be empty initially"""
        session = ConversationSession("sess", {})
        assert len(session.context) == 0
    
    def test_current_stage_index_zero(self):
        """ConversationSession should start at stage 0"""
        session = ConversationSession("sess", {})
        assert session.current_stage_index == 0
    
    def test_has_created_at(self):
        """ConversationSession should have created_at"""
        session = ConversationSession("sess", {})
        assert hasattr(session, "created_at")


class TestConversationSessionStages:
    """Test ConversationSession stage management"""
    
    def test_add_stage(self):
        """add_stage should add stage to session"""
        session = ConversationSession("sess", {})
        stage = ConversationStage("clarification", {})
        
        session.add_stage(stage)
        
        assert len(session.stages) == 1
    
    def test_add_multiple_stages(self):
        """Should add multiple stages"""
        session = ConversationSession("sess", {})
        
        session.add_stage(ConversationStage("clarification", {}))
        session.add_stage(ConversationStage("option_selection", {}))
        session.add_stage(ConversationStage("confirmation", {}))
        
        assert len(session.stages) == 3
    
    def test_get_current_stage(self):
        """get_current_stage should return current stage"""
        session = ConversationSession("sess", {})
        stage = ConversationStage("clarification", {"question": "date?"})
        session.add_stage(stage)
        
        current = session.get_current_stage()
        
        assert current is stage
    
    def test_get_current_stage_empty(self):
        """get_current_stage should return None when no stages"""
        session = ConversationSession("sess", {})
        
        current = session.get_current_stage()
        
        assert current is None


class TestConversationSessionProgression:
    """Test stage progression"""
    
    def test_complete_current_stage(self):
        """complete_current_stage should mark stage completed"""
        session = ConversationSession("sess", {})
        session.add_stage(ConversationStage("clarification", {}))
        
        session.complete_current_stage({"date": "Monday"})
        
        assert session.stages[0].completed is True
    
    def test_complete_advances_index(self):
        """complete_current_stage should advance index"""
        session = ConversationSession("sess", {})
        session.add_stage(ConversationStage("stage1", {}))
        session.add_stage(ConversationStage("stage2", {}))
        
        session.complete_current_stage({})
        
        assert session.current_stage_index == 1
    
    def test_complete_updates_context(self):
        """complete_current_stage should update context"""
        session = ConversationSession("sess", {})
        session.add_stage(ConversationStage("clarification", {}))
        
        session.complete_current_stage({"date": "2024-01-15", "time": "10:00"})
        
        assert session.context["date"] == "2024-01-15"
        assert session.context["time"] == "10:00"
    
    def test_is_complete_false_initially(self):
        """is_complete should be False initially"""
        session = ConversationSession("sess", {})
        session.add_stage(ConversationStage("stage1", {}))
        
        assert session.is_complete() is False
    
    def test_is_complete_after_all_stages(self):
        """is_complete should be True after all stages completed"""
        session = ConversationSession("sess", {})
        session.add_stage(ConversationStage("stage1", {}))
        session.add_stage(ConversationStage("stage2", {}))
        
        session.complete_current_stage({})
        session.complete_current_stage({})
        
        assert session.is_complete() is True
    
    def test_is_complete_empty_session(self):
        """is_complete should be True for session with no stages"""
        session = ConversationSession("sess", {})
        assert session.is_complete() is True


class TestConversationSessionSerialization:
    """Test ConversationSession serialization"""
    
    def test_to_dict_returns_dict(self):
        """to_dict should return dictionary"""
        session = ConversationSession("sess", {})
        result = session.to_dict()
        assert isinstance(result, dict)
    
    def test_to_dict_has_session_id(self):
        """to_dict should include session_id"""
        session = ConversationSession("my-id", {})
        result = session.to_dict()
        assert result["session_id"] == "my-id"
    
    def test_to_dict_has_initial_intent(self):
        """to_dict should include initial_intent"""
        intent = {"type": "booking"}
        session = ConversationSession("sess", intent)
        result = session.to_dict()
        assert result["initial_intent"] == intent
    
    def test_to_dict_has_stages(self):
        """to_dict should include stages"""
        session = ConversationSession("sess", {})
        session.add_stage(ConversationStage("test", {}))
        result = session.to_dict()
        assert "stages" in result
        assert len(result["stages"]) == 1
    
    def test_to_dict_has_context(self):
        """to_dict should include context"""
        session = ConversationSession("sess", {})
        result = session.to_dict()
        assert "context" in result
    
    def test_to_dict_has_current_stage_index(self):
        """to_dict should include current_stage_index"""
        session = ConversationSession("sess", {})
        result = session.to_dict()
        assert result["current_stage_index"] == 0


class TestConversationSessionDeserialization:
    """Test ConversationSession deserialization"""
    
    def test_from_dict_creates_session(self):
        """from_dict should create session"""
        data = {
            "session_id": "sess-123",
            "initial_intent": {"type": "meeting"},
            "stages": [],
            "context": {},
            "current_stage_index": 0,
            "created_at": "2024-01-01T00:00:00"
        }
        session = ConversationSession.from_dict(data)
        assert session is not None
    
    def test_from_dict_preserves_session_id(self):
        """from_dict should preserve session_id"""
        data = {
            "session_id": "preserved-id",
            "initial_intent": {},
            "stages": [],
            "context": {},
            "current_stage_index": 0,
            "created_at": "2024-01-01T00:00:00"
        }
        session = ConversationSession.from_dict(data)
        assert session.session_id == "preserved-id"
    
    def test_from_dict_restores_stages(self):
        """from_dict should restore stages"""
        data = {
            "session_id": "sess",
            "initial_intent": {},
            "stages": [
                {"id": "1", "stage_type": "test", "data": {}, "completed": True, "created_at": "2024-01-01T00:00:00"}
            ],
            "context": {},
            "current_stage_index": 1,
            "created_at": "2024-01-01T00:00:00"
        }
        session = ConversationSession.from_dict(data)
        assert len(session.stages) == 1
        assert session.stages[0].completed is True
    
    def test_roundtrip_serialization(self):
        """Serialization should be reversible"""
        original = ConversationSession("sess-orig", {"type": "travel"})
        original.add_stage(ConversationStage("clarification", {"q": "where?"}))
        original.complete_current_stage({"destination": "Paris"})
        original.add_stage(ConversationStage("confirmation", {}))
        
        serialized = original.to_dict()
        restored = ConversationSession.from_dict(serialized)
        
        assert restored.session_id == original.session_id
        assert restored.initial_intent == original.initial_intent
        assert len(restored.stages) == len(original.stages)
        assert restored.context == original.context
        assert restored.current_stage_index == original.current_stage_index


class TestEdgeCases:
    """Test edge cases"""
    
    def test_complete_past_last_stage(self):
        """complete_current_stage should be safe past last stage"""
        session = ConversationSession("sess", {})
        session.add_stage(ConversationStage("only", {}))
        
        session.complete_current_stage({})
        # Should not raise
        session.complete_current_stage({})
        
        assert session.current_stage_index >= 1
    
    def test_get_current_stage_past_end(self):
        """get_current_stage should return None past end"""
        session = ConversationSession("sess", {})
        session.add_stage(ConversationStage("only", {}))
        session.complete_current_stage({})
        
        current = session.get_current_stage()
        assert current is None
    
    def test_empty_intent(self):
        """Should handle empty intent"""
        session = ConversationSession("sess", {})
        assert session.initial_intent == {}
    
    def test_nested_data(self):
        """Should handle nested data in stages"""
        nested_data = {
            "options": [
                {"id": 1, "label": "Option A"},
                {"id": 2, "label": "Option B"}
            ],
            "metadata": {"source": "ai"}
        }
        stage = ConversationStage("option_selection", nested_data)
        
        serialized = stage.to_dict()
        restored = ConversationStage.from_dict(serialized)
        
        assert restored.data == nested_data
