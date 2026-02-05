"""
SELF-HEALING AI CONVERSATION MANAGER
Uses OpenAI/Groq for ALL decisions, data generation, and error recovery
"""
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

class SelfHealingAIManager:
    """AI-powered manager with automatic error recovery"""
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.2-90b-text-preview")
        
        self.openai_client = None
        self.groq_client = None
        self.error_log = []
        
        # Initialize clients
        if self.openai_key and OPENAI_AVAILABLE:
            self.openai_client = AsyncOpenAI(api_key=self.openai_key)
            print("[AI_MANAGER] OpenAI initialized")
        
        if self.groq_key and GROQ_AVAILABLE:
            self.groq_client = Groq(api_key=self.groq_key)
            print("[AI_MANAGER] Groq initialized")
            
        if not self.openai_client and not self.groq_client:
            print("[AI_MANAGER] ⚠️ NO AI CLIENTS AVAILABLE - USING MOCK MODE")
            self.mock_mode = True
        else:
            self.mock_mode = False
    
    async def generate_destinations(self, user_input: str) -> List[Dict[str, Any]]:
        """Generate location-specific destinations using AI with error recovery"""
        
        prompt = f"""User said: "{user_input}"

Extract the location mentioned (if any) and generate 4 specific destination options in that region.
If no location mentioned, suggest popular Indian destinations.

Return ONLY valid JSON array (no markdown, no explanation):
[
  {{"id": "destination_id", "name": "Destination Name", "description": "Brief description"}},
  ...
]"""

        try:
            # Try OpenAI first
            if self.openai_client:
                try:
                    return await self._generate_with_openai(prompt, "destinations")
                except Exception as e:
                    print(f"[AI_MANAGER] OpenAI failed, trying Groq... Error: {e}")
                    if self.groq_client:
                        return self._generate_with_groq(prompt, "destinations")
                    raise e
            # Fallback to Groq
            elif self.groq_client:
                return self._generate_with_groq(prompt, "destinations")
            else:
                raise Exception("No AI client available")
                
        except Exception as e:
            print(f"[AI_MANAGER] Error in destination generation: {e}")
            # Self-healing: Try alternative approach
            return await self._self_heal_destinations(user_input, str(e))
    
    async def generate_accommodations(self, destination: str, user_input: str) -> List[Dict[str, Any]]:
        """Generate accommodation options using AI"""
        
        prompt = f"""For destination: {destination}
User context: {user_input}

Generate 4 real hotel/resort options in {destination}.

Return ONLY valid JSON array:
[
  {{"id": "hotel_id", "name": "Hotel Name", "price": "₹X,XXX/night", "rating": "X★"}},
  ...
]"""

        try:
            if self.openai_client:
                try:
                    return await self._generate_with_openai(prompt, "accommodations")
                except Exception as e:
                    print(f"[AI_MANAGER] OpenAI failed, trying Groq... Error: {e}")
                    if self.groq_client:
                        return self._generate_with_groq(prompt, "accommodations")
                    raise e
            elif self.groq_client:
                return self._generate_with_groq(prompt, "accommodations")
            else:
                raise Exception("No AI client available")
                
        except Exception as e:
            print(f"[AI_MANAGER] Error in accommodation generation: {e}")
            return await self._self_heal_accommodations(destination, str(e))
    
    async def generate_activities(self, destination: str, user_input: str) -> List[Dict[str, Any]]:
        """Generate activity options using AI"""
        
        prompt = f"""For destination: {destination}
User context: {user_input}

Generate 5 specific activities/experiences in {destination}.

Return ONLY valid JSON array:
[
  {{"id": "activity_id", "name": "Activity Name", "duration": "X hours"}},
  ...
]"""

        try:
            if self.openai_client:
                try:
                    return await self._generate_with_openai(prompt, "activities")
                except Exception as e:
                    print(f"[AI_MANAGER] OpenAI failed, trying Groq... Error: {e}")
                    if self.groq_client:
                        return self._generate_with_groq(prompt, "activities")
                    raise e
            elif self.groq_client:
                return self._generate_with_groq(prompt, "activities")
            else:
                raise Exception("No AI client available")
                
        except Exception as e:
            print(f"[AI_MANAGER] Error in activity generation: {e}")
            return await self._self_heal_activities(destination, str(e))

    async def generate_dynamic_response(self, context: str, data_type: str, schema_description: str) -> Any:
        """Generate dynamic response based on context and schema"""
        
        prompt = f"""Context: {context}
        
Generate {data_type}.
{schema_description}

Return ONLY valid JSON."""

        try:
            if self.openai_client:
                try:
                    return await self._generate_with_openai(prompt, data_type)
                except Exception as e:
                    print(f"[AI_MANAGER] OpenAI failed, trying Groq... Error: {e}")
                    if self.groq_client:
                        return self._generate_with_groq(prompt, data_type)
                    raise e
            elif self.groq_client:
                return self._generate_with_groq(prompt, data_type)
            else:
                raise Exception("No AI client available")
        except Exception as e:
            print(f"[AI_MANAGER] Error in dynamic generation: {e}")
            return [] # Return empty list on failure for now
    
    async def _generate_with_openai(self, prompt: str, data_type: str) -> List[Dict[str, Any]]:
        """Generate using OpenAI with error handling"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a travel expert. Return ONLY valid JSON arrays, no markdown formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up response
            content = self._clean_json_response(content)
            
            data = json.loads(content)
            
            print(f"[AI_MANAGER] OpenAI generated {len(data)} {data_type}")
            return data
            
        except json.JSONDecodeError as e:
            print(f"[AI_MANAGER] JSON decode error: {e}")
            print(f"[AI_MANAGER] Raw response: {content}")
            # Try to fix JSON
            return await self._fix_json_with_ai(content, data_type)
        except Exception as e:
            print(f"[AI_MANAGER] OpenAI error: {e}")
            raise
    
    def _generate_with_groq(self, prompt: str, data_type: str) -> List[Dict[str, Any]]:
        """Generate using Groq with error handling"""
        try:
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {"role": "system", "content": "You are a travel expert. Return ONLY valid JSON arrays, no markdown formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up response
            content = self._clean_json_response(content)
            
            data = json.loads(content)
            
            print(f"[AI_MANAGER] Groq generated {len(data)} {data_type}")
            return data
            
        except json.JSONDecodeError as e:
            print(f"[AI_MANAGER] JSON decode error: {e}")
            print(f"[AI_MANAGER] Raw response: {content}")
            # Try to fix JSON synchronously
            return self._fix_json_sync(content, data_type)
        except Exception as e:
            print(f"[AI_MANAGER] Groq error: {e}")
            raise
    
    def _clean_json_response(self, content: str) -> str:
        """Clean AI response to extract valid JSON"""
        # Remove markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Remove any text before start or after end
        content = content.strip()
        
        # Find start of JSON
        start_brace = content.find("{")
        start_bracket = content.find("[")
        
        if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
            # It's an object
            start = start_brace
            end = content.rindex("}") + 1
            content = content[start:end]
        elif start_bracket != -1:
            # It's an array
            start = start_bracket
            end = content.rindex("]") + 1
            content = content[start:end]
        
        return content
    
    async def _fix_json_with_ai(self, broken_json: str, data_type: str) -> List[Dict[str, Any]]:
        """Use AI to fix broken JSON - SELF-HEALING"""
        print("[AI_MANAGER] Attempting self-healing JSON fix...")
        
        fix_prompt = f"""The following JSON is malformed:

{broken_json}

Fix it and return ONLY valid JSON array for {data_type}. No explanation, just the fixed JSON."""

        try:
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[{"role": "user", "content": fix_prompt}],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                fixed_content = response.choices[0].message.content.strip()
                fixed_content = self._clean_json_response(fixed_content)
                data = json.loads(fixed_content)
                
                print(f"[AI_MANAGER] ✅ Self-healed! Fixed {data_type}")
                return data
        except Exception as e:
            print(f"[AI_MANAGER] Self-healing failed: {e}")
            # Ultimate fallback
            return self._emergency_fallback(data_type)
    
    def _fix_json_sync(self, broken_json: str, data_type: str) -> List[Dict[str, Any]]:
        """Synchronous JSON fix for Groq"""
        print("[AI_MANAGER] Attempting synchronous JSON fix...")
        
        fix_prompt = f"""Fix this malformed JSON and return ONLY valid JSON array:

{broken_json}"""

        try:
            if self.groq_client:
                response = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": fix_prompt}],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                fixed_content = response.choices[0].message.content.strip()
                fixed_content = self._clean_json_response(fixed_content)
                data = json.loads(fixed_content)
                
                print(f"[AI_MANAGER] ✅ Self-healed! Fixed {data_type}")
                return data
        except Exception as e:
            print(f"[AI_MANAGER] Self-healing failed: {e}")
            return self._emergency_fallback(data_type)
    
    async def _self_heal_destinations(self, user_input: str, error: str) -> List[Dict[str, Any]]:
        """Self-healing for destination generation failures"""
        print(f"[AI_MANAGER] Self-healing destinations after error: {error}")
        
        # Log error
        self.error_log.append({
            "type": "destination_generation",
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Try simpler prompt
        simple_prompt = f"List 4 destinations in India for: {user_input}. Return as JSON array with id, name, description."
        
        try:
            if self.openai_client:
                return await self._generate_with_openai(simple_prompt, "destinations")
            elif self.groq_client:
                return self._generate_with_groq(simple_prompt, "destinations")
        except:
            pass
        
        # Emergency fallback
        return self._emergency_fallback("destinations")
    
    async def _self_heal_accommodations(self, destination: str, error: str) -> List[Dict[str, Any]]:
        """Self-healing for accommodation generation failures"""
        print(f"[AI_MANAGER] Self-healing accommodations after error: {error}")
        return self._emergency_fallback("accommodations")
    
    async def _self_heal_activities(self, destination: str, error: str) -> List[Dict[str, Any]]:
        """Self-healing for activity generation failures"""
        print(f"[AI_MANAGER] Self-healing activities after error: {error}")
        return self._emergency_fallback("activities")
    
    def _emergency_fallback(self, data_type: str) -> List[Dict[str, Any]]:
        """Emergency fallback data when all AI attempts fail"""
        print(f"[AI_MANAGER] Using emergency fallback for {data_type}")
        
        if data_type == "destinations":
            return [
                {"id": "coorg", "name": "Coorg", "description": "Coffee plantations"},
                {"id": "hampi", "name": "Hampi", "description": "Ancient ruins"},
                {"id": "gokarna", "name": "Gokarna", "description": "Beach town"},
                {"id": "chikmagalur", "name": "Chikmagalur", "description": "Hill station"}
            ]
        elif data_type == "accommodations":
            return [
                {"id": "luxury", "name": "Luxury Resort", "price": "₹10,000/night", "rating": "5★"},
                {"id": "boutique", "name": "Boutique Hotel", "price": "₹7,000/night", "rating": "4★"}
            ]
        elif data_type == "activities":
            return [
                {"id": "sightseeing", "name": "Sightseeing Tour", "duration": "4 hours"},
                {"id": "trekking", "name": "Nature Trek", "duration": "3 hours"}
            ]
        
        return []
    
    def get_error_log(self) -> List[Dict[str, Any]]:
        """Get error log for debugging"""
        return self.error_log

# Global instance
_ai_manager = None

def get_ai_manager() -> SelfHealingAIManager:
    """Get or create global AI manager instance"""
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = SelfHealingAIManager()
    return _ai_manager
