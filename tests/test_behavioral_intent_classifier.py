"""
Behavioral Tests: Intent Classifier
=====================================
Tests that the intent classifier ACTUALLY works:
- IntentClassifier initialization
- Pattern matching for different intents
- Entity extraction
- Confidence levels

README Requirements:
- Classify user intents into categories
- Extract entities from user input
- Pattern-based classification
"""

import pytest

from backend.core.intent_classifier import IntentClassifier


class TestIntentClassifierInit:
    """Test IntentClassifier initialization"""
    
    def test_can_instantiate(self):
        """IntentClassifier should be instantiatable"""
        classifier = IntentClassifier()
        assert classifier is not None
    
    def test_has_intent_patterns(self):
        """IntentClassifier should have intent_patterns"""
        classifier = IntentClassifier()
        assert hasattr(classifier, "intent_patterns")
        assert isinstance(classifier.intent_patterns, dict)
    
    def test_has_birthday_party_intent(self):
        """IntentClassifier should have birthday_party intent"""
        classifier = IntentClassifier()
        assert "birthday_party" in classifier.intent_patterns
    
    def test_has_travel_planning_intent(self):
        """IntentClassifier should have travel_planning intent"""
        classifier = IntentClassifier()
        assert "travel_planning" in classifier.intent_patterns
    
    def test_has_meeting_scheduling_intent(self):
        """IntentClassifier should have meeting_scheduling intent"""
        classifier = IntentClassifier()
        assert "meeting_scheduling" in classifier.intent_patterns
    
    def test_has_event_planning_intent(self):
        """IntentClassifier should have event_planning intent"""
        classifier = IntentClassifier()
        assert "event_planning" in classifier.intent_patterns
    
    def test_has_restaurant_booking_intent(self):
        """IntentClassifier should have restaurant_booking intent"""
        classifier = IntentClassifier()
        assert "restaurant_booking" in classifier.intent_patterns
    
    def test_has_shopping_intent(self):
        """IntentClassifier should have shopping intent"""
        classifier = IntentClassifier()
        assert "shopping" in classifier.intent_patterns


class TestClassifyMethod:
    """Test IntentClassifier.classify() method"""
    
    def test_returns_dict(self):
        """classify() should return dict"""
        classifier = IntentClassifier()
        result = classifier.classify("Hello world")
        
        assert isinstance(result, dict)
    
    def test_result_has_type(self):
        """classify() result should have type"""
        classifier = IntentClassifier()
        result = classifier.classify("Hello world")
        
        assert "type" in result
    
    def test_result_has_confidence(self):
        """classify() result should have confidence"""
        classifier = IntentClassifier()
        result = classifier.classify("Hello world")
        
        assert "confidence" in result
    
    def test_result_has_entities(self):
        """classify() result should have entities"""
        classifier = IntentClassifier()
        result = classifier.classify("Hello world")
        
        assert "entities" in result
    
    def test_result_has_original_input(self):
        """classify() result should have original_input"""
        classifier = IntentClassifier()
        result = classifier.classify("Test input")
        
        assert result["original_input"] == "Test input"


class TestBirthdayPartyIntent:
    """Test birthday_party intent classification"""
    
    def test_detects_birthday_party(self):
        """Should detect 'birthday party'"""
        classifier = IntentClassifier()
        result = classifier.classify("Plan a birthday party for my son")
        
        assert result["type"] == "birthday_party"
    
    def test_detects_celebrate_birthday(self):
        """Should detect 'celebrate birthday'"""
        classifier = IntentClassifier()
        result = classifier.classify("I want to celebrate my birthday")
        
        assert result["type"] == "birthday_party"
    
    def test_detects_birthday_weekend(self):
        """Should detect 'birthday weekend'"""
        classifier = IntentClassifier()
        result = classifier.classify("Planning a birthday weekend")
        
        assert result["type"] == "birthday_party"
    
    def test_high_confidence(self):
        """birthday_party match should have high confidence"""
        classifier = IntentClassifier()
        result = classifier.classify("Plan a birthday party")
        
        assert result["confidence"] == "high"


class TestTravelPlanningIntent:
    """Test travel_planning intent classification"""
    
    def test_detects_plan_trip(self):
        """Should detect 'plan trip'"""
        classifier = IntentClassifier()
        result = classifier.classify("Help me plan a trip to Paris")
        
        assert result["type"] == "travel_planning"
    
    def test_detects_vacation(self):
        """Should detect 'vacation'"""
        classifier = IntentClassifier()
        result = classifier.classify("I need a vacation next month")
        
        assert result["type"] == "travel_planning"
    
    def test_detects_holiday_plan(self):
        """Should detect 'holiday plan'"""
        classifier = IntentClassifier()
        result = classifier.classify("Make a holiday plan for December")
        
        assert result["type"] == "travel_planning"
    
    def test_detects_weekend_getaway(self):
        """Should detect 'weekend getaway'"""
        classifier = IntentClassifier()
        result = classifier.classify("Find a weekend getaway destination")
        
        assert result["type"] == "travel_planning"


class TestMeetingSchedulingIntent:
    """Test meeting_scheduling intent classification"""
    
    def test_detects_schedule_meeting(self):
        """Should detect 'schedule meeting'"""
        classifier = IntentClassifier()
        result = classifier.classify("Schedule a meeting with John")
        
        assert result["type"] == "meeting_scheduling"
    
    def test_detects_book_meeting(self):
        """Should detect 'book meeting'"""
        classifier = IntentClassifier()
        result = classifier.classify("Book a meeting room for tomorrow")
        
        assert result["type"] == "meeting_scheduling"
    
    def test_detects_zoom_meeting(self):
        """Should detect 'zoom meeting'"""
        classifier = IntentClassifier()
        result = classifier.classify("Set up a zoom meeting")
        
        assert result["type"] == "meeting_scheduling"
    
    def test_detects_instant_meeting(self):
        """Should detect 'instant meeting'"""
        classifier = IntentClassifier()
        result = classifier.classify("Start an instant meeting now")
        
        assert result["type"] == "meeting_scheduling"


class TestEventPlanningIntent:
    """Test event_planning intent classification"""
    
    def test_detects_plan_event(self):
        """Should detect 'plan event'"""
        classifier = IntentClassifier()
        result = classifier.classify("I need to plan an event")
        
        assert result["type"] == "event_planning"
    
    def test_detects_organize_event(self):
        """Should detect 'organize event'"""
        classifier = IntentClassifier()
        result = classifier.classify("Help me organize an event")
        
        assert result["type"] == "event_planning"
    
    def test_detects_host_event(self):
        """Should detect 'host event'"""
        classifier = IntentClassifier()
        result = classifier.classify("I want to host an event at my house")
        
        assert result["type"] == "event_planning"


class TestRestaurantBookingIntent:
    """Test restaurant_booking intent classification"""
    
    def test_detects_book_restaurant(self):
        """Should detect 'book restaurant'"""
        classifier = IntentClassifier()
        result = classifier.classify("Book a restaurant for dinner")
        
        assert result["type"] == "restaurant_booking"
    
    def test_detects_reserve_table(self):
        """Should detect 'reserve table'"""
        classifier = IntentClassifier()
        result = classifier.classify("Reserve a table for 4")
        
        assert result["type"] == "restaurant_booking"
    
    def test_detects_dinner_reservation(self):
        """Should detect 'dinner reservation'"""
        classifier = IntentClassifier()
        result = classifier.classify("Make a dinner reservation")
        
        assert result["type"] == "restaurant_booking"


class TestShoppingIntent:
    """Test shopping intent classification"""
    
    def test_detects_buy(self):
        """Should detect 'buy'"""
        classifier = IntentClassifier()
        result = classifier.classify("I want to buy a new laptop")
        
        assert result["type"] == "shopping"
    
    def test_detects_purchase(self):
        """Should detect 'purchase'"""
        classifier = IntentClassifier()
        result = classifier.classify("Help me purchase gifts")
        
        assert result["type"] == "shopping"
    
    def test_detects_order(self):
        """Should detect 'order'"""
        classifier = IntentClassifier()
        result = classifier.classify("Order some groceries")
        
        assert result["type"] == "shopping"
    
    def test_detects_shopping_for(self):
        """Should detect 'shopping for'"""
        classifier = IntentClassifier()
        result = classifier.classify("I'm shopping for clothes")
        
        assert result["type"] == "shopping"


class TestGeneralIntent:
    """Test general (default) intent classification"""
    
    def test_returns_general_for_unknown(self):
        """Should return general for unknown input"""
        classifier = IntentClassifier()
        result = classifier.classify("Hello, how are you?")
        
        assert result["type"] == "general"
    
    def test_low_confidence_for_general(self):
        """general intent should have low confidence"""
        classifier = IntentClassifier()
        result = classifier.classify("Random text here")
        
        assert result["confidence"] == "low"


class TestCaseInsensitivity:
    """Test that classification is case insensitive"""
    
    def test_uppercase_works(self):
        """UPPERCASE should be classified correctly"""
        classifier = IntentClassifier()
        result = classifier.classify("PLAN A BIRTHDAY PARTY")
        
        assert result["type"] == "birthday_party"
    
    def test_mixed_case_works(self):
        """MiXeD cAsE should be classified correctly"""
        classifier = IntentClassifier()
        result = classifier.classify("Schedule A Meeting Now")
        
        assert result["type"] == "meeting_scheduling"


class TestEntityExtraction:
    """Test entity extraction from classified intents"""
    
    def test_entities_is_dict(self):
        """entities should be a dict"""
        classifier = IntentClassifier()
        result = classifier.classify("Plan a birthday party tomorrow")
        
        assert isinstance(result["entities"], dict)


class TestIntentPriority:
    """Test intent pattern matching priority"""
    
    def test_first_match_wins(self):
        """First matching pattern should determine intent"""
        classifier = IntentClassifier()
        
        # This could match multiple intents
        result = classifier.classify("Plan a birthday party event")
        
        # Should match one specific intent
        assert result["type"] in ["birthday_party", "event_planning"]


class TestPatternVariations:
    """Test various pattern variations"""
    
    def test_birthday_celebration(self):
        """Should detect 'birthday celebration'"""
        classifier = IntentClassifier()
        result = classifier.classify("A birthday celebration for my wife")
        
        assert result["type"] == "birthday_party"
    
    def test_travel_to_place(self):
        """Should detect 'travel to'"""
        classifier = IntentClassifier()
        result = classifier.classify("I want to travel to Japan")
        
        assert result["type"] == "travel_planning"
    
    def test_visit_place(self):
        """Should detect 'visit place'"""
        classifier = IntentClassifier()
        result = classifier.classify("We should visit some places in Italy")
        
        assert result["type"] == "travel_planning"
    
    def test_meeting_right_now(self):
        """Should detect 'meeting right now'"""
        classifier = IntentClassifier()
        result = classifier.classify("I need a meeting right now")
        
        assert result["type"] == "meeting_scheduling"
