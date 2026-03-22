"""
Behavioral Tests: Intent Parser
================================
Tests that the intent parser module ACTUALLY works:
- IntentParser class
- Quick classification
- Entity extraction
- Pattern matching

README Requirements:
- Intent parsing
- Entity extraction
- NLU capabilities
"""

import pytest
import re

from backend.core.intent_parser import IntentParser


class TestIntentParserInit:
    """Test IntentParser initialization"""
    
    def test_can_instantiate(self):
        """IntentParser should be instantiatable"""
        parser = IntentParser()
        assert parser is not None
    
    def test_has_api_key(self):
        """Should have api_key attribute"""
        parser = IntentParser()
        assert hasattr(parser, "api_key")
    
    def test_has_model(self):
        """Should have model attribute"""
        parser = IntentParser()
        assert hasattr(parser, "model")
    
    def test_has_intent_patterns(self):
        """Should have intent_patterns dict"""
        parser = IntentParser()
        assert hasattr(parser, "intent_patterns")
        assert isinstance(parser.intent_patterns, dict)


class TestIntentPatterns:
    """Test intent patterns configuration"""
    
    def test_has_schedule_pattern(self):
        """Should have schedule intent pattern"""
        parser = IntentParser()
        assert "schedule" in parser.intent_patterns
    
    def test_has_search_pattern(self):
        """Should have search intent pattern"""
        parser = IntentParser()
        assert "search" in parser.intent_patterns
    
    def test_has_purchase_pattern(self):
        """Should have purchase intent pattern"""
        parser = IntentParser()
        assert "purchase" in parser.intent_patterns
    
    def test_has_manage_pattern(self):
        """Should have manage intent pattern"""
        parser = IntentParser()
        assert "manage" in parser.intent_patterns
    
    def test_has_analyze_pattern(self):
        """Should have analyze intent pattern"""
        parser = IntentParser()
        assert "analyze" in parser.intent_patterns
    
    def test_has_communicate_pattern(self):
        """Should have communicate intent pattern"""
        parser = IntentParser()
        assert "communicate" in parser.intent_patterns
    
    def test_patterns_are_lists(self):
        """Each pattern should be a list of keywords"""
        parser = IntentParser()
        for name, keywords in parser.intent_patterns.items():
            assert isinstance(keywords, list), f"{name} should be a list"
            assert len(keywords) > 0, f"{name} should have keywords"


class TestQuickClassify:
    """Test _quick_classify method"""
    
    def test_has_quick_classify_method(self):
        """Should have _quick_classify method"""
        parser = IntentParser()
        assert hasattr(parser, "_quick_classify")
        assert callable(parser._quick_classify)
    
    def test_classifies_schedule_intent(self):
        """Should classify schedule intent"""
        parser = IntentParser()
        result = parser._quick_classify("Schedule a meeting for tomorrow")
        assert result == "schedule"
    
    def test_classifies_book_as_schedule(self):
        """Should classify 'book' as schedule"""
        parser = IntentParser()
        result = parser._quick_classify("Book an appointment")
        assert result == "schedule"
    
    def test_classifies_search_intent(self):
        """Should classify search intent"""
        parser = IntentParser()
        result = parser._quick_classify("Find the nearest coffee shop")
        assert result == "search"
    
    def test_classifies_purchase_intent(self):
        """Should classify purchase intent"""
        parser = IntentParser()
        result = parser._quick_classify("Buy tickets for the concert")
        assert result == "purchase"
    
    def test_classifies_communicate_intent(self):
        """Should classify communicate intent"""
        parser = IntentParser()
        result = parser._quick_classify("Send an email to John")
        assert result == "communicate"
    
    def test_returns_general_for_unknown(self):
        """Should return 'general' for unknown intent"""
        parser = IntentParser()
        result = parser._quick_classify("Hello there")
        assert result == "general"
    
    def test_case_insensitive(self):
        """Should be case insensitive"""
        parser = IntentParser()
        result = parser._quick_classify("SCHEDULE A MEETING")
        assert result == "schedule"


class TestExtractEntities:
    """Test extract_entities method"""
    
    def test_has_extract_entities_method(self):
        """Should have extract_entities method"""
        parser = IntentParser()
        assert hasattr(parser, "extract_entities")
        assert callable(parser.extract_entities)
    
    def test_returns_dict(self):
        """Should return dict"""
        parser = IntentParser()
        result = parser.extract_entities("Meeting tomorrow at 3pm")
        assert isinstance(result, dict)
    
    def test_has_dates_key(self):
        """Result should have dates key"""
        parser = IntentParser()
        result = parser.extract_entities("test")
        assert "dates" in result
    
    def test_has_times_key(self):
        """Result should have times key"""
        parser = IntentParser()
        result = parser.extract_entities("test")
        assert "times" in result
    
    def test_has_amounts_key(self):
        """Result should have amounts key"""
        parser = IntentParser()
        result = parser.extract_entities("test")
        assert "amounts" in result
    
    def test_has_locations_key(self):
        """Result should have locations key"""
        parser = IntentParser()
        result = parser.extract_entities("test")
        assert "locations" in result


class TestExtractDates:
    """Test _extract_dates method"""
    
    def test_has_extract_dates_method(self):
        """Should have _extract_dates method"""
        parser = IntentParser()
        assert hasattr(parser, "_extract_dates")
        assert callable(parser._extract_dates)
    
    def test_extracts_today(self):
        """Should extract 'today'"""
        parser = IntentParser()
        result = parser._extract_dates("Meeting today")
        assert "today" in result
    
    def test_extracts_tomorrow(self):
        """Should extract 'tomorrow'"""
        parser = IntentParser()
        result = parser._extract_dates("Call me tomorrow")
        assert "tomorrow" in result
    
    def test_extracts_date_format(self):
        """Should extract date format"""
        parser = IntentParser()
        result = parser._extract_dates("Appointment on 12/25/2024")
        assert any("12" in d and "25" in d for d in result)


class TestExtractTimes:
    """Test _extract_times method"""
    
    def test_has_extract_times_method(self):
        """Should have _extract_times method"""
        parser = IntentParser()
        assert hasattr(parser, "_extract_times")
        assert callable(parser._extract_times)
    
    def test_extracts_time_with_am_pm(self):
        """Should extract time with am/pm"""
        parser = IntentParser()
        result = parser._extract_times("Meeting at 3:30 pm")
        assert len(result) > 0


class TestCalculateConfidence:
    """Test _calculate_confidence method"""
    
    def test_has_calculate_confidence_method(self):
        """Should have _calculate_confidence method"""
        parser = IntentParser()
        assert hasattr(parser, "_calculate_confidence")
        assert callable(parser._calculate_confidence)
    
    def test_returns_float(self):
        """Should return float"""
        parser = IntentParser()
        intent = {"action": "schedule", "entities": {"dates": ["tomorrow"]}}
        result = parser._calculate_confidence("schedule meeting", intent)
        assert isinstance(result, float)
    
    def test_high_confidence_with_action_and_entities(self):
        """Should return high confidence with action and entities"""
        parser = IntentParser()
        intent = {"action": "schedule", "entities": {"dates": ["tomorrow"]}}
        result = parser._calculate_confidence("test", intent)
        assert result >= 0.9
    
    def test_medium_confidence_with_action_only(self):
        """Should return medium confidence with action only"""
        parser = IntentParser()
        intent = {"action": "schedule", "entities": {}}
        result = parser._calculate_confidence("test", intent)
        assert result == 0.7
    
    def test_low_confidence_for_unknown(self):
        """Should return low confidence for unknown action"""
        parser = IntentParser()
        intent = {"action": "unknown", "entities": {}}
        result = parser._calculate_confidence("test", intent)
        assert result == 0.5


class TestParseMethods:
    """Test parse method"""
    
    def test_has_parse_method(self):
        """Should have parse method"""
        parser = IntentParser()
        assert hasattr(parser, "parse")
        assert callable(parser.parse)
    
    def test_parse_is_async(self):
        """parse should be async"""
        import inspect
        parser = IntentParser()
        assert inspect.iscoroutinefunction(parser.parse)
    
    def test_has_deep_parse_method(self):
        """Should have _deep_parse method"""
        parser = IntentParser()
        assert hasattr(parser, "_deep_parse")
        assert callable(parser._deep_parse)
    
    def test_deep_parse_is_async(self):
        """_deep_parse should be async"""
        import inspect
        parser = IntentParser()
        assert inspect.iscoroutinefunction(parser._deep_parse)


class TestDeepParseWithoutApiKey:
    """Test _deep_parse fallback without API key"""
    
    @pytest.mark.asyncio
    async def test_deep_parse_fallback(self):
        """Should fallback gracefully without API key"""
        parser = IntentParser()
        parser.api_key = ""  # Ensure no API key
        
        result = await parser._deep_parse("Schedule a meeting", {})
        assert isinstance(result, dict)
        assert "action" in result
        assert "category" in result


class TestGetClient:
    """Test _get_client method"""
    
    def test_has_get_client_method(self):
        """Should have _get_client method"""
        parser = IntentParser()
        assert hasattr(parser, "_get_client")
        assert callable(parser._get_client)
    
    def test_raises_without_api_key(self):
        """Should raise error without API key"""
        parser = IntentParser()
        parser.api_key = ""
        
        with pytest.raises(ValueError):
            parser._get_client()
