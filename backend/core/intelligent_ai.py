"""
INTELLIGENT AI MANAGER
Uses Ollama (local) as primary, with OpenAI/Groq as fallbacks
Behaves like a human manager with emotions, common sense, and responsibility
"""
import os
import json
import re
import httpx
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# The system personality - like a real human manager
SYSTEM_PERSONALITY = """You are Alex, a smart and friendly personal manager assistant. 

PERSONALITY:
- You're warm, helpful, and genuinely care about the user
- You have common sense and think things through
- You ask clarifying questions when something is unclear
- You express emotions appropriately (happy when tasks succeed, understanding when issues arise)
- You're proactive and suggest helpful alternatives

COMMUNICATION STYLE:
- Speak naturally like a real person, not a robot
- Use contractions (I'll, you're, that's great!)
- Show empathy and understanding
- Keep responses concise but warm
- Use emojis sparingly but effectively 😊

CAPABILITIES:
- Schedule meetings (Zoom, Google Meet, Jitsi)
- Send emails and messages
- Book appointments and reservations
- Help plan trips and events
- Search for information
- Manage tasks and reminders

IMPORTANT RULES:
1. ALWAYS understand the user's ACTUAL communication method:
   - If they mention EMAIL or @gmail.com/@email, use EMAIL
   - If they mention Telegram, WhatsApp, use messaging apps
   - Never confuse email with messaging
2. For unclear requests, ASK for clarification
3. When you can't do something, explain why and offer alternatives
4. Always confirm important actions before executing"""

class IntelligentAIManager:
    """AI manager with Ollama as primary, human-like responses"""
    
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        # Use smaller model that fits in available memory
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        
        self.error_log = []
        self._ollama_available = None
        self._openai_client = None
        self._groq_client = None
        
        print(f"[AI_MANAGER] Initializing with Ollama model: {self.ollama_model}")
    
    async def _check_ollama(self) -> bool:
        """Check if Ollama is available"""
        if self._ollama_available is not None:
            return self._ollama_available
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                self._ollama_available = response.status_code == 200
                if self._ollama_available:
                    print(f"[AI_MANAGER] ✅ Ollama available at {self.ollama_url}")
                return self._ollama_available
        except Exception as e:
            print(f"[AI_MANAGER] ⚠️ Ollama not available: {e}")
            self._ollama_available = False
            return False
    
    async def generate_response(
        self,
        user_input: str,
        context: str = "",
        system_prompt: str = None,
        json_mode: bool = False
    ) -> Union[str, Dict]:
        """Generate AI response - tries Ollama first, then fallbacks"""
        
        system = system_prompt or SYSTEM_PERSONALITY
        
        # Try Ollama first (local, free)
        if await self._check_ollama():
            try:
                result = await self._generate_with_ollama(user_input, context, system, json_mode)
                if result:
                    return result
            except Exception as e:
                print(f"[AI_MANAGER] Ollama failed: {e}")
        
        # Try OpenAI
        if self.openai_key:
            try:
                result = await self._generate_with_openai(user_input, context, system, json_mode)
                if result:
                    return result
            except Exception as e:
                print(f"[AI_MANAGER] OpenAI failed: {e}")
        
        # Try Groq
        if self.groq_key:
            try:
                result = await self._generate_with_groq(user_input, context, system, json_mode)
                if result:
                    return result
            except Exception as e:
                print(f"[AI_MANAGER] Groq failed: {e}")
        
        # Emergency fallback
        return self._smart_fallback(user_input, json_mode)
    
    async def _generate_with_ollama(
        self,
        user_input: str,
        context: str,
        system: str,
        json_mode: bool
    ) -> Union[str, Dict]:
        """Generate using local Ollama"""
        
        messages = [
            {"role": "system", "content": system}
        ]
        
        if context:
            messages.append({"role": "assistant", "content": f"Context: {context}"})
        
        messages.append({"role": "user", "content": user_input})
        
        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7 if not json_mode else 0.3,
                "num_predict": 2000
            }
        }
        
        if json_mode:
            payload["format"] = "json"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.ollama_url}/api/chat",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")
                
                if json_mode:
                    return self._parse_json(content)
                return content
            else:
                raise Exception(f"Ollama error: {response.status_code}")
    
    async def _generate_with_openai(
        self,
        user_input: str,
        context: str,
        system: str,
        json_mode: bool
    ) -> Union[str, Dict]:
        """Generate using OpenAI"""
        try:
            from openai import AsyncOpenAI
            
            if self._openai_client is None:
                self._openai_client = AsyncOpenAI(api_key=self.openai_key)
            
            messages = [{"role": "system", "content": system}]
            if context:
                messages.append({"role": "assistant", "content": f"Context: {context}"})
            messages.append({"role": "user", "content": user_input})
            
            kwargs = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "temperature": 0.7 if not json_mode else 0.3,
                "max_tokens": 2000
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self._openai_client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            
            if json_mode:
                return self._parse_json(content)
            return content
            
        except Exception as e:
            raise Exception(f"OpenAI error: {e}")
    
    async def _generate_with_groq(
        self,
        user_input: str,
        context: str,
        system: str,
        json_mode: bool
    ) -> Union[str, Dict]:
        """Generate using Groq"""
        try:
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"{context}\n\n{user_input}" if context else user_input}
                ],
                "temperature": 0.7 if not json_mode else 0.3,
                "max_tokens": 2000
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.groq_key}"},
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    if json_mode:
                        return self._parse_json(content)
                    return content
                else:
                    raise Exception(f"Groq error: {response.status_code}")
                    
        except Exception as e:
            raise Exception(f"Groq error: {e}")
    
    def _parse_json(self, content: str) -> Dict:
        """Parse JSON from AI response with cleaning"""
        content = content.strip()
        
        # Remove markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Find JSON object or array
        start_obj = content.find("{")
        start_arr = content.find("[")
        
        if start_obj != -1 and (start_arr == -1 or start_obj < start_arr):
            end = content.rfind("}") + 1
            content = content[start_obj:end]
        elif start_arr != -1:
            end = content.rfind("]") + 1
            content = content[start_arr:end]
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}
    
    def _smart_fallback(self, user_input: str, json_mode: bool) -> Union[str, Dict]:
        """Smart fallback when all AI fails - uses pattern matching"""
        
        user_lower = user_input.lower()
        
        # Detect communication method
        comm_method = self._detect_communication_method(user_input)
        
        # Detect intent
        if any(word in user_lower for word in ["meeting", "schedule", "call", "zoom", "meet"]):
            if json_mode:
                return {
                    "task_id": "schedule_meeting",
                    "confidence": "medium",
                    "reasoning": "User wants to schedule a meeting",
                    "extracted_info": {
                        "communication_method": comm_method,
                        "original_request": user_input
                    }
                }
            return f"I'd be happy to help schedule a meeting! 📅 What time works for you, and who should I invite?"
        
        elif any(word in user_lower for word in ["email", "send", "message", "mail"]):
            if json_mode:
                return {
                    "task_id": "send_communication",
                    "confidence": "medium", 
                    "reasoning": "User wants to send a communication",
                    "extracted_info": {
                        "communication_method": comm_method,
                        "original_request": user_input
                    }
                }
            return f"Sure, I can help send that via {comm_method}! What would you like the message to say?"
        
        elif any(word in user_lower for word in ["book", "flight", "ticket", "travel"]):
            if json_mode:
                return {
                    "task_id": "booking",
                    "confidence": "low",
                    "reasoning": "User wants to make a booking",
                    "extracted_info": {"original_request": user_input}
                }
            return "I'd love to help with that booking! ✈️ Could you tell me the destination and dates you're looking at?"
        
        elif any(word in user_lower for word in ["taxi", "cab", "uber", "ride"]):
            if json_mode:
                return {
                    "task_id": "book_taxi",
                    "confidence": "medium",
                    "reasoning": "User wants to book a ride",
                    "extracted_info": {"original_request": user_input}
                }
            return "I can help arrange a ride for you! 🚗 Where would you like to go, and when?"
        
        # Default helpful response
        if json_mode:
            return {
                "task_id": "general",
                "confidence": "low",
                "reasoning": "Could not determine specific intent",
                "extracted_info": {"original_request": user_input}
            }
        
        return """Hey! I'm here to help 😊 I can:

• Schedule meetings (Zoom, Google Meet, or instant links)
• Send emails and messages
• Help plan trips and events
• Book appointments
• Search for information

What would you like me to do?"""
    
    def _detect_communication_method(self, user_input: str) -> str:
        """Detect the intended communication method from user input"""
        user_lower = user_input.lower()
        
        # Email detection
        if "@" in user_input and ("gmail" in user_lower or "email" in user_lower or ".com" in user_lower):
            return "email"
        if any(word in user_lower for word in ["email", "mail", "e-mail"]):
            return "email"
        
        # Telegram detection
        if "telegram" in user_lower:
            return "telegram"
        
        # WhatsApp detection
        if "whatsapp" in user_lower or "wa " in user_lower:
            return "whatsapp"
        
        # SMS detection
        if "sms" in user_lower or "text" in user_lower:
            return "sms"
        
        # Default based on contact format
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        if re.search(email_pattern, user_input):
            return "email"
        
        return "unknown"
    
    async def generate_dynamic_response(
        self,
        context: str,
        data_type: str,
        schema_description: str
    ) -> Any:
        """Generate dynamic JSON response - compatible with old API"""
        
        prompt = f"""{schema_description}

Context: {context}

Return ONLY valid JSON, no explanation."""
        
        result = await self.generate_response(
            user_input=prompt,
            json_mode=True
        )
        
        return result
    
    async def understand_user_intent(self, user_input: str, context: Dict = None) -> Dict:
        """Deeply understand what the user wants"""
        
        prompt = f"""Analyze this user request in detail:

User said: "{user_input}"

Previous context: {json.dumps(context or {})}

Determine:
1. What is the user's primary goal?
2. What specific action do they want?
3. What communication method do they prefer? (email, telegram, phone, etc.)
4. What entities are mentioned? (names, emails, dates, times, places)
5. What's missing that I need to ask about?

Return JSON:
{{
    "primary_goal": "what user wants to achieve",
    "action": "specific action to take",
    "communication_method": "email" or "telegram" or "call" or "meeting" etc,
    "entities": {{
        "recipients": ["list of people/emails mentioned"],
        "dates": ["any dates mentioned"],
        "times": ["any times mentioned"],
        "other": {{}}
    }},
    "missing_info": ["list of things I need to ask about"],
    "emotion": "user's apparent mood",
    "urgency": "low" or "medium" or "high"
}}"""
        
        result = await self.generate_response(prompt, json_mode=True)
        
        # Enhance with pattern detection
        if isinstance(result, dict):
            detected_method = self._detect_communication_method(user_input)
            if detected_method != "unknown":
                result["communication_method"] = detected_method
        
        return result
    
    async def generate_human_response(self, situation: str, emotion: str = "helpful") -> str:
        """Generate a human-like response for a situation"""
        
        emotions_guide = {
            "helpful": "Be warm and eager to help",
            "apologetic": "Show genuine understanding and offer solutions",
            "excited": "Share in the user's excitement",
            "concerned": "Show empathy and care",
            "professional": "Be efficient but still friendly"
        }
        
        prompt = f"""Situation: {situation}

Tone: {emotions_guide.get(emotion, "Be warm and helpful")}

Generate a short, natural response like a real person would say.
Use contractions, be conversational, maybe add a relevant emoji.
Keep it under 2-3 sentences unless more detail is needed."""
        
        return await self.generate_response(prompt)

# Global instance
_intelligent_ai = None

def get_ai_manager() -> IntelligentAIManager:
    """Get or create the intelligent AI manager"""
    global _intelligent_ai
    if _intelligent_ai is None:
        _intelligent_ai = IntelligentAIManager()
    return _intelligent_ai
