"""
Advanced Intent Parsing System
"""
import json
from typing import Dict, List, Any
from openai import AsyncOpenAI
import os
import re

class IntentParser:
    """Advanced intent parsing with entity extraction"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self._client = None
        
        # Common intent patterns
        self.intent_patterns = {
            "schedule": ["schedule", "book", "appointment", "meeting", "calendar"],
            "search": ["find", "search", "look for", "where is"],
            "purchase": ["buy", "purchase", "order", "shop"],
            "manage": ["manage", "organize", "update", "change"],
            "analyze": ["analyze", "review", "report", "summary"],
            "communicate": ["send", "email", "message", "notify"]
        }
    
    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
        
        # Common intent patterns
        self.intent_patterns = {
            "schedule": ["schedule", "book", "appointment", "meeting", "calendar"],
            "search": ["find", "search", "look for", "where is"],
            "purchase": ["buy", "purchase", "order", "shop"],
            "manage": ["manage", "organize", "update", "change"],
            "analyze": ["analyze", "review", "report", "summary"],
            "communicate": ["send", "email", "message", "notify"]
        }
    
    async def parse(self, user_input: str, context: Dict = None) -> Dict[str, Any]:
        """Parse user intent with high accuracy"""
        context = context or {}
        
        # Quick pattern matching for common intents
        quick_intent = self._quick_classify(user_input)
        
        # Deep LLM-based parsing
        detailed_intent = await self._deep_parse(user_input, context)
        
        # Merge results
        intent = {
            **detailed_intent,
            "quick_classification": quick_intent,
            "confidence": self._calculate_confidence(user_input, detailed_intent)
        }
        
        return intent
    
    def _quick_classify(self, user_input: str) -> str:
        """Quick classification using patterns"""
        user_lower = user_input.lower()
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in user_lower for pattern in patterns):
                return intent
        return "general"
    
    async def _deep_parse(self, user_input: str, context: Dict) -> Dict[str, Any]:
        """Deep parsing using LLM"""
        system_prompt = """You are an expert intent parser. Extract:
1. Primary action and category
2. All entities (dates, times, people, locations, items, amounts)
3. User preferences and constraints
4. Required plugins/capabilities
5. Priority and urgency

Be precise and extract all relevant information."""
        
        try:
            if not self.api_key:
                # Fallback to pattern matching only
                return {
                    "action": self._quick_classify(user_input),
                    "category": "general",
                    "entities": self.extract_entities(user_input),
                    "constraints": [],
                    "priority": "medium",
                    "capabilities": []
                }
            
            response = await self._get_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User input: {user_input}\n\nContext: {json.dumps(context)}"}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {
                "action": "unknown",
                "category": "general",
                "entities": {},
                "constraints": [],
                "priority": "medium"
            }
    
    def _calculate_confidence(self, user_input: str, intent: Dict) -> float:
        """Calculate confidence score"""
        # Simple heuristic - in production, use more sophisticated method
        if intent.get("action") != "unknown" and intent.get("entities"):
            return 0.9
        elif intent.get("action") != "unknown":
            return 0.7
        return 0.5
    
    def extract_entities(self, user_input: str) -> Dict[str, Any]:
        """Extract entities using regex and patterns"""
        entities = {
            "dates": self._extract_dates(user_input),
            "times": self._extract_times(user_input),
            "amounts": self._extract_amounts(user_input),
            "locations": self._extract_locations(user_input)
        }
        return entities
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract date mentions"""
        # Simplified - use dateparser in production
        patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'(today|tomorrow|next week|next month)'
        ]
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        return dates
    
    def _extract_times(self, text: str) -> List[str]:
        """Extract time mentions"""
        patterns = [
            r'\d{1,2}:\d{2}\s*(am|pm)?',
            r'\d{1,2}\s*(am|pm)'
        ]
        times = []
        for pattern in patterns:
            times.extend(re.findall(pattern, text, re.IGNORECASE))
        return times
    
    def _extract_amounts(self, text: str) -> List[str]:
        """Extract monetary amounts"""
        pattern = r'\$?\d+(?:\.\d{2})?'
        return re.findall(pattern, text)
    
    def _extract_locations(self, text: str) -> List[str]:
        """Extract location mentions"""
        # Simplified - use NER in production
        location_keywords = ["at", "in", "near", "to"]
        words = text.split()
        locations = []
        for i, word in enumerate(words):
            if word.lower() in location_keywords and i + 1 < len(words):
                locations.append(" ".join(words[i+1:i+3]))
        return locations

