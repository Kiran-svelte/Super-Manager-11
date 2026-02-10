"""
Autonomous Capability Acquisition System
=========================================
When the AI lacks a capability (API key), it can:
1. Identify what service provides that capability
2. Sign up for the service autonomously
3. Get and store the API key
4. Use the new capability

This makes the AI truly autonomous - it can acquire new capabilities at runtime.
"""

import os
import asyncio
import secrets
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CapabilityType(str, Enum):
    """Types of capabilities the AI might need"""
    IMAGE_GENERATION = "image_generation"
    EMAIL_SENDING = "email_sending"
    WEB_SEARCH = "web_search"
    PAYMENT_PROCESSING = "payment_processing"
    AI_CHAT = "ai_chat"
    CODE_EXECUTION = "code_execution"
    FILE_STORAGE = "file_storage"
    SMS_SENDING = "sms_sending"
    VOICE_CALL = "voice_call"
    VIDEO_GENERATION = "video_generation"


@dataclass
class ServiceInfo:
    """Information about a service that provides a capability"""
    name: str
    capability: CapabilityType
    signup_url: str
    api_key_env: str
    free_tier: bool
    signup_method: str  # 'api', 'browser', 'manual'
    requires_verification: bool
    requires_payment: bool
    api_key_location: str  # Where to find API key after signup
    notes: str = ""


@dataclass
class AcquiredCapability:
    """A capability that has been acquired"""
    capability: CapabilityType
    service_name: str
    api_key: str
    api_secret: Optional[str] = None
    acquired_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    usage_limit: Optional[int] = None


class ServiceRegistry:
    """Registry of services and their capabilities"""
    
    SERVICES: Dict[str, ServiceInfo] = {
        # ===== IMAGE GENERATION (FREE OPTIONS) =====
        "pollinations": ServiceInfo(
            name="Pollinations AI",
            capability=CapabilityType.IMAGE_GENERATION,
            signup_url="https://pollinations.ai",
            api_key_env="POLLINATIONS_API_KEY",
            free_tier=True,
            signup_method="none",  # No API key needed!
            requires_verification=False,
            requires_payment=False,
            api_key_location="No API key required",
            notes="Completely free, no signup needed. Direct URL-based image generation."
        ),
        "together_ai": ServiceInfo(
            name="Together AI",
            capability=CapabilityType.IMAGE_GENERATION,
            signup_url="https://api.together.xyz/signup",
            api_key_env="TOGETHER_API_KEY",
            free_tier=True,
            signup_method="browser",
            requires_verification=True,
            requires_payment=False,
            api_key_location="Settings > API Keys",
            notes="Free tier with FLUX model. Email verification required."
        ),
        "replicate": ServiceInfo(
            name="Replicate",
            capability=CapabilityType.IMAGE_GENERATION,
            signup_url="https://replicate.com/signin",
            api_key_env="REPLICATE_API_TOKEN",
            free_tier=True,
            signup_method="browser",
            requires_verification=True,
            requires_payment=False,
            api_key_location="Account > API Tokens",
            notes="Free credits on signup. Many models available."
        ),
        "stability_ai": ServiceInfo(
            name="Stability AI",
            capability=CapabilityType.IMAGE_GENERATION,
            signup_url="https://platform.stability.ai/",
            api_key_env="STABILITY_API_KEY",
            free_tier=True,
            signup_method="browser",
            requires_verification=True,
            requires_payment=False,
            api_key_location="Account > API Keys",
            notes="Stable Diffusion. Limited free credits."
        ),
        
        # ===== EMAIL SENDING (FREE OPTIONS) =====
        "resend": ServiceInfo(
            name="Resend",
            capability=CapabilityType.EMAIL_SENDING,
            signup_url="https://resend.com/signup",
            api_key_env="RESEND_API_KEY",
            free_tier=True,
            signup_method="browser",
            requires_verification=True,
            requires_payment=False,
            api_key_location="API Keys page",
            notes="3000 emails/month free. Modern email API."
        ),
        "sendgrid": ServiceInfo(
            name="SendGrid",
            capability=CapabilityType.EMAIL_SENDING,
            signup_url="https://signup.sendgrid.com/",
            api_key_env="SENDGRID_API_KEY",
            free_tier=True,
            signup_method="browser",
            requires_verification=True,
            requires_payment=False,
            api_key_location="Settings > API Keys",
            notes="100 emails/day free. Established provider."
        ),
        "mailgun": ServiceInfo(
            name="Mailgun",
            capability=CapabilityType.EMAIL_SENDING,
            signup_url="https://signup.mailgun.com/new/signup",
            api_key_env="MAILGUN_API_KEY",
            free_tier=True,
            signup_method="browser",
            requires_verification=True,
            requires_payment=True,  # Requires CC for verification
            api_key_location="API Security page",
            notes="Generous free tier but requires payment verification."
        ),
        
        # ===== AI/LLM (FREE OPTIONS) =====
        "groq": ServiceInfo(
            name="Groq",
            capability=CapabilityType.AI_CHAT,
            signup_url="https://console.groq.com/signup",
            api_key_env="GROQ_API_KEY",
            free_tier=True,
            signup_method="browser",
            requires_verification=True,
            requires_payment=False,
            api_key_location="API Keys section",
            notes="Very fast inference. Magic link login."
        ),
        "openrouter": ServiceInfo(
            name="OpenRouter",
            capability=CapabilityType.AI_CHAT,
            signup_url="https://openrouter.ai/auth",
            api_key_env="OPENROUTER_API_KEY",
            free_tier=True,
            signup_method="browser",
            requires_verification=False,
            requires_payment=False,
            api_key_location="Keys page",
            notes="Access to multiple LLMs with free credits."
        ),
        
        # ===== PAYMENTS (FREE TO SETUP) =====
        "razorpay": ServiceInfo(
            name="Razorpay",
            capability=CapabilityType.PAYMENT_PROCESSING,
            signup_url="https://dashboard.razorpay.com/signup",
            api_key_env="RAZORPAY_KEY_ID",
            free_tier=True,
            signup_method="browser",
            requires_verification=True,
            requires_payment=False,
            api_key_location="Settings > API Keys",
            notes="Indian payment gateway. Test mode available."
        ),
        "stripe": ServiceInfo(
            name="Stripe",
            capability=CapabilityType.PAYMENT_PROCESSING,
            signup_url="https://dashboard.stripe.com/register",
            api_key_env="STRIPE_SECRET_KEY",
            free_tier=True,
            signup_method="browser",
            requires_verification=True,
            requires_payment=False,
            api_key_location="Developers > API Keys",
            notes="Global payment gateway. Test mode available."
        ),
        
        # ===== SMS (FREE OPTIONS) =====
        "twilio": ServiceInfo(
            name="Twilio",
            capability=CapabilityType.SMS_SENDING,
            signup_url="https://www.twilio.com/try-twilio",
            api_key_env="TWILIO_AUTH_TOKEN",
            free_tier=True,
            signup_method="browser",
            requires_verification=True,
            requires_payment=False,
            api_key_location="Console > Account > API Credentials",
            notes="Free trial credits. Phone number required."
        ),
    }
    
    @classmethod
    def get_services_for_capability(cls, capability: CapabilityType) -> List[ServiceInfo]:
        """Get all services that provide a capability, sorted by ease of acquisition"""
        services = [s for s in cls.SERVICES.values() if s.capability == capability]
        
        # Sort: no-signup first, then free without payment, then others
        def sort_key(s: ServiceInfo):
            if s.signup_method == "none":
                return (0, 0, s.name)
            elif s.free_tier and not s.requires_payment:
                return (1, 0 if s.signup_method == "api" else 1, s.name)
            else:
                return (2, 1, s.name)
        
        return sorted(services, key=sort_key)
    
    @classmethod
    def find_service_by_env(cls, env_var: str) -> Optional[ServiceInfo]:
        """Find a service by its environment variable name"""
        for service in cls.SERVICES.values():
            if service.api_key_env == env_var:
                return service
        return None


class CapabilityResolver:
    """
    Resolves missing capabilities by acquiring them autonomously.
    
    Flow:
    1. Task fails due to missing capability (e.g., no image gen API)
    2. Identify what capability is needed
    3. Find best service that provides it
    4. Acquire the capability (signup, get API key)
    5. Store in environment/database
    6. Retry the task
    """
    
    # Cache of acquired capabilities (in-memory for session)
    _acquired: Dict[CapabilityType, AcquiredCapability] = {}
    
    def __init__(self, user_id: str = None, ai_identity_email: str = None):
        self.user_id = user_id
        self.ai_email = ai_identity_email
        self.registry = ServiceRegistry
        
    def check_capability(self, capability: CapabilityType) -> Tuple[bool, Optional[str]]:
        """
        Check if we have a capability.
        Returns (has_capability, api_key_or_none)
        """
        
        # Check memory cache first
        if capability in self._acquired:
            return (True, self._acquired[capability].api_key)
        
        # Check environment for known services
        services = self.registry.get_services_for_capability(capability)
        
        for service in services:
            # No-signup services are always available
            if service.signup_method == "none":
                return (True, "NO_KEY_NEEDED")
            
            # Check if we have the API key
            api_key = os.getenv(service.api_key_env)
            if api_key:
                return (True, api_key)
        
        return (False, None)
    
    async def acquire_capability(
        self, 
        capability: CapabilityType,
        preferred_service: str = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Attempt to acquire a capability.
        
        Returns: (success, message, api_key)
        """
        
        services = self.registry.get_services_for_capability(capability)
        
        if not services:
            return (False, f"No known services provide {capability.value}", None)
        
        # Try each service in order of preference
        for service in services:
            if preferred_service and service.name.lower() != preferred_service.lower():
                continue
            
            logger.info(f"Attempting to acquire {capability.value} via {service.name}")
            
            # No-signup services
            if service.signup_method == "none":
                self._acquired[capability] = AcquiredCapability(
                    capability=capability,
                    service_name=service.name,
                    api_key="NO_KEY_NEEDED"
                )
                return (True, f"✅ {service.name} is available (no signup needed)", "NO_KEY_NEEDED")
            
            # API-based signup
            if service.signup_method == "api":
                result = await self._signup_via_api(service)
                if result[0]:
                    return result
            
            # Browser-based signup (requires AI email/identity)
            if service.signup_method == "browser":
                if not self.ai_email:
                    return (
                        False, 
                        f"To sign up for {service.name}, I need an email identity. "
                        f"Please set up AI identity first, or manually sign up at: {service.signup_url}",
                        None
                    )
                
                result = await self._signup_via_browser(service)
                if result[0]:
                    return result
        
        # Could not acquire
        return (
            False,
            f"Could not automatically acquire {capability.value}. "
            f"Please sign up manually at one of these services: {[s.name for s in services]}",
            None
        )
    
    async def _signup_via_api(self, service: ServiceInfo) -> Tuple[bool, str, Optional[str]]:
        """Attempt API-based signup (rarely available)"""
        # Most services don't allow API signup, this is a placeholder
        return (False, f"{service.name} requires manual signup", None)
    
    async def _signup_via_browser(self, service: ServiceInfo) -> Tuple[bool, str, Optional[str]]:
        """
        Attempt browser-based signup using Playwright.
        This is complex and service-specific.
        """
        try:
            from ..agent.browser_automation import BrowserAutomation
            
            automation = BrowserAutomation(
                email=self.ai_email,
                password=self._generate_password()
            )
            
            # Service-specific signup methods
            signup_methods = {
                "groq": automation.signup_groq,
                "together_ai": automation.signup_together,
                "replicate": automation.signup_replicate,
                "resend": automation.signup_resend,
            }
            
            method = signup_methods.get(service.name.lower().replace(" ", "_"))
            
            if method:
                result = await method(self.user_id)
                
                if result.success and result.api_key:
                    # Store in environment
                    os.environ[service.api_key_env] = result.api_key
                    
                    # Cache in memory
                    self._acquired[service.capability] = AcquiredCapability(
                        capability=service.capability,
                        service_name=service.name,
                        api_key=result.api_key
                    )
                    
                    return (
                        True,
                        f"✅ Successfully signed up for {service.name}!",
                        result.api_key
                    )
                else:
                    return (False, result.message, None)
            else:
                return (
                    False,
                    f"Automated signup not implemented for {service.name}. "
                    f"Please sign up manually at: {service.signup_url}",
                    None
                )
                
        except ImportError:
            return (
                False,
                f"Browser automation not available. Please sign up at: {service.signup_url}",
                None
            )
        except Exception as e:
            logger.error(f"Browser signup failed for {service.name}: {e}")
            return (False, f"Signup failed: {str(e)}", None)
    
    def _generate_password(self) -> str:
        """Generate a secure password for signups"""
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(16))
    
    def get_capability_status(self) -> Dict[str, Any]:
        """Get status of all capabilities"""
        status = {}
        
        for cap in CapabilityType:
            has_it, api_key = self.check_capability(cap)
            services = self.registry.get_services_for_capability(cap)
            
            status[cap.value] = {
                "available": has_it,
                "has_api_key": api_key is not None,
                "possible_services": [
                    {
                        "name": s.name,
                        "free": s.free_tier,
                        "auto_signup": s.signup_method in ["none", "api", "browser"]
                    }
                    for s in services
                ]
            }
        
        return status


class AutonomousTaskExecutor:
    """
    Enhanced task executor that can acquire capabilities on-demand.
    
    When a task fails due to missing capability:
    1. Identify needed capability
    2. Try to acquire it
    3. Retry the task
    """
    
    # Maps task types to required capabilities
    TASK_CAPABILITIES = {
        "generate_image": CapabilityType.IMAGE_GENERATION,
        "create_logo": CapabilityType.IMAGE_GENERATION,
        "send_email": CapabilityType.EMAIL_SENDING,
        "make_payment": CapabilityType.PAYMENT_PROCESSING,
        "ai_chat": CapabilityType.AI_CHAT,
        "send_sms": CapabilityType.SMS_SENDING,
    }
    
    def __init__(self, user_id: str = None, ai_email: str = None):
        self.resolver = CapabilityResolver(user_id, ai_email)
        self.user_id = user_id
    
    async def ensure_capability(self, task_type: str) -> Tuple[bool, str]:
        """
        Ensure we have the capability for a task.
        If not, try to acquire it.
        
        Returns: (success, message)
        """
        capability = self.TASK_CAPABILITIES.get(task_type)
        
        if not capability:
            return (True, "No specific capability needed")
        
        has_it, api_key = self.resolver.check_capability(capability)
        
        if has_it:
            return (True, f"✓ {capability.value} capability available")
        
        # Try to acquire
        logger.info(f"Missing capability {capability.value} for {task_type}, attempting acquisition...")
        
        success, message, key = await self.resolver.acquire_capability(capability)
        
        return (success, message)
    
    async def execute_with_capability_resolution(
        self,
        task_type: str,
        execute_fn,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a task with automatic capability resolution.
        
        If execution fails due to missing capability, try to acquire it and retry.
        """
        
        # First, ensure capability
        has_cap, cap_message = await self.ensure_capability(task_type)
        
        if not has_cap:
            return {
                "success": False,
                "error": "capability_missing",
                "message": cap_message,
                "needs_action": "acquire_capability"
            }
        
        # Execute the task
        try:
            result = await execute_fn(*args, **kwargs)
            return result
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a missing API key error
            if any(x in error_str for x in ["api key", "unauthorized", "authentication", "not configured"]):
                # Identify and try to acquire capability
                capability = self.TASK_CAPABILITIES.get(task_type)
                
                if capability:
                    success, message, key = await self.resolver.acquire_capability(capability)
                    
                    if success:
                        # Retry with new capability
                        try:
                            result = await execute_fn(*args, **kwargs)
                            result["capability_acquired"] = True
                            return result
                        except Exception as retry_error:
                            return {
                                "success": False,
                                "error": str(retry_error),
                                "capability_acquired": True,
                                "message": "Acquired capability but task still failed"
                            }
                    else:
                        return {
                            "success": False,
                            "error": "capability_acquisition_failed",
                            "message": message
                        }
            
            # Re-raise other errors
            raise


# Convenience functions
def get_capability_status(user_id: str = None) -> Dict[str, Any]:
    """Get current capability status"""
    resolver = CapabilityResolver(user_id)
    return resolver.get_capability_status()


async def ensure_capability(
    capability: CapabilityType,
    user_id: str = None,
    ai_email: str = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Ensure a capability is available, acquiring if needed.
    
    Returns: (success, message, api_key)
    """
    resolver = CapabilityResolver(user_id, ai_email)
    has_it, key = resolver.check_capability(capability)
    
    if has_it:
        return (True, "Capability available", key)
    
    return await resolver.acquire_capability(capability)
