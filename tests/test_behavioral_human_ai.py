"""
Behavioral Tests: Human AI Manager
===================================
Tests that the human-like AI manager ACTUALLY works:
- Emotion enum
- EmotionalState dataclass
- Personality dataclass
- WORLD_KNOWLEDGE constant
- COMMON_SENSE_RULES constant
- HumanAIManager class

README Requirements:
- Human-like AI
- Emotional intelligence
- Personality system
"""

import pytest
from dataclasses import is_dataclass
from datetime import datetime

from backend.core.human_ai import (
    Emotion,
    EmotionalState,
    Personality,
    HumanAIManager,
    WORLD_KNOWLEDGE,
    COMMON_SENSE_RULES,
)


class TestEmotionEnum:
    """Test Emotion enum"""
    
    def test_has_happy(self):
        """Should have HAPPY emotion"""
        assert hasattr(Emotion, "HAPPY")
        assert Emotion.HAPPY.value == "happy"
    
    def test_has_excited(self):
        """Should have EXCITED emotion"""
        assert hasattr(Emotion, "EXCITED")
        assert Emotion.EXCITED.value == "excited"
    
    def test_has_curious(self):
        """Should have CURIOUS emotion"""
        assert hasattr(Emotion, "CURIOUS")
        assert Emotion.CURIOUS.value == "curious"
    
    def test_has_concerned(self):
        """Should have CONCERNED emotion"""
        assert hasattr(Emotion, "CONCERNED")
        assert Emotion.CONCERNED.value == "concerned"
    
    def test_has_sympathetic(self):
        """Should have SYMPATHETIC emotion"""
        assert hasattr(Emotion, "SYMPATHETIC")
        assert Emotion.SYMPATHETIC.value == "sympathetic"
    
    def test_has_determined(self):
        """Should have DETERMINED emotion"""
        assert hasattr(Emotion, "DETERMINED")
        assert Emotion.DETERMINED.value == "determined"
    
    def test_has_thoughtful(self):
        """Should have THOUGHTFUL emotion"""
        assert hasattr(Emotion, "THOUGHTFUL")
        assert Emotion.THOUGHTFUL.value == "thoughtful"
    
    def test_has_playful(self):
        """Should have PLAYFUL emotion"""
        assert hasattr(Emotion, "PLAYFUL")
        assert Emotion.PLAYFUL.value == "playful"
    
    def test_has_calm(self):
        """Should have CALM emotion"""
        assert hasattr(Emotion, "CALM")
        assert Emotion.CALM.value == "calm"
    
    def test_has_focused(self):
        """Should have FOCUSED emotion"""
        assert hasattr(Emotion, "FOCUSED")
        assert Emotion.FOCUSED.value == "focused"


class TestEmotionalStateDataclass:
    """Test EmotionalState dataclass"""
    
    def test_is_dataclass(self):
        """EmotionalState should be a dataclass"""
        assert is_dataclass(EmotionalState)
    
    def test_can_create_default(self):
        """EmotionalState should be creatable with defaults"""
        state = EmotionalState()
        assert state is not None
    
    def test_default_primary_emotion_calm(self):
        """Default primary_emotion should be CALM"""
        state = EmotionalState()
        assert state.primary_emotion == Emotion.CALM
    
    def test_default_intensity(self):
        """Default intensity should be 0.5"""
        state = EmotionalState()
        assert state.intensity == 0.5
    
    def test_default_triggers_empty(self):
        """Default triggers should be empty list"""
        state = EmotionalState()
        assert state.triggers == []
    
    def test_can_set_emotion(self):
        """Should be able to set emotion"""
        state = EmotionalState(primary_emotion=Emotion.EXCITED)
        assert state.primary_emotion == Emotion.EXCITED
    
    def test_can_set_intensity(self):
        """Should be able to set intensity"""
        state = EmotionalState(intensity=0.8)
        assert state.intensity == 0.8


class TestEmotionalStateToPromptContext:
    """Test EmotionalState.to_prompt_context method"""
    
    def test_has_to_prompt_context_method(self):
        """Should have to_prompt_context method"""
        state = EmotionalState()
        assert hasattr(state, "to_prompt_context")
        assert callable(state.to_prompt_context)
    
    def test_to_prompt_context_returns_string(self):
        """to_prompt_context should return string"""
        state = EmotionalState()
        result = state.to_prompt_context()
        assert isinstance(result, str)
    
    def test_to_prompt_context_includes_emotion(self):
        """to_prompt_context should include emotion value"""
        state = EmotionalState(primary_emotion=Emotion.HAPPY)
        result = state.to_prompt_context()
        assert "happy" in result.lower()
    
    def test_to_prompt_context_low_intensity(self):
        """Low intensity should use 'slightly'"""
        state = EmotionalState(intensity=0.2)
        result = state.to_prompt_context()
        assert "slightly" in result.lower()
    
    def test_to_prompt_context_high_intensity(self):
        """High intensity should use 'quite'"""
        state = EmotionalState(intensity=0.8)
        result = state.to_prompt_context()
        assert "quite" in result.lower()


class TestPersonalityDataclass:
    """Test Personality dataclass"""
    
    def test_is_dataclass(self):
        """Personality should be a dataclass"""
        assert is_dataclass(Personality)
    
    def test_can_create_default(self):
        """Personality should be creatable with defaults"""
        personality = Personality()
        assert personality is not None
    
    def test_default_name(self):
        """Default name should be Alex"""
        personality = Personality()
        assert personality.name == "Alex"
    
    def test_has_traits(self):
        """Should have traits dict"""
        personality = Personality()
        assert hasattr(personality, "traits")
        assert isinstance(personality.traits, dict)
    
    def test_has_values(self):
        """Should have values list"""
        personality = Personality()
        assert hasattr(personality, "values")
        assert isinstance(personality.values, list)


class TestPersonalityTraits:
    """Test Personality traits"""
    
    def test_has_warmth_trait(self):
        """Should have warmth trait"""
        personality = Personality()
        assert "warmth" in personality.traits
    
    def test_has_curiosity_trait(self):
        """Should have curiosity trait"""
        personality = Personality()
        assert "curiosity" in personality.traits
    
    def test_has_helpfulness_trait(self):
        """Should have helpfulness trait"""
        personality = Personality()
        assert "helpfulness" in personality.traits
    
    def test_has_empathy_trait(self):
        """Should have empathy trait"""
        personality = Personality()
        assert "empathy" in personality.traits
    
    def test_has_honesty_trait(self):
        """Should have honesty trait"""
        personality = Personality()
        assert "honesty" in personality.traits
    
    def test_has_creativity_trait(self):
        """Should have creativity trait"""
        personality = Personality()
        assert "creativity" in personality.traits
    
    def test_traits_are_floats(self):
        """All traits should be float values"""
        personality = Personality()
        for trait, value in personality.traits.items():
            assert isinstance(value, (int, float)), f"{trait} is not numeric"
    
    def test_traits_in_range(self):
        """All traits should be between 0 and 1"""
        personality = Personality()
        for trait, value in personality.traits.items():
            assert 0 <= value <= 1, f"{trait}={value} out of range"


class TestPersonalityValues:
    """Test Personality values"""
    
    def test_values_not_empty(self):
        """Values should not be empty"""
        personality = Personality()
        assert len(personality.values) > 0
    
    def test_values_are_strings(self):
        """All values should be strings"""
        personality = Personality()
        for value in personality.values:
            assert isinstance(value, str)
    
    def test_values_include_helpful(self):
        """Values should include being helpful"""
        personality = Personality()
        helpful_found = any("help" in v.lower() for v in personality.values)
        assert helpful_found
    
    def test_values_include_privacy(self):
        """Values should include privacy"""
        personality = Personality()
        privacy_found = any("privacy" in v.lower() for v in personality.values)
        assert privacy_found
    
    def test_values_include_honesty(self):
        """Values should include honesty"""
        personality = Personality()
        honest_found = any("honest" in v.lower() for v in personality.values)
        assert honest_found


class TestWorldKnowledgeConstant:
    """Test WORLD_KNOWLEDGE constant"""
    
    def test_exists(self):
        """WORLD_KNOWLEDGE should exist"""
        assert WORLD_KNOWLEDGE is not None
    
    def test_is_string(self):
        """WORLD_KNOWLEDGE should be a string"""
        assert isinstance(WORLD_KNOWLEDGE, str)
    
    def test_not_empty(self):
        """WORLD_KNOWLEDGE should not be empty"""
        assert len(WORLD_KNOWLEDGE) > 0
    
    def test_includes_physics(self):
        """Should include physics knowledge"""
        assert "physics" in WORLD_KNOWLEDGE.lower() or "gravity" in WORLD_KNOWLEDGE.lower()
    
    def test_includes_time(self):
        """Should include time knowledge"""
        assert "time" in WORLD_KNOWLEDGE.lower()
    
    def test_includes_human_needs(self):
        """Should include human needs"""
        assert "sleep" in WORLD_KNOWLEDGE.lower() or "human" in WORLD_KNOWLEDGE.lower()


class TestCommonSenseRulesConstant:
    """Test COMMON_SENSE_RULES constant"""
    
    def test_exists(self):
        """COMMON_SENSE_RULES should exist"""
        assert COMMON_SENSE_RULES is not None
    
    def test_is_string(self):
        """COMMON_SENSE_RULES should be a string"""
        assert isinstance(COMMON_SENSE_RULES, str)
    
    def test_not_empty(self):
        """COMMON_SENSE_RULES should not be empty"""
        assert len(COMMON_SENSE_RULES) > 0
    
    def test_includes_check_guidelines(self):
        """Should include checking guidelines"""
        assert "check" in COMMON_SENSE_RULES.lower()


class TestHumanAIManagerClass:
    """Test HumanAIManager class"""
    
    def test_class_exists(self):
        """HumanAIManager class should exist"""
        assert HumanAIManager is not None
    
    def test_can_instantiate(self):
        """HumanAIManager should be instantiable"""
        manager = HumanAIManager()
        assert manager is not None
    
    def test_has_personality(self):
        """Should have personality"""
        manager = HumanAIManager()
        assert hasattr(manager, "personality")
    
    def test_has_emotional_state(self):
        """Should have emotional_state"""
        manager = HumanAIManager()
        assert hasattr(manager, "emotional_state")
    
    def test_has_generate_response_method(self):
        """Should have generate_response method"""
        manager = HumanAIManager()
        assert hasattr(manager, "generate_response")
        assert callable(manager.generate_response)
