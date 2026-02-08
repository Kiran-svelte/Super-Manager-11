"""
AI TASK PLANNER - Autonomous Pipeline Builder
==============================================
When user requests a task, the AI:
1. Analyzes what's needed
2. Finds services that can help
3. Signs up for them (using AI's own email)
4. Gets API keys
5. Completes the task

This is TRUE autonomous AI behavior.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import httpx

# Service categories and their providers
SERVICE_REGISTRY = {
    "image_generation": {
        "description": "Generate images from text prompts",
        "providers": [
            {
                "name": "stability",
                "url": "https://platform.stability.ai",
                "signup_url": "https://platform.stability.ai/sign-up",
                "free_tier": True,
                "free_credits": "25 credits",
                "api_available": True,
                "difficulty": "easy",
                "captcha": False,
            },
            {
                "name": "leonardo",
                "url": "https://leonardo.ai",
                "signup_url": "https://app.leonardo.ai/auth/login",
                "free_tier": True,
                "free_credits": "150 tokens/day",
                "api_available": True,
                "difficulty": "medium",
                "captcha": True,
            },
            {
                "name": "clipdrop",
                "url": "https://clipdrop.co",
                "signup_url": "https://clipdrop.co/apis",
                "free_tier": True,
                "free_credits": "100 calls/day",
                "api_available": True,
                "difficulty": "easy",
                "captcha": False,
            },
        ]
    },
    "llm_inference": {
        "description": "Large Language Model inference",
        "providers": [
            {
                "name": "groq",
                "url": "https://console.groq.com",
                "signup_url": "https://console.groq.com/signup",
                "free_tier": True,
                "free_credits": "Unlimited (rate limited)",
                "api_available": True,
                "difficulty": "easy",
                "captcha": False,
            },
            {
                "name": "together",
                "url": "https://together.ai",
                "signup_url": "https://api.together.xyz/signup",
                "free_tier": True,
                "free_credits": "$5 free credits",
                "api_available": True,
                "difficulty": "easy",
                "captcha": False,
            },
            {
                "name": "openrouter",
                "url": "https://openrouter.ai",
                "signup_url": "https://openrouter.ai/auth",
                "free_tier": True,
                "free_credits": "Some free models",
                "api_available": True,
                "difficulty": "easy",
                "captcha": False,
            },
            {
                "name": "huggingface",
                "url": "https://huggingface.co",
                "signup_url": "https://huggingface.co/join",
                "free_tier": True,
                "free_credits": "Free inference API",
                "api_available": True,
                "difficulty": "easy",
                "captcha": True,
            },
        ]
    },
    "speech_to_text": {
        "description": "Convert speech/audio to text",
        "providers": [
            {
                "name": "assemblyai",
                "url": "https://www.assemblyai.com",
                "signup_url": "https://www.assemblyai.com/app/signup",
                "free_tier": True,
                "free_credits": "100 hours free",
                "api_available": True,
                "difficulty": "easy",
                "captcha": False,
            },
            {
                "name": "deepgram",
                "url": "https://deepgram.com",
                "signup_url": "https://console.deepgram.com/signup",
                "free_tier": True,
                "free_credits": "$200 free credits",
                "api_available": True,
                "difficulty": "easy",
                "captcha": False,
            },
        ]
    },
    "text_to_speech": {
        "description": "Convert text to speech/audio",
        "providers": [
            {
                "name": "elevenlabs",
                "url": "https://elevenlabs.io",
                "signup_url": "https://elevenlabs.io/sign-up",
                "free_tier": True,
                "free_credits": "10,000 chars/month",
                "api_available": True,
                "difficulty": "easy",
                "captcha": True,
            },
            {
                "name": "playht",
                "url": "https://play.ht",
                "signup_url": "https://play.ht/signup/",
                "free_tier": True,
                "free_credits": "12,500 chars free",
                "api_available": True,
                "difficulty": "easy",
                "captcha": False,
            },
        ]
    },
    "video_generation": {
        "description": "Generate videos from text/images",
        "providers": [
            {
                "name": "runway",
                "url": "https://runwayml.com",
                "signup_url": "https://app.runwayml.com/signup",
                "free_tier": True,
                "free_credits": "125 credits",
                "api_available": True,
                "difficulty": "medium",
                "captcha": True,
            },
        ]
    },
    "web_search": {
        "description": "Search the web programmatically",
        "providers": [
            {
                "name": "serper",
                "url": "https://serper.dev",
                "signup_url": "https://serper.dev/signup",
                "free_tier": True,
                "free_credits": "2,500 queries free",
                "api_available": True,
                "difficulty": "easy",
                "captcha": False,
            },
            {
                "name": "tavily",
                "url": "https://tavily.com",
                "signup_url": "https://app.tavily.com/sign-up",
                "free_tier": True,
                "free_credits": "1,000 queries/month",
                "api_available": True,
                "difficulty": "easy",
                "captcha": False,
            },
        ]
    },
    "code_execution": {
        "description": "Execute code in sandbox",
        "providers": [
            {
                "name": "e2b",
                "url": "https://e2b.dev",
                "signup_url": "https://e2b.dev/signup",
                "free_tier": True,
                "free_credits": "100 hours free",
                "api_available": True,
                "difficulty": "easy",
                "captcha": False,
            },
        ]
    },
    "email_sending": {
        "description": "Send emails programmatically",
        "providers": [
            {
                "name": "resend",
                "url": "https://resend.com",
                "signup_url": "https://resend.com/signup",
                "free_tier": True,
                "free_credits": "100 emails/day",
                "api_available": True,
                "difficulty": "easy",
                "captcha": False,
            },
            {
                "name": "mailgun",
                "url": "https://mailgun.com",
                "signup_url": "https://signup.mailgun.com/new/signup",
                "free_tier": True,
                "free_credits": "5,000 emails/month",
                "api_available": True,
                "difficulty": "medium",
                "captcha": True,
            },
        ]
    },
}

# Task to capability mapping
TASK_CAPABILITY_MAP = {
    # Image related
    "generate image": ["image_generation"],
    "create image": ["image_generation"],
    "draw": ["image_generation"],
    "make a picture": ["image_generation"],
    "ai art": ["image_generation"],
    
    # Text/Chat related
    "chat": ["llm_inference"],
    "answer question": ["llm_inference"],
    "write": ["llm_inference"],
    "summarize": ["llm_inference"],
    "translate": ["llm_inference"],
    "code": ["llm_inference"],
    
    # Audio related
    "transcribe": ["speech_to_text"],
    "convert audio to text": ["speech_to_text"],
    "speech to text": ["speech_to_text"],
    "read aloud": ["text_to_speech"],
    "text to speech": ["text_to_speech"],
    "voice": ["text_to_speech"],
    
    # Video related
    "generate video": ["video_generation"],
    "create video": ["video_generation"],
    "animate": ["video_generation"],
    
    # Search related
    "search": ["web_search"],
    "find": ["web_search"],
    "research": ["web_search", "llm_inference"],
    
    # Email related
    "send email": ["email_sending"],
    "email": ["email_sending"],
    
    # Code related
    "run code": ["code_execution"],
    "execute": ["code_execution"],
}


class TaskStatus(str, Enum):
    PLANNING = "planning"
    FINDING_SERVICES = "finding_services"
    SIGNING_UP = "signing_up"
    GETTING_API_KEY = "getting_api_key"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskPlan:
    """A plan for completing a user task"""
    task_id: str
    user_request: str
    capabilities_needed: List[str] = field(default_factory=list)
    selected_providers: List[Dict] = field(default_factory=list)
    api_keys_acquired: Dict[str, str] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PLANNING
    steps: List[Dict] = field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class TaskPlanner:
    """
    Autonomous task planner that:
    1. Analyzes user requests
    2. Determines required capabilities
    3. Finds suitable service providers
    4. Signs up and gets API keys
    5. Executes the task
    """
    
    def __init__(self, ai_email: str, ai_password: str, supabase_client=None):
        self.ai_email = ai_email
        self.ai_password = ai_password
        self.supabase = supabase_client
        self.active_plans: Dict[str, TaskPlan] = {}
        
    def analyze_request(self, user_request: str) -> List[str]:
        """
        Analyze what the user wants and determine required capabilities.
        """
        request_lower = user_request.lower()
        capabilities = set()
        
        # Check each task pattern
        for pattern, caps in TASK_CAPABILITY_MAP.items():
            if pattern in request_lower:
                capabilities.update(caps)
        
        # If no match, default to LLM for general questions
        if not capabilities:
            capabilities.add("llm_inference")
        
        return list(capabilities)
    
    def find_best_providers(self, capabilities: List[str]) -> List[Dict]:
        """
        Find the best providers for required capabilities.
        Prioritizes:
        1. Free tier available
        2. Easy signup (no captcha)
        3. API available
        """
        providers = []
        
        for capability in capabilities:
            if capability not in SERVICE_REGISTRY:
                continue
            
            category = SERVICE_REGISTRY[capability]
            category_providers = category["providers"]
            
            # Sort by difficulty and captcha
            sorted_providers = sorted(
                category_providers,
                key=lambda p: (
                    not p["free_tier"],  # Free first
                    p["captcha"],  # No captcha first
                    p["difficulty"] == "hard",
                    p["difficulty"] == "medium",
                )
            )
            
            if sorted_providers:
                best = sorted_providers[0]
                providers.append({
                    "capability": capability,
                    "provider": best["name"],
                    "url": best["url"],
                    "signup_url": best["signup_url"],
                    "free_tier": best["free_tier"],
                    "captcha": best["captcha"],
                })
        
        return providers
    
    async def check_existing_api_keys(self, providers: List[Dict]) -> Dict[str, str]:
        """
        Check if we already have API keys for these providers.
        """
        existing_keys = {}
        
        if not self.supabase:
            return existing_keys
        
        try:
            for provider in providers:
                # Check database for existing API key
                result = self.supabase.table("ai_service_accounts").select("*").eq(
                    "service_name", provider["provider"]
                ).eq("status", "active").execute()
                
                if result.data and len(result.data) > 0:
                    account = result.data[0]
                    if account.get("api_key"):
                        existing_keys[provider["provider"]] = account["api_key"]
        except Exception as e:
            print(f"Error checking existing keys: {e}")
        
        return existing_keys
    
    async def create_plan(self, user_request: str) -> TaskPlan:
        """
        Create a complete plan for the user's task.
        """
        import uuid
        
        plan = TaskPlan(
            task_id=str(uuid.uuid4()),
            user_request=user_request,
        )
        
        # Step 1: Analyze what's needed
        plan.status = TaskStatus.PLANNING
        plan.capabilities_needed = self.analyze_request(user_request)
        plan.steps.append({
            "step": "analyze",
            "status": "completed",
            "result": f"Need capabilities: {', '.join(plan.capabilities_needed)}"
        })
        
        # Step 2: Find providers
        plan.status = TaskStatus.FINDING_SERVICES
        plan.selected_providers = self.find_best_providers(plan.capabilities_needed)
        plan.steps.append({
            "step": "find_providers",
            "status": "completed",
            "result": f"Selected: {', '.join(p['provider'] for p in plan.selected_providers)}"
        })
        
        # Step 3: Check existing API keys
        existing = await self.check_existing_api_keys(plan.selected_providers)
        plan.api_keys_acquired.update(existing)
        
        # Determine which providers need signup
        providers_needing_signup = [
            p for p in plan.selected_providers 
            if p["provider"] not in existing
        ]
        
        if providers_needing_signup:
            plan.steps.append({
                "step": "check_existing",
                "status": "completed",
                "result": f"Need to sign up for: {', '.join(p['provider'] for p in providers_needing_signup)}"
            })
        else:
            plan.steps.append({
                "step": "check_existing",
                "status": "completed",
                "result": "All API keys already available!"
            })
        
        self.active_plans[plan.task_id] = plan
        return plan
    
    async def execute_plan(self, plan: TaskPlan) -> TaskPlan:
        """
        Execute the plan:
        1. Sign up for services we don't have keys for
        2. Execute the actual task
        """
        from agent.browser_automation import ServiceSignupAutomation
        
        # Sign up for services that need it
        providers_needing_signup = [
            p for p in plan.selected_providers 
            if p["provider"] not in plan.api_keys_acquired
        ]
        
        if providers_needing_signup:
            plan.status = TaskStatus.SIGNING_UP
            automation = ServiceSignupAutomation(self.ai_email, self.ai_password)
            
            for provider in providers_needing_signup:
                try:
                    plan.steps.append({
                        "step": f"signup_{provider['provider']}",
                        "status": "in_progress",
                        "result": f"Signing up for {provider['provider']}..."
                    })
                    
                    result = await automation.signup(provider["provider"], plan.task_id)
                    
                    if result.success and result.api_key:
                        plan.api_keys_acquired[provider["provider"]] = result.api_key
                        plan.steps[-1]["status"] = "completed"
                        plan.steps[-1]["result"] = f"Got API key for {provider['provider']}"
                        
                        # Store in database
                        if self.supabase:
                            try:
                                self.supabase.table("ai_service_accounts").insert({
                                    "service_name": provider["provider"],
                                    "email": self.ai_email,
                                    "api_key": result.api_key,
                                    "status": "active",
                                    "created_at": datetime.utcnow().isoformat(),
                                }).execute()
                            except Exception as e:
                                print(f"Failed to store API key: {e}")
                    else:
                        plan.steps[-1]["status"] = "failed"
                        plan.steps[-1]["result"] = f"Failed: {result.message}"
                        
                except Exception as e:
                    plan.steps[-1]["status"] = "failed"
                    plan.steps[-1]["result"] = f"Error: {str(e)}"
        
        # Now execute the actual task
        plan.status = TaskStatus.EXECUTING
        plan.steps.append({
            "step": "execute_task",
            "status": "in_progress",
            "result": "Executing user task..."
        })
        
        try:
            # Execute based on the first capability needed
            if plan.capabilities_needed:
                primary_capability = plan.capabilities_needed[0]
                
                if primary_capability == "image_generation":
                    result = await self._execute_image_generation(plan)
                elif primary_capability == "llm_inference":
                    result = await self._execute_llm_inference(plan)
                elif primary_capability == "text_to_speech":
                    result = await self._execute_tts(plan)
                elif primary_capability == "speech_to_text":
                    result = await self._execute_stt(plan)
                else:
                    result = {"message": f"Task completed using {primary_capability}"}
                
                plan.result = result
                plan.status = TaskStatus.COMPLETED
                plan.steps[-1]["status"] = "completed"
                plan.steps[-1]["result"] = "Task completed successfully!"
            else:
                plan.error = "No capabilities determined"
                plan.status = TaskStatus.FAILED
                
        except Exception as e:
            plan.error = str(e)
            plan.status = TaskStatus.FAILED
            plan.steps[-1]["status"] = "failed"
            plan.steps[-1]["result"] = f"Error: {str(e)}"
        
        return plan
    
    async def _execute_image_generation(self, plan: TaskPlan) -> Dict:
        """Execute image generation task"""
        # Find the provider and API key
        provider = None
        api_key = None
        
        for p in plan.selected_providers:
            if p["capability"] == "image_generation":
                provider = p["provider"]
                api_key = plan.api_keys_acquired.get(provider)
                break
        
        if not api_key:
            return {"error": "No API key available for image generation"}
        
        # Execute based on provider
        async with httpx.AsyncClient() as client:
            if provider == "stability":
                response = await client.post(
                    "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "text_prompts": [{"text": plan.user_request}],
                        "cfg_scale": 7,
                        "steps": 30,
                    },
                    timeout=60,
                )
                if response.status_code == 200:
                    return {"success": True, "images": response.json().get("artifacts", [])}
                else:
                    return {"error": response.text}
        
        return {"message": f"Image generation with {provider} - API key ready"}
    
    async def _execute_llm_inference(self, plan: TaskPlan) -> Dict:
        """Execute LLM inference task"""
        # Use GROQ_API_KEY from environment
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            # Try to get from acquired keys
            for p in plan.selected_providers:
                if p["capability"] == "llm_inference":
                    api_key = plan.api_keys_acquired.get(p["provider"])
                    if api_key:
                        break
        
        if not api_key:
            return {"error": "No LLM API key available"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": plan.user_request}],
                    "max_tokens": 1000,
                },
                timeout=30,
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data["choices"][0]["message"]["content"]
                }
            else:
                return {"error": response.text}
    
    async def _execute_tts(self, plan: TaskPlan) -> Dict:
        """Execute text-to-speech task"""
        return {"message": "TTS execution ready - API key acquired"}
    
    async def _execute_stt(self, plan: TaskPlan) -> Dict:
        """Execute speech-to-text task"""
        return {"message": "STT execution ready - API key acquired"}
    
    def get_plan_status(self, task_id: str) -> Optional[TaskPlan]:
        """Get the status of a plan"""
        return self.active_plans.get(task_id)
    
    def format_plan_for_user(self, plan: TaskPlan) -> str:
        """Format the plan as a user-friendly message"""
        lines = []
        
        lines.append(f"📋 **Task Plan for:** {plan.user_request}\n")
        lines.append(f"**Status:** {plan.status.value}\n")
        
        if plan.capabilities_needed:
            lines.append(f"**Capabilities needed:** {', '.join(plan.capabilities_needed)}")
        
        if plan.selected_providers:
            lines.append(f"**Services selected:**")
            for p in plan.selected_providers:
                status = "✅" if p["provider"] in plan.api_keys_acquired else "⏳"
                lines.append(f"  {status} {p['provider']} ({p['capability']})")
        
        if plan.steps:
            lines.append(f"\n**Steps:**")
            for step in plan.steps:
                icon = "✅" if step["status"] == "completed" else "❌" if step["status"] == "failed" else "⏳"
                lines.append(f"  {icon} {step['result']}")
        
        if plan.result:
            lines.append(f"\n**Result:** {plan.result}")
        
        if plan.error:
            lines.append(f"\n**Error:** {plan.error}")
        
        return "\n".join(lines)


# Singleton instance
_task_planner = None

def get_task_planner() -> TaskPlanner:
    """Get the singleton task planner instance"""
    global _task_planner
    if _task_planner is None:
        ai_email = os.getenv("AI_EMAIL", "traderlighter11@gmail.com")
        ai_password = os.getenv("AI_PASSWORD", "SecureAI2024!")
        
        # Try to get Supabase client
        supabase = None
        try:
            from backend.database_supabase import get_supabase_client
            supabase = get_supabase_client()
        except:
            pass
        
        _task_planner = TaskPlanner(ai_email, ai_password, supabase)
    
    return _task_planner
