"""
Advanced Intent Classification System
Classifies user intents into specific categories for better handling
"""
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

class IntentClassifier:
    """Classifies user intents into actionable categories"""
    
    def __init__(self):
        self.intent_patterns = {
            "birthday_party": [
                r"birthday.*party",
                r"celebrate.*birthday",
                r"birthday.*weekend",
                r"birthday.*celebration"
            ],
            "travel_planning": [
                r"plan.*trip",
                r"travel.*to",
                r"visit.*place",
                r"vacation",
                r"holiday.*plan",
                r"weekend.*getaway"
            ],
            "meeting_scheduling": [
                r"schedule.*meeting",
                r"book.*meeting",
                r"arrange.*call",
                r"set.*up.*meeting",
                r"zoom.*meeting",
                r"create.*meeting",
                r"meeting.*now",
                r"meeting.*right now",
                r"start.*meeting",
                r"instant.*meeting"
            ],
            "event_planning": [
                r"plan.*event",
                r"organize.*event",
                r"arrange.*party",
                r"host.*event"
            ],
            "restaurant_booking": [
                r"book.*restaurant",
                r"reserve.*table",
                r"dinner.*reservation"
            ],
            "shopping": [
                r"buy.*",
                r"purchase.*",
                r"order.*",
                r"shopping.*for"
            ]
        }
    
    def classify(self, user_input: str) -> Dict[str, Any]:
        """
        Classify user input into intent category
        Returns intent type, confidence, and extracted entities
        """
        user_input_lower = user_input.lower()
        
        # Check each intent pattern
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input_lower):
                    entities = self._extract_entities(user_input, intent_type)
                    return {
                        "type": intent_type,
                        "confidence": "high",
                        "entities": entities,
                        "original_input": user_input
                    }
        
        # Default to general if no match
        return {
            "type": "general",
            "confidence": "low",
            "entities": {},
            "original_input": user_input
        }
    
    def _extract_entities(self, user_input: str, intent_type: str) -> Dict[str, Any]:
        """Extract relevant entities based on intent type"""
        entities = {}
        user_input_lower = user_input.lower()
        
        # Extract time references
        time_entities = self._extract_time_entities(user_input_lower)
        entities.update(time_entities)
        
        # Extract location references
        location_entities = self._extract_locations(user_input_lower)
        entities.update(location_entities)
        
        # Intent-specific extraction
        if intent_type == "birthday_party":
            entities["event_type"] = "birthday_party"
            entities["requires_planning"] = True
            
        elif intent_type == "travel_planning":
            entities["requires_destination_selection"] = True
            entities["requires_accommodation"] = True
            
        elif intent_type == "meeting_scheduling":
            entities["requires_participants"] = True
            entities["requires_time_slot"] = True
        
        return entities
    
    def _extract_time_entities(self, text: str) -> Dict[str, Any]:
        """Extract time-related entities"""
        entities = {}
        
        # Days of week
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in days:
            if day in text:
                entities["day"] = day
        
        # Relative time
        if "today" in text:
            entities["when"] = "today"
        elif "tomorrow" in text:
            entities["when"] = "tomorrow"
        elif "this weekend" in text or "weekend" in text:
            entities["when"] = "this_weekend"
        elif "next week" in text:
            entities["when"] = "next_week"
        
        # Time of day
        time_match = re.search(r'(\d{1,2})\s*(am|pm|:)', text)
        if time_match:
            entities["time"] = time_match.group(0)
        
        return entities
    
    def _extract_locations(self, text: str) -> Dict[str, str]:
        """Extract location entities"""
        entities = {}
        
        # Common Indian cities/destinations
        locations = {
            "goa": "Goa",
            "mumbai": "Mumbai",
            "delhi": "Delhi",
            "bangalore": "Bangalore",
            "chennai": "Chennai",
            "hyderabad": "Hyderabad",
            "pune": "Pune",
            "jaipur": "Jaipur",
            "udaipur": "Udaipur",
            "manali": "Manali",
            "shimla": "Shimla",
            "kerala": "Kerala",
            "kashmir": "Kashmir"
        }
        
        for key, value in locations.items():
            if key in text:
                entities["destination"] = value
                entities["location"] = value
        
        return entities
    
    def requires_clarification(self, classified_intent: Dict[str, Any]) -> bool:
        """Check if intent requires clarification from user"""
        intent_type = classified_intent["type"]
        entities = classified_intent["entities"]
        
        # Birthday party needs destination
        if intent_type == "birthday_party":
            return "destination" not in entities
        
        # Travel planning needs destination
        if intent_type == "travel_planning":
            return "destination" not in entities
        
        # Meeting needs time
        if intent_type == "meeting_scheduling":
            return "time" not in entities and "when" not in entities
        
        return False
    
    def generate_clarification_question(self, classified_intent: Dict[str, Any]) -> str:
        """Generate a clarification question based on missing information"""
        intent_type = classified_intent["type"]
        entities = classified_intent["entities"]
        
        if intent_type == "birthday_party":
            if "destination" not in entities:
                return "Where would you like to celebrate your birthday? (e.g., Goa, Mumbai, Bangalore)"
        
        if intent_type == "travel_planning":
            if "destination" not in entities:
                return "Where would you like to travel? (e.g., Goa, Manali, Kerala)"
        
        if intent_type == "meeting_scheduling":
            if "time" not in entities and "when" not in entities:
                return "When would you like to schedule the meeting?"
        
        return "Could you provide more details about your request?"
