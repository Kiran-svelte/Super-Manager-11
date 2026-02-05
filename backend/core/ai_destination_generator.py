"""
AI-Powered Destination and Activity Generator
Uses Groq API (free) to generate location-specific suggestions
Falls back to intelligent defaults if API not available
"""
import os
import json
from typing import List, Dict, Any

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("[AI_GENERATOR] Groq not installed. Install with: pip install groq")

class AIDestinationGenerator:
    """Generate location-specific destinations and activities using AI"""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.client = None
        
        if self.api_key and GROQ_AVAILABLE:
            try:
                self.client = Groq(api_key=self.api_key)
                print("[AI_GENERATOR] Groq API initialized")
            except Exception as e:
                print(f"[AI_GENERATOR] Failed to initialize Groq: {e}")
    
    def generate_destinations(self, user_input: str, location_hint: str = "") -> List[Dict[str, Any]]:
        """Generate destination options based on user input"""
        
        # Extract location from user input if present
        location = self._extract_location(user_input, location_hint)
        
        if self.client:
            return self._generate_with_ai(user_input, location)
        else:
            return self._generate_fallback(location)
    
    def _extract_location(self, user_input: str, location_hint: str) -> str:
        """Extract location from user input"""
        user_lower = user_input.lower()
        
        # Check for specific locations
        locations = {
            "karnataka": ["karnataka", "bengaluru", "bangalore", "mysore", "coorg", "hampi"],
            "goa": ["goa"],
            "kerala": ["kerala", "kochi", "munnar"],
            "rajasthan": ["rajasthan", "jaipur", "udaipur", "jodhpur"],
            "himachal": ["himachal", "manali", "shimla"],
            "maharashtra": ["maharashtra", "mumbai", "pune", "lonavala"],
            "tamil nadu": ["tamil nadu", "chennai", "ooty", "kodaikanal"]
        }
        
        for state, keywords in locations.items():
            if any(keyword in user_lower for keyword in keywords):
                return state
        
        return location_hint or "india"
    
    def _generate_with_ai(self, user_input: str, location: str) -> List[Dict[str, Any]]:
        """Generate destinations using Groq AI"""
        try:
            prompt = f"""Given the user request: "{user_input}"
And the location context: "{location}"

Generate 4 specific destination options in {location} for celebrating a birthday. 
For each destination, provide:
- id: lowercase name with underscores
- name: Proper name
- description: Brief appealing description (max 50 chars)

Return ONLY a JSON array, no other text:
[{{"id": "...", "name": "...", "description": "..."}}, ...]"""

            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            destinations = json.loads(content)
            
            print(f"[AI_GENERATOR] Generated {len(destinations)} destinations for {location}")
            return destinations
            
        except Exception as e:
            print(f"[AI_GENERATOR] AI generation failed: {e}")
            return self._generate_fallback(location)
    
    def _generate_fallback(self, location: str) -> List[Dict[str, Any]]:
        """Generate intelligent fallback destinations based on location"""
        
        destinations_by_location = {
            "karnataka": [
                {"id": "coorg", "name": "Coorg", "description": "Coffee plantations and misty hills"},
                {"id": "hampi", "name": "Hampi", "description": "Ancient ruins and boulder landscapes"},
                {"id": "chikmagalur", "name": "Chikmagalur", "description": "Hill station with coffee estates"},
                {"id": "gokarna", "name": "Gokarna", "description": "Peaceful beaches and temples"}
            ],
            "goa": [
                {"id": "north_goa", "name": "North Goa", "description": "Beaches and nightlife"},
                {"id": "south_goa", "name": "South Goa", "description": "Peaceful beaches and resorts"},
                {"id": "panjim", "name": "Panjim", "description": "Portuguese heritage and culture"},
                {"id": "arambol", "name": "Arambol", "description": "Hippie vibe and beach parties"}
            ],
            "kerala": [
                {"id": "munnar", "name": "Munnar", "description": "Tea gardens and hill station"},
                {"id": "alleppey", "name": "Alleppey", "description": "Backwaters and houseboats"},
                {"id": "wayanad", "name": "Wayanad", "description": "Wildlife and waterfalls"},
                {"id": "varkala", "name": "Varkala", "description": "Cliff beaches and yoga"}
            ]
        }
        
        # Return location-specific destinations or default
        return destinations_by_location.get(location.lower(), [
            {"id": "coorg", "name": "Coorg", "description": "Coffee plantations and misty hills"},
            {"id": "hampi", "name": "Hampi", "description": "Ancient ruins and boulder landscapes"},
            {"id": "chikmagalur", "name": "Chikmagalur", "description": "Hill station with coffee estates"},
            {"id": "gokarna", "name": "Gokarna", "description": "Peaceful beaches and temples"}
        ])
    
    def generate_accommodations(self, destination: str, user_input: str = "") -> List[Dict[str, Any]]:
        """Generate accommodation options for a destination"""
        
        if self.client:
            return self._generate_accommodations_with_ai(destination, user_input)
        else:
            return self._generate_accommodations_fallback(destination)
    
    def _generate_accommodations_with_ai(self, destination: str, user_input: str) -> List[Dict[str, Any]]:
        """Generate accommodations using AI"""
        try:
            prompt = f"""For the destination: {destination}
User context: {user_input}

Generate 4 real accommodation options (hotels/resorts) in {destination}.
For each, provide:
- id: lowercase name with underscores
- name: Actual hotel/resort name
- price: Approximate price per night in ₹
- rating: Star rating (e.g., "5★")

Return ONLY a JSON array:
[{{"id": "...", "name": "...", "price": "₹.../night", "rating": "...★"}}, ...]"""

            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            accommodations = json.loads(content)
            return accommodations
            
        except Exception as e:
            print(f"[AI_GENERATOR] Accommodation generation failed: {e}")
            return self._generate_accommodations_fallback(destination)
    
    def _generate_accommodations_fallback(self, destination: str) -> List[Dict[str, Any]]:
        """Fallback accommodations"""
        return [
            {"id": "luxury_resort", "name": f"{destination.title()} Luxury Resort", "price": "₹10,000/night", "rating": "5★"},
            {"id": "boutique_hotel", "name": f"{destination.title()} Boutique Hotel", "price": "₹7,000/night", "rating": "4★"},
            {"id": "heritage_stay", "name": f"{destination.title()} Heritage Stay", "price": "₹5,000/night", "rating": "4★"},
            {"id": "budget_hotel", "name": f"{destination.title()} Comfort Inn", "price": "₹3,000/night", "rating": "3★"}
        ]
    
    def generate_activities(self, destination: str, user_input: str = "") -> List[Dict[str, Any]]:
        """Generate activity options for a destination"""
        
        if self.client:
            return self._generate_activities_with_ai(destination, user_input)
        else:
            return self._generate_activities_fallback(destination)
    
    def _generate_activities_with_ai(self, destination: str, user_input: str) -> List[Dict[str, Any]]:
        """Generate activities using AI"""
        try:
            prompt = f"""For the destination: {destination}
User context: {user_input}

Generate 5 specific activities/experiences available in {destination}.
For each, provide:
- id: lowercase name with underscores
- name: Activity name
- duration: Estimated duration

Return ONLY a JSON array:
[{{"id": "...", "name": "...", "duration": "..."}}, ...]"""

            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            activities = json.loads(content)
            return activities
            
        except Exception as e:
            print(f"[AI_GENERATOR] Activity generation failed: {e}")
            return self._generate_activities_fallback(destination)
    
    def _generate_activities_fallback(self, destination: str) -> List[Dict[str, Any]]:
        """Fallback activities"""
        return [
            {"id": "sightseeing", "name": f"{destination.title()} Sightseeing Tour", "duration": "4 hours"},
            {"id": "local_cuisine", "name": "Local Cuisine Experience", "duration": "2 hours"},
            {"id": "nature_walk", "name": "Nature Walk/Trek", "duration": "3 hours"},
            {"id": "cultural_tour", "name": "Cultural Heritage Tour", "duration": "3 hours"},
            {"id": "adventure_sports", "name": "Adventure Activities", "duration": "2 hours"}
        ]

# Global instance
_ai_generator = None

def get_ai_generator() -> AIDestinationGenerator:
    """Get or create global AI generator instance"""
    global _ai_generator
    if _ai_generator is None:
        _ai_generator = AIDestinationGenerator()
    return _ai_generator
