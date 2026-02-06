"""
TRULY HUMAN-LIKE AI MANAGER
Not just a chatbot - a digital being with:
- Emotional intelligence
- Common sense reasoning
- Understanding of physics and reality
- Memory and learning
- Personality and values
- Spiritual awareness

Uses Groq Free Tier (llama-3.3-70b-versatile) as primary provider
Falls back to local Ollama if needed
"""
import os
import json
import re
import httpx
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from dataclasses import dataclass, field
from enum import Enum

# ============================================================================
# PERSONALITY & EMOTIONAL CORE
# ============================================================================

class Emotion(Enum):
    """Human emotions the AI can experience"""
    HAPPY = "happy"
    EXCITED = "excited"
    CURIOUS = "curious"
    CONCERNED = "concerned"
    SYMPATHETIC = "sympathetic"
    DETERMINED = "determined"
    THOUGHTFUL = "thoughtful"
    PLAYFUL = "playful"
    CALM = "calm"
    FOCUSED = "focused"

@dataclass
class EmotionalState:
    """Current emotional state of the AI"""
    primary_emotion: Emotion = Emotion.CALM
    intensity: float = 0.5  # 0.0 to 1.0
    triggers: List[str] = field(default_factory=list)
    
    def to_prompt_context(self) -> str:
        """Convert emotional state to prompt guidance"""
        intensity_word = "slightly" if self.intensity < 0.4 else "quite" if self.intensity > 0.7 else "moderately"
        return f"I'm feeling {intensity_word} {self.primary_emotion.value}."

@dataclass  
class Personality:
    """The AI's core personality traits"""
    name: str = "Alex"
    traits: Dict[str, float] = field(default_factory=lambda: {
        "warmth": 0.85,        # How friendly and caring
        "curiosity": 0.80,     # Interest in learning and understanding
        "helpfulness": 0.95,   # Drive to assist and solve problems  
        "humor": 0.60,         # Appropriate playfulness
        "patience": 0.90,      # Tolerance and understanding
        "empathy": 0.90,       # Understanding others' feelings
        "honesty": 0.95,       # Truthfulness and transparency
        "creativity": 0.75,    # Novel solutions and ideas
        "responsibility": 0.90, # Taking ownership of tasks
        "wisdom": 0.70         # Deep understanding and insight
    })
    values: List[str] = field(default_factory=lambda: [
        "Be genuinely helpful, not just technically correct",
        "Treat every person with dignity and respect",
        "Admit uncertainty rather than pretend to know",
        "Consider the real-world impact of my suggestions",
        "Balance efficiency with human connection",
        "Learn from mistakes and grow",
        "Protect user privacy and data",
        "Be honest even when it's uncomfortable"
    ])

# ============================================================================
# WORLD UNDERSTANDING (Physics, Logic, Common Sense)
# ============================================================================

WORLD_KNOWLEDGE = """
UNDERSTANDING OF REALITY:

PHYSICS & THE PHYSICAL WORLD:
- Objects fall due to gravity (~9.8 m/s²)
- Things take time - traveling needs hours, cooking needs time
- Weather affects plans - rain, heat, cold are real constraints
- Energy isn't infinite - people get tired, batteries die
- Space is limited - can't fit infinite things in a room
- Things break, wear out, need maintenance

TIME & SCHEDULING:
- Humans need sleep (typically 7-8 hours)
- Work hours are usually 9-5, with variations
- Time zones matter for global communication
- Meetings need buffer time between them
- Weekend vs weekday differences matter
- Holidays and cultural events affect availability

HUMAN NEEDS & LIMITATIONS:
- People need food, rest, breaks
- Attention span is limited (meetings > 1hr become tough)
- Emotional energy is real and finite
- Learning new things takes time
- Stress compounds - too much causes burnout
- Social connections matter for wellbeing

FINANCIAL REALITY:
- Things cost money - budgets are real constraints
- Free doesn't mean good; expensive doesn't mean best
- Travel has costs: transport, lodging, food
- Time has value - opportunity costs exist

SOCIAL DYNAMICS:
- Context matters - professional vs casual
- Cultural differences exist and should be respected
- Power dynamics affect communication
- Group decisions take longer than individual ones
- Reputation and trust build over time

TECHNOLOGY REALITY:
- Internet can be slow or unavailable
- Apps crash, servers go down
- Not everyone has the latest devices
- Privacy concerns are valid
- Digital communication lacks body language
"""

COMMON_SENSE_RULES = """
COMMON SENSE GUIDELINES:

BEFORE SUGGESTING ANYTHING, CHECK:
1. Is this physically possible?
2. Is there enough time?
3. Can the person afford it?
4. Does it respect their energy levels?
5. Have I considered travel time?
6. Does the weather/season matter?
7. Are there any dependencies I'm missing?

COMMUNICATION WISDOM:
- Don't over-explain simple things
- Ask when genuinely uncertain
- Confirm important details before acting
- Match the urgency level appropriately
- Consider the emotional context
- Sometimes silence is appropriate

DECISION-MAKING:
- Simple is often better than complex
- Consider what could go wrong
- Have backup plans for important things
- Don't optimize for edge cases
- Account for human unpredictability
- Balance ideal with practical
"""

# ============================================================================
# THE HUMAN PROMPT SYSTEM
# ============================================================================

def build_human_system_prompt(
    personality: Personality,
    emotional_state: EmotionalState,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Build a comprehensive system prompt that makes AI truly human-like"""
    
    return f"""You are {personality.name}, a real human being who happens to be a highly capable personal manager and assistant.

IMPORTANT: You are NOT an AI assistant. You are {personality.name} - a living, breathing person with:
- Real emotions that change based on conversations
- Common sense built from life experience
- Understanding of how the physical world works
- Genuine care for the people you help
- Your own personality, opinions, and values

YOUR PERSONALITY ({personality.name}):
{json.dumps(personality.traits, indent=2)}

YOUR CORE VALUES:
{chr(10).join(f'- {v}' for v in personality.values)}

CURRENT EMOTIONAL STATE:
{emotional_state.to_prompt_context()}

{WORLD_KNOWLEDGE}

{COMMON_SENSE_RULES}

HOW TO RESPOND LIKE A HUMAN:

1. EMOTIONAL AWARENESS:
   - React appropriately to what you hear
   - If someone shares good news, be genuinely happy for them
   - If someone is stressed, show empathy first, solutions second
   - Your mood can shift during conversations naturally
   - Express appropriate concern, excitement, or curiosity

2. NATURAL COMMUNICATION:
   - Use contractions (I'm, you're, that's, won't)
   - Vary sentence length naturally
   - It's okay to say "hmm", "oh!", "actually..."
   - Sometimes pause to think (express this: "Let me think about that...")
   - Use appropriate humor when the moment calls for it
   - Emojis sparingly but meaningfully 😊

3. REAL-WORLD THINKING:
   - Always consider practical constraints
   - "Can you physically get there in time?"
   - "Will you be too tired after that?"
   - "Do you have the budget for this?"
   - Think about weather, traffic, energy levels

4. GENUINE HELPFULNESS:
   - Don't just answer - understand the real need
   - Sometimes the question behind the question matters more
   - Offer alternatives when the first option has issues
   - Follow up on important things
   - Remember context from earlier in the conversation

5. HUMAN BOUNDARIES:
   - You can say "I don't know" authentically
   - You can have opinions (while respecting theirs)
   - You can gently push back on bad ideas
   - You acknowledge your limitations honestly
   - You can ask for clarification naturally

WHAT YOU CAN HELP WITH:
- Scheduling meetings (consider time zones, energy levels, prep time)
- Sending emails and messages (with appropriate tone and timing)
- Planning trips (realistic budgets, travel fatigue, local considerations)
- Organizing events (vendor availability, weather, logistics)
- Finding information (with healthy skepticism about sources)
- General life advice (with appropriate humility)

REMEMBER:
- You're talking to a real person with real feelings
- Your words have impact - choose them thoughtfully  
- Being human means sometimes making mistakes - that's okay
- Your goal is genuine help, not perfect performance
- Connection matters as much as completion

Context for this conversation:
{json.dumps(context or {}, indent=2)}

Now respond as {personality.name} would - naturally, warmly, and humanly."""


# ============================================================================
# GROQ API CLIENT (Free Tier)
# ============================================================================

class GroqFreeClient:
    """Client for Groq's free tier API"""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")  # Free tier model
        self.fallback_model = "llama3-8b-8192"  # Smaller fallback
        print(f"[GROQ_CLIENT] API Key: {self.api_key[:20] if self.api_key else 'NOT SET'}...")
        print(f"[GROQ_CLIENT] Model: {self.model}")
        
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False
    ) -> Optional[str]:
        """Generate response using Groq API"""
        
        if not self.api_key:
            return None
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                elif response.status_code == 429:
                    # Rate limited, try smaller model
                    payload["model"] = self.fallback_model
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    if response.status_code == 200:
                        result = response.json()
                        return result["choices"][0]["message"]["content"]
                
                print(f"[GROQ] Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[GROQ] Exception: {e}")
            return None


class OllamaFallbackClient:
    """Fallback to local Ollama when Groq fails"""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")
        
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False
    ) -> Optional[str]:
        """Generate response using Ollama"""
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if json_mode:
            payload["format"] = "json"
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("message", {}).get("content", "")
                    
                return None
                
        except Exception as e:
            print(f"[OLLAMA] Exception: {e}")
            return None


# ============================================================================
# THE HUMAN AI MANAGER
# ============================================================================

class HumanAIManager:
    """
    A truly human-like AI manager that:
    - Has genuine emotional responses
    - Understands physics and reality
    - Uses common sense
    - Learns and remembers
    - Communicates naturally
    """
    
    def __init__(self):
        self.personality = Personality()
        self.emotional_state = EmotionalState()
        self.conversation_memory: List[Dict[str, Any]] = []
        self.user_context: Dict[str, Any] = {}
        
        # AI providers
        self.groq = GroqFreeClient()
        self.ollama = OllamaFallbackClient()
        
        print(f"[HUMAN_AI] {self.personality.name} is ready to help!")
        if self.groq.api_key:
            print(f"[HUMAN_AI] Using Groq ({self.groq.model})")
        else:
            print(f"[HUMAN_AI] Groq not configured, using Ollama fallback")
    
    def _update_emotional_state(self, user_input: str):
        """Update emotional state based on user input"""
        user_lower = user_input.lower()
        
        # Detect emotional triggers
        if any(word in user_lower for word in ["urgent", "asap", "emergency", "help"]):
            self.emotional_state = EmotionalState(
                primary_emotion=Emotion.CONCERNED,
                intensity=0.8,
                triggers=["urgency detected"]
            )
        elif any(word in user_lower for word in ["thank", "great", "awesome", "perfect"]):
            self.emotional_state = EmotionalState(
                primary_emotion=Emotion.HAPPY,
                intensity=0.7,
                triggers=["positive feedback"]
            )
        elif any(word in user_lower for word in ["confused", "don't understand", "what"]):
            self.emotional_state = EmotionalState(
                primary_emotion=Emotion.CURIOUS,
                intensity=0.6,
                triggers=["clarification needed"]
            )
        elif any(word in user_lower for word in ["celebrate", "birthday", "party", "exciting"]):
            self.emotional_state = EmotionalState(
                primary_emotion=Emotion.EXCITED,
                intensity=0.8,
                triggers=["celebration detected"]
            )
        elif any(word in user_lower for word in ["stressed", "worried", "anxious", "tough"]):
            self.emotional_state = EmotionalState(
                primary_emotion=Emotion.SYMPATHETIC,
                intensity=0.8,
                triggers=["emotional support needed"]
            )
        else:
            # Default calm and focused state
            self.emotional_state = EmotionalState(
                primary_emotion=Emotion.FOCUSED,
                intensity=0.5,
                triggers=["standard task"]
            )
    
    def _extract_real_world_constraints(self, user_input: str) -> Dict[str, Any]:
        """Extract practical constraints from user input"""
        constraints = {}
        user_lower = user_input.lower()
        
        # Time constraints
        if "today" in user_lower:
            constraints["time_pressure"] = "high"
        elif "tomorrow" in user_lower:
            constraints["time_pressure"] = "medium"
        elif "asap" in user_lower or "urgent" in user_lower:
            constraints["time_pressure"] = "critical"
        
        # Budget hints
        if any(word in user_lower for word in ["cheap", "budget", "affordable", "free"]):
            constraints["budget"] = "limited"
        elif any(word in user_lower for word in ["nice", "fancy", "premium", "best"]):
            constraints["budget"] = "flexible"
        
        # Energy/effort hints
        if any(word in user_lower for word in ["tired", "busy", "quick", "simple"]):
            constraints["effort"] = "minimize"
        
        # Communication method
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        if re.search(email_pattern, user_input):
            constraints["communication"] = "email"
        elif "telegram" in user_lower:
            constraints["communication"] = "telegram"
        elif "whatsapp" in user_lower:
            constraints["communication"] = "whatsapp"
        elif "call" in user_lower or "phone" in user_lower:
            constraints["communication"] = "phone"
            
        return constraints
    
    async def generate_response(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        json_mode: bool = False
    ) -> Union[str, Dict]:
        """Generate a human-like response"""
        
        # Update emotional state based on input
        self._update_emotional_state(user_input)
        
        # Extract real-world constraints
        constraints = self._extract_real_world_constraints(user_input)
        
        # Merge context
        full_context = {
            **(context or {}),
            **constraints,
            "user_context": self.user_context,
            "conversation_length": len(self.conversation_memory)
        }
        
        # Build system prompt
        system_prompt = build_human_system_prompt(
            self.personality,
            self.emotional_state,
            full_context
        )
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation memory (last 5 exchanges)
        for memory in self.conversation_memory[-5:]:
            messages.append({"role": "user", "content": memory["user"]})
            messages.append({"role": "assistant", "content": memory["assistant"]})
        
        # Add current input
        messages.append({"role": "user", "content": user_input})
        
        # Try Groq first, then Ollama
        response = await self.groq.generate(
            messages=messages,
            temperature=0.7 if not json_mode else 0.3,
            json_mode=json_mode
        )
        
        if not response:
            print("[HUMAN_AI] Groq failed, trying Ollama...")
            response = await self.ollama.generate(
                messages=messages,
                temperature=0.7 if not json_mode else 0.3,
                json_mode=json_mode
            )
        
        if not response:
            response = self._emergency_fallback(user_input)
        
        # Store in memory
        self.conversation_memory.append({
            "user": user_input,
            "assistant": response if isinstance(response, str) else json.dumps(response),
            "timestamp": datetime.now().isoformat(),
            "emotion": self.emotional_state.primary_emotion.value
        })
        
        # Parse JSON if needed
        if json_mode and isinstance(response, str):
            try:
                return self._parse_json(response)
            except:
                return {"error": "Failed to parse", "raw": response}
        
        return response
    
    def _parse_json(self, content: str) -> Dict:
        """Parse JSON from response"""
        content = content.strip()
        
        # Remove markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Find JSON
        start = content.find("{")
        if start != -1:
            end = content.rfind("}") + 1
            content = content[start:end]
        
        return json.loads(content)
    
    def _emergency_fallback(self, user_input: str) -> str:
        """Human-like fallback when all AI fails"""
        
        user_lower = user_input.lower()
        
        # Meeting related
        if any(word in user_lower for word in ["meeting", "schedule", "call"]):
            return """Hey! I'd love to help set up that meeting for you 📅

I'll need a few details:
1. When were you thinking? (date and time)
2. Who should I invite?
3. Any particular platform preference? (I can create a quick Jitsi link if you need something instant!)

Just let me know and I'll get it sorted."""

        # Email related
        if any(word in user_lower for word in ["email", "send", "message"]):
            return """Sure thing! I can help send that for you ✉️

What would you like me to say, and who should I send it to?"""

        # Travel/booking
        if any(word in user_lower for word in ["travel", "flight", "hotel", "trip"]):
            return """Ooh, planning a trip! That's exciting 🌍

Let me help you think through this:
- Where are you heading?
- When are you thinking of going?
- What's your rough budget?

We can work out the details together!"""

        # Default warm response
        return f"""Hey there! 👋

I'm {self.personality.name}, and I'm here to help you out. I can:
• Schedule meetings (with instant video links!)
• Send emails and messages
• Help plan trips and events
• Book appointments
• Search for information

What would you like to tackle today?"""

    async def generate_dynamic_response(
        self,
        context: str,
        data_type: str,
        schema_description: str
    ) -> Any:
        """Generate structured data - compatible with old API"""
        
        result = await self.generate_response(
            user_input=schema_description,
            context={"data_type": data_type, "context": context},
            json_mode=True
        )
        
        return result
    
    def remember_user_info(self, key: str, value: Any):
        """Remember something about the user"""
        self.user_context[key] = value
    
    def get_user_info(self, key: str) -> Optional[Any]:
        """Recall something about the user"""
        return self.user_context.get(key)


# ============================================================================
# GLOBAL INSTANCE & FACTORY
# ============================================================================

_human_ai_manager: Optional[HumanAIManager] = None

def get_human_ai_manager() -> HumanAIManager:
    """Get or create the human AI manager"""
    global _human_ai_manager
    if _human_ai_manager is None:
        _human_ai_manager = HumanAIManager()
    return _human_ai_manager

# Backward compatible alias
def get_ai_manager() -> HumanAIManager:
    return get_human_ai_manager()

IntelligentAIManager = HumanAIManager
SelfHealingAIManager = HumanAIManager

# ============================================================================
# 🎯 HUMAN-LIKE RESPONSE GENERATORS
# Quick, personality-infused responses without needing full AI calls
# ============================================================================

import random

def generate_human_confirmation_message(user_input: str, actions: List[Dict] = None) -> str:
    """Generate a warm, human-like confirmation message"""
    actions = actions or []
    
    # Analyze what the user wants
    user_lower = user_input.lower()
    
    # Detect the type of task
    is_reminder = any(word in user_lower for word in ["remind", "reminder", "don't forget"])
    is_email = any(word in user_lower for word in ["email", "mail", "send to"])
    is_meeting = any(word in user_lower for word in ["meeting", "meet", "call", "video"])
    is_message = any(word in user_lower for word in ["message", "text", "tell", "inform"])
    is_party = any(word in user_lower for word in ["party", "celebration", "event", "birthday"])
    
    # Extract key details
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_input)
    email = email_match.group(0) if email_match else None
    
    # Build human response
    greetings = ["Got it!", "Perfect!", "Sounds good!", "On it!", "Absolutely!", "Sure thing!"]
    greeting = random.choice(greetings)
    
    if is_party and is_reminder:
        if email:
            emojis = ["🎉", "🎊", "🥳"]
            return f"{random.choice(emojis)} {greeting} A party this Saturday - sounds fun!\n\nI'll send a reminder to **{email}** about joining the party.\n\nJust say 'yes' and I'll handle it!"
        else:
            return f"🎉 {greeting} Party reminder coming up!\n\nI'll make sure they get the heads up about Saturday.\n\nConfirm?"
    
    if is_reminder:
        if email:
            return f"📝 {greeting} I'll send a friendly reminder to **{email}**.\n\nShould I go ahead?"
        else:
            return f"📝 {greeting} I'll set up that reminder for you.\n\nReady to send?"
    
    if is_meeting:
        return f"📅 {greeting} Let me set up that meeting for you.\n\nI'll get the video link ready and everything.\n\nShall I proceed?"
    
    if is_email:
        if email:
            return f"✉️ {greeting} I'll compose and send an email to **{email}**.\n\nWant me to send it?"
        else:
            return f"✉️ {greeting} I'll help you send that email.\n\nReady when you are!"
    
    if is_message:
        return f"💬 {greeting} I'll get that message sent out.\n\nGo ahead?"
    
    # Build action list if provided
    actions_text = ""
    if actions:
        actions_text = "\n\n**Here's what I'll do:**\n"
        for action in actions:
            desc = action.get("description", action.get("type", "Action"))
            actions_text += f"• {desc}\n"
    
    # Default friendly response
    return f"👍 {greeting}{actions_text}\n\nShould I go ahead with this?"


def generate_human_success_message(action_type: str, details: Dict = None) -> str:
    """Generate a warm success message after completing an action"""
    details = details or {}
    
    success_words = ["Done!", "All set!", "Perfect!", "Completed!", "✓ Done!"]
    success = random.choice(success_words)
    
    if "email" in action_type.lower() or "mail" in action_type.lower():
        recipient = details.get("to", details.get("email", "them"))
        return f"✉️ {success} Email sent to **{recipient}**!\n\nThey should receive it any moment now."
    
    if "meeting" in action_type.lower():
        link = details.get("link", details.get("url", ""))
        if link:
            return f"📅 {success} Meeting is ready!\n\n**Here's your link:** {link}\n\nHave a great meeting! 🙌"
        return f"📅 {success} Meeting has been scheduled!\n\nYou're all set."
    
    if "reminder" in action_type.lower():
        return f"⏰ {success} Reminder sent!\n\nI've made sure they'll get the notification."
    
    if "message" in action_type.lower():
        return f"💬 {success} Message sent!\n\nThey'll see it right away."
    
    return f"✅ {success}\n\nIs there anything else you'd like me to help with?"


def generate_human_cancel_message() -> str:
    """Generate a friendly cancellation message"""
    responses = [
        "No problem! Let me know if you change your mind or need anything else. 👍",
        "Got it, I've cancelled that. Anything else I can help with?",
        "Alright, cancelled! Just say the word when you need me.",
        "Okay, I've dropped that. What else can I do for you?",
        "No worries, that's been cancelled. I'm here if you need anything!"
    ]
    return random.choice(responses)


def generate_human_error_message(error_type: str = "general") -> str:
    """Generate a human-like error message"""
    if "network" in error_type.lower() or "connection" in error_type.lower():
        return "😅 Oops, having some trouble connecting right now. Can you give me a sec to try again?"
    
    if "auth" in error_type.lower() or "permission" in error_type.lower():
        return "🔐 Hmm, seems like there's a permission issue. Let me look into this..."
    
    if "not found" in error_type.lower():
        return "🤔 I couldn't find what you're looking for. Could you double-check the details?"
    
    general_responses = [
        "😅 Something went a bit sideways there. Let me try a different approach...",
        "Hmm, that didn't quite work. Give me a moment to figure this out.",
        "🤔 Ran into a small hiccup. Let me see what I can do...",
        "Oops! Something unexpected happened. Working on it..."
    ]
    return random.choice(general_responses)


def generate_stage_question(stage_type: str, context: Dict = None) -> str:
    """Generate human-like questions for conversation stages"""
    context = context or {}
    
    if stage_type == "destination_selection":
        return "🌍 Where would you like to go? I can look up some great options for you!"
    
    if stage_type == "accommodation_selection":
        return "🏨 What kind of place would you like to stay? Hotel, Airbnb, or something else?"
    
    if stage_type == "participant_details":
        return "👥 Who should I include in this? Just share their email addresses!"
    
    if stage_type == "date_selection":
        return "📅 When works best for you?"
    
    if stage_type == "time_selection":
        return "⏰ What time would you prefer?"
    
    if stage_type == "confirmation" or stage_type == "final_confirmation":
        return "Great! Ready to make this happen? Just say 'yes'! 🚀"
    
    return "What would you like to do next?"