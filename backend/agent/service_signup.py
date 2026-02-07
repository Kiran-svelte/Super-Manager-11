"""
Service Signup Automation
==========================
Automates signing up for online services using the AI's identity.

Uses Playwright for browser automation:
- Fills out signup forms
- Handles email verification
- Solves CAPTCHAs via 2Captcha
- Stores API keys securely
"""

import os
import re
import uuid
import json
import asyncio
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

# 2Captcha API
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "3061822dc7a19a701597941c6f00cd85")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://hpqmcdygbjdmvxfmvucf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


@dataclass
class SignupResult:
    """Result of a service signup attempt"""
    success: bool
    service_name: str
    message: str
    account_email: Optional[str] = None
    account_username: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    additional_data: Dict = field(default_factory=dict)
    needs_verification: bool = False
    needs_user_input: str = None  # What input is needed from user
    blocked_reason: str = None


class CaptchaSolver:
    """Solves CAPTCHAs using 2Captcha API"""
    
    API_URL = "http://2captcha.com"
    
    def __init__(self, api_key: str = CAPTCHA_API_KEY):
        self.api_key = api_key
    
    async def solve_recaptcha(
        self, 
        site_key: str, 
        page_url: str,
        timeout: int = 120
    ) -> Optional[str]:
        """Solve reCAPTCHA v2 and return the token"""
        
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Submit the captcha
                submit_url = f"{self.API_URL}/in.php"
                response = await client.get(submit_url, params={
                    "key": self.api_key,
                    "method": "userrecaptcha",
                    "googlekey": site_key,
                    "pageurl": page_url,
                    "json": 1
                })
                
                data = response.json()
                if data.get("status") != 1:
                    print(f"[CAPTCHA ERROR] Submit failed: {data}")
                    return None
                
                request_id = data.get("request")
                
                # Poll for result
                result_url = f"{self.API_URL}/res.php"
                for _ in range(timeout // 5):
                    await asyncio.sleep(5)
                    
                    response = await client.get(result_url, params={
                        "key": self.api_key,
                        "action": "get",
                        "id": request_id,
                        "json": 1
                    })
                    
                    data = response.json()
                    if data.get("status") == 1:
                        return data.get("request")
                    elif data.get("request") == "CAPCHA_NOT_READY":
                        continue
                    else:
                        print(f"[CAPTCHA ERROR] Solve failed: {data}")
                        return None
                
        except Exception as e:
            print(f"[CAPTCHA ERROR] {str(e)}")
        
        return None
    
    async def solve_hcaptcha(
        self, 
        site_key: str, 
        page_url: str,
        timeout: int = 120
    ) -> Optional[str]:
        """Solve hCaptcha and return the token"""
        
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Submit the captcha
                submit_url = f"{self.API_URL}/in.php"
                response = await client.get(submit_url, params={
                    "key": self.api_key,
                    "method": "hcaptcha",
                    "sitekey": site_key,
                    "pageurl": page_url,
                    "json": 1
                })
                
                data = response.json()
                if data.get("status") != 1:
                    return None
                
                request_id = data.get("request")
                
                # Poll for result
                result_url = f"{self.API_URL}/res.php"
                for _ in range(timeout // 5):
                    await asyncio.sleep(5)
                    
                    response = await client.get(result_url, params={
                        "key": self.api_key,
                        "action": "get",
                        "id": request_id,
                        "json": 1
                    })
                    
                    data = response.json()
                    if data.get("status") == 1:
                        return data.get("request")
                    elif data.get("request") == "CAPCHA_NOT_READY":
                        continue
                    else:
                        return None
                
        except Exception as e:
            print(f"[CAPTCHA ERROR] {str(e)}")
        
        return None


class ServiceSignup:
    """
    Handles automated service signup.
    
    For cloud deployment, we use API-based signup where possible.
    For services requiring browser automation, we queue the task.
    """
    
    # Services that can be signed up via API
    API_SIGNUP_SERVICES = {
        "github": {
            "signup_url": "https://github.com/join",
            "api_signup": False,  # Needs browser
            "capabilities": ["code_repos", "gists", "actions"]
        },
        "sendgrid": {
            "signup_url": "https://signup.sendgrid.com/",
            "api_signup": False,
            "capabilities": ["email_sending"]
        },
        "openai": {
            "signup_url": "https://platform.openai.com/signup",
            "api_signup": False,
            "capabilities": ["llm_api", "embeddings", "images"]
        },
        "anthropic": {
            "signup_url": "https://console.anthropic.com/",
            "api_signup": False,
            "capabilities": ["llm_api"]
        },
        "replicate": {
            "signup_url": "https://replicate.com/signin",
            "api_signup": False,
            "capabilities": ["ml_models", "image_gen"]
        },
        "huggingface": {
            "signup_url": "https://huggingface.co/join",
            "api_signup": False,
            "capabilities": ["ml_models", "datasets"]
        },
        "cloudflare": {
            "signup_url": "https://dash.cloudflare.com/sign-up",
            "api_signup": False,
            "capabilities": ["cdn", "dns", "workers"]
        }
    }
    
    def __init__(self, identity_email: str, identity_password: str):
        self.email = identity_email
        self.password = identity_password  # For accounts, not Gmail password
        self.captcha_solver = CaptchaSolver()
        
        # Supabase
        try:
            from supabase import create_client
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except:
            self.supabase = None
    
    def generate_password(self, length: int = 16) -> str:
        """Generate a secure random password"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def signup_via_api(
        self,
        service_name: str,
        user_id: str
    ) -> SignupResult:
        """
        Attempt to sign up for a service via their API.
        Most services don't allow this, so we return guidance.
        """
        
        service_info = self.API_SIGNUP_SERVICES.get(service_name.lower())
        
        if not service_info:
            return SignupResult(
                success=False,
                service_name=service_name,
                message=f"Service '{service_name}' not in our registry. You may need to sign up manually."
            )
        
        # Most services require browser signup
        if not service_info.get("api_signup", False):
            return SignupResult(
                success=False,
                service_name=service_name,
                message=f"Please sign up at {service_info['signup_url']} using your AI email: {self.email}",
                needs_verification=True,
                additional_data={
                    "signup_url": service_info["signup_url"],
                    "email_to_use": self.email,
                    "capabilities": service_info.get("capabilities", [])
                }
            )
        
        return SignupResult(
            success=False,
            service_name=service_name,
            message="Direct API signup not implemented for this service."
        )
    
    async def store_service_account(
        self,
        user_id: str,
        ai_identity_id: str,
        service_name: str,
        api_key: str,
        api_secret: str = None,
        account_email: str = None,
        account_username: str = None
    ) -> bool:
        """Store a service account after manual signup"""
        
        if not self.supabase:
            return False
        
        try:
            # Encrypt credentials
            from .identity import EncryptionManager
            encryption = EncryptionManager()
            
            encrypted_key = encryption.encrypt(api_key) if api_key else None
            encrypted_secret = encryption.encrypt(api_secret) if api_secret else None
            
            self.supabase.table("ai_service_accounts").upsert({
                "id": str(uuid.uuid4()),
                "ai_identity_id": ai_identity_id,
                "user_id": user_id,
                "service_name": service_name,
                "account_email": account_email or self.email,
                "account_username": account_username,
                "encrypted_api_key": encrypted_key,
                "encrypted_api_secret": encrypted_secret,
                "status": "active",
                "email_verified": True,
                "last_used_at": datetime.now().isoformat()
            }).execute()
            
            return True
            
        except Exception as e:
            print(f"[SERVICE ACCOUNT ERROR] {str(e)}")
            return False
    
    async def get_service_credentials(
        self,
        user_id: str,
        service_name: str
    ) -> Optional[Dict]:
        """Get stored credentials for a service"""
        
        if not self.supabase:
            return None
        
        try:
            result = self.supabase.table("ai_service_accounts")\
                .select("*")\
                .eq("user_id", user_id)\
                .ilike("service_name", f"%{service_name}%")\
                .eq("status", "active")\
                .single()\
                .execute()
            
            if result.data:
                from .identity import EncryptionManager
                encryption = EncryptionManager()
                
                data = result.data
                return {
                    "service_name": data["service_name"],
                    "account_email": data["account_email"],
                    "account_username": data["account_username"],
                    "api_key": encryption.decrypt(data["encrypted_api_key"]) if data.get("encrypted_api_key") else None,
                    "api_secret": encryption.decrypt(data["encrypted_api_secret"]) if data.get("encrypted_api_secret") else None
                }
                
        except Exception as e:
            print(f"[GET CREDENTIALS ERROR] {str(e)}")
        
        return None
    
    async def list_service_accounts(self, user_id: str) -> List[Dict]:
        """List all service accounts for a user"""
        
        if not self.supabase:
            return []
        
        try:
            result = self.supabase.table("ai_service_accounts")\
                .select("service_name, account_email, status, last_used_at, capabilities")\
                .eq("user_id", user_id)\
                .execute()
            
            return result.data if result.data else []
            
        except:
            return []


class ServiceRegistry:
    """
    Registry of known services and their capabilities.
    Helps the AI decide which services to use for tasks.
    """
    
    SERVICES = {
        # Email
        "sendgrid": {
            "category": "email",
            "free_tier": True,
            "monthly_limit": 100,
            "capabilities": ["send_email", "templates", "analytics"],
            "requires": ["email_verification"]
        },
        "mailgun": {
            "category": "email",
            "free_tier": True,
            "monthly_limit": 5000,
            "capabilities": ["send_email", "receive_email", "templates"],
            "requires": ["email_verification", "domain_verification"]
        },
        
        # AI/LLM
        "groq": {
            "category": "ai",
            "free_tier": True,
            "capabilities": ["llm_api", "fast_inference"],
            "requires": ["email_verification"]
        },
        "together": {
            "category": "ai",
            "free_tier": True,
            "monthly_limit_credits": 25,
            "capabilities": ["llm_api", "image_gen", "embeddings"],
            "requires": ["email_verification"]
        },
        "openrouter": {
            "category": "ai",
            "free_tier": True,
            "capabilities": ["llm_api", "multiple_models"],
            "requires": ["email_verification"]
        },
        "huggingface": {
            "category": "ai",
            "free_tier": True,
            "capabilities": ["ml_models", "datasets", "spaces"],
            "requires": ["email_verification"]
        },
        
        # Storage
        "cloudflare_r2": {
            "category": "storage",
            "free_tier": True,
            "monthly_limit_gb": 10,
            "capabilities": ["object_storage", "cdn"],
            "requires": ["email_verification"]
        },
        "supabase": {
            "category": "database",
            "free_tier": True,
            "capabilities": ["postgres", "auth", "storage", "realtime"],
            "requires": ["email_verification"]
        },
        
        # Communication (mostly blocked)
        "telegram_bot": {
            "category": "messaging",
            "free_tier": True,
            "capabilities": ["send_messages", "receive_messages", "bots"],
            "requires": ["email_verification"],  # Bot creation doesn't need phone
            "blocked": False
        },
        "discord_bot": {
            "category": "messaging",
            "free_tier": True,
            "capabilities": ["send_messages", "bots"],
            "requires": ["email_verification"],
            "blocked": False
        },
        "twilio": {
            "category": "sms",
            "free_tier": True,
            "trial_credits": 15,
            "capabilities": ["send_sms", "voice", "whatsapp"],
            "requires": ["phone_verification"],
            "blocked": True,
            "blocked_reason": "Requires phone verification"
        },
        
        # Code & Hosting
        "github": {
            "category": "code",
            "free_tier": True,
            "capabilities": ["repos", "actions", "pages"],
            "requires": ["email_verification"]
        },
        "vercel": {
            "category": "hosting",
            "free_tier": True,
            "capabilities": ["deploy", "serverless", "edge"],
            "requires": ["email_verification", "github_oauth"]
        },
        "railway": {
            "category": "hosting",
            "free_tier": True,
            "monthly_limit_hours": 500,
            "capabilities": ["deploy", "databases"],
            "requires": ["email_verification", "github_oauth"]
        },
        
        # Payment (all blocked)
        "stripe": {
            "category": "payment",
            "blocked": True,
            "blocked_reason": "Requires business verification and bank account"
        },
        "razorpay": {
            "category": "payment",
            "blocked": True,
            "blocked_reason": "Requires PAN and bank account verification"
        }
    }
    
    @classmethod
    def get_service_for_task(cls, task_type: str) -> List[str]:
        """Get recommended services for a task type"""
        
        task_to_category = {
            "send_email": ["email"],
            "ai_chat": ["ai"],
            "store_data": ["database", "storage"],
            "send_message": ["messaging"],
            "deploy_code": ["hosting"],
            "manage_code": ["code"]
        }
        
        categories = task_to_category.get(task_type, [])
        
        services = []
        for name, info in cls.SERVICES.items():
            if info.get("category") in categories and not info.get("blocked", False):
                services.append(name)
        
        return services
    
    @classmethod
    def get_service_info(cls, service_name: str) -> Optional[Dict]:
        """Get info about a specific service"""
        return cls.SERVICES.get(service_name.lower())
    
    @classmethod
    def is_blocked(cls, service_name: str) -> Tuple[bool, Optional[str]]:
        """Check if a service is blocked"""
        service = cls.SERVICES.get(service_name.lower())
        if service:
            return service.get("blocked", False), service.get("blocked_reason")
        return False, None


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_service_signup: Optional[ServiceSignup] = None

def get_service_signup(email: str, password: str) -> ServiceSignup:
    """Get Service Signup instance"""
    global _service_signup
    if _service_signup is None or _service_signup.email != email:
        _service_signup = ServiceSignup(email, password)
    return _service_signup
