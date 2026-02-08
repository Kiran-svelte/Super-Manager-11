"""
Browser Automation for Service Signup
=====================================
Uses Playwright for headless browser automation to:
- Sign up for online services
- Handle form filling
- Work with CAPTCHAs (via 2Captcha)
- Extract API keys from dashboards

Works on Render.com with proper configuration.
"""

import os
import re
import uuid
import asyncio
import random
import string
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

# Playwright for browser automation
try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Internal imports
from .gmail_reader import get_gmail_reader, VerificationCode
from .service_signup import CaptchaSolver, SignupResult, ServiceRegistry

# Environment variables
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


def generate_password(length: int = 16) -> str:
    """Generate a secure random password"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))


def generate_username(base_email: str) -> str:
    """Generate a username from email"""
    name = base_email.split('@')[0]
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{name}{suffix}"


@dataclass
class SignupContext:
    """Context for a signup operation"""
    user_id: str
    email: str
    password: str
    username: str
    service_name: str
    captcha_solver: CaptchaSolver


class BrowserAutomation:
    """
    Handles browser-based service signups.
    
    Uses Playwright with headless Chrome.
    Configured to work on Render.com.
    """
    
    def __init__(self, email: str, password: str = None):
        self.email = email
        self.password = password or generate_password()
        self.username = generate_username(email)
        self.captcha_solver = CaptchaSolver(CAPTCHA_API_KEY)
        self.gmail_reader = get_gmail_reader()
        
    async def signup_groq(self, user_id: str) -> SignupResult:
        """
        Sign up for Groq API.
        
        Groq allows email-based signup:
        1. Go to console.groq.com
        2. Click sign up with email
        3. Enter email
        4. Get magic link via email
        5. Click link to complete signup
        6. Get API key from dashboard
        """
        
        if not PLAYWRIGHT_AVAILABLE:
            return SignupResult(
                success=False,
                service_name="groq",
                message="Browser automation not available. Install playwright."
            )
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu'
                    ]
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                try:
                    # Go to Groq console
                    print("[GROQ] Navigating to console.groq.com...")
                    await page.goto("https://console.groq.com/login", wait_until='networkidle', timeout=30000)
                    
                    # Look for email signup option
                    await asyncio.sleep(2)
                    
                    # Click "Continue with email" or similar
                    email_btn = await page.query_selector('text=email')
                    if email_btn:
                        await email_btn.click()
                        await asyncio.sleep(1)
                    
                    # Enter email
                    email_input = await page.query_selector('input[type="email"], input[name="email"]')
                    if email_input:
                        await email_input.fill(self.email)
                        await asyncio.sleep(0.5)
                    
                    # Click continue/submit
                    submit_btn = await page.query_selector('button[type="submit"], button:has-text("Continue"), button:has-text("Sign")')
                    if submit_btn:
                        await submit_btn.click()
                        await asyncio.sleep(3)
                    
                    # Wait for magic link email
                    print("[GROQ] Waiting for magic link email...")
                    verification = await self.gmail_reader.wait_for_verification_email(
                        from_service="groq",
                        timeout_seconds=120
                    )
                    
                    if not verification or not verification.link:
                        return SignupResult(
                            success=False,
                            service_name="groq",
                            message="No verification email received. Please check your spam folder."
                        )
                    
                    # Click the magic link
                    print(f"[GROQ] Opening magic link...")
                    await page.goto(verification.link, wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(5)
                    
                    # Navigate to API keys page
                    await page.goto("https://console.groq.com/keys", wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(2)
                    
                    # Click create API key button
                    create_btn = await page.query_selector('button:has-text("Create"), button:has-text("New"), button:has-text("Generate")')
                    if create_btn:
                        await create_btn.click()
                        await asyncio.sleep(2)
                    
                    # Look for the API key in the page
                    api_key = await self._extract_api_key_from_page(page, "gsk_")
                    
                    if api_key:
                        return SignupResult(
                            success=True,
                            service_name="groq",
                            message="Successfully signed up for Groq!",
                            account_email=self.email,
                            api_key=api_key
                        )
                    else:
                        return SignupResult(
                            success=True,
                            service_name="groq", 
                            message="Signed up for Groq. Please get your API key manually from console.groq.com/keys",
                            account_email=self.email,
                            needs_verification=True
                        )
                        
                finally:
                    await browser.close()
                    
        except Exception as e:
            return SignupResult(
                success=False,
                service_name="groq",
                message=f"Signup failed: {str(e)}"
            )
    
    async def signup_together(self, user_id: str) -> SignupResult:
        """
        Sign up for Together AI.
        
        Together AI has a simple email signup:
        1. Go to api.together.ai
        2. Sign up with email
        3. Verify email
        4. Get API key
        """
        
        if not PLAYWRIGHT_AVAILABLE:
            return SignupResult(
                success=False,
                service_name="together",
                message="Browser automation not available"
            )
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                )
                
                page = await browser.new_page()
                
                try:
                    # Go to Together signup
                    print("[TOGETHER] Navigating to signup...")
                    await page.goto("https://api.together.ai/signin", wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(2)
                    
                    # Look for signup option
                    signup_link = await page.query_selector('a:has-text("Sign up"), text=Sign up')
                    if signup_link:
                        await signup_link.click()
                        await asyncio.sleep(2)
                    
                    # Enter email
                    email_input = await page.query_selector('input[type="email"], input[name="email"]')
                    if email_input:
                        await email_input.fill(self.email)
                    
                    # Enter password if there's a password field
                    password_input = await page.query_selector('input[type="password"], input[name="password"]')
                    if password_input:
                        await password_input.fill(self.password)
                    
                    # Submit
                    submit_btn = await page.query_selector('button[type="submit"]')
                    if submit_btn:
                        await submit_btn.click()
                        await asyncio.sleep(3)
                    
                    # Wait for verification email
                    verification = await self.gmail_reader.wait_for_verification_email(
                        from_service="together",
                        timeout_seconds=120
                    )
                    
                    if verification and verification.link:
                        await page.goto(verification.link, wait_until='networkidle', timeout=30000)
                        await asyncio.sleep(3)
                    
                    # Go to API keys
                    await page.goto("https://api.together.ai/settings/api-keys", wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(2)
                    
                    # Extract API key
                    api_key = await self._extract_api_key_from_page(page)
                    
                    return SignupResult(
                        success=True,
                        service_name="together",
                        message="Signed up for Together AI!",
                        account_email=self.email,
                        api_key=api_key
                    )
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            return SignupResult(
                success=False,
                service_name="together",
                message=f"Signup failed: {str(e)}"
            )
    
    async def signup_huggingface(self, user_id: str) -> SignupResult:
        """
        Sign up for HuggingFace.
        
        HuggingFace has email signup:
        1. Go to huggingface.co/join
        2. Enter email, username, password
        3. Verify email
        4. Get API token from settings
        """
        
        if not PLAYWRIGHT_AVAILABLE:
            return SignupResult(
                success=False,
                service_name="huggingface",
                message="Browser automation not available"
            )
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                page = await browser.new_page()
                
                try:
                    print("[HUGGINGFACE] Navigating to signup...")
                    await page.goto("https://huggingface.co/join", wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(2)
                    
                    # Fill signup form
                    email_input = await page.query_selector('input[name="email"], input[type="email"]')
                    if email_input:
                        await email_input.fill(self.email)
                    
                    username_input = await page.query_selector('input[name="username"]')
                    if username_input:
                        await username_input.fill(self.username)
                    
                    password_input = await page.query_selector('input[name="password"], input[type="password"]')
                    if password_input:
                        await password_input.fill(self.password)
                    
                    # Handle CAPTCHA if present
                    captcha_key = await self._get_recaptcha_key(page)
                    if captcha_key:
                        solved = await self.captcha_solver.solve_recaptcha(
                            captcha_key, 
                            "https://huggingface.co/join"
                        )
                        if solved:
                            # Inject the solution
                            await page.evaluate(f'document.getElementById("g-recaptcha-response").value = "{solved}"')
                    
                    # Submit
                    submit_btn = await page.query_selector('button[type="submit"]')
                    if submit_btn:
                        await submit_btn.click()
                        await asyncio.sleep(5)
                    
                    # Wait for verification email
                    verification = await self.gmail_reader.wait_for_verification_email(
                        from_service="huggingface",
                        timeout_seconds=120
                    )
                    
                    if verification and verification.link:
                        await page.goto(verification.link, wait_until='networkidle', timeout=30000)
                        await asyncio.sleep(3)
                    
                    # Get API token
                    await page.goto("https://huggingface.co/settings/tokens", wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(2)
                    
                    # Click new token button
                    new_token_btn = await page.query_selector('button:has-text("New token"), button:has-text("Create")')
                    if new_token_btn:
                        await new_token_btn.click()
                        await asyncio.sleep(2)
                    
                    api_key = await self._extract_api_key_from_page(page, "hf_")
                    
                    return SignupResult(
                        success=True,
                        service_name="huggingface",
                        message="Signed up for HuggingFace!",
                        account_email=self.email,
                        account_username=self.username,
                        api_key=api_key
                    )
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            return SignupResult(
                success=False,
                service_name="huggingface",
                message=f"Signup failed: {str(e)}"
            )
    
    async def signup_openrouter(self, user_id: str) -> SignupResult:
        """
        Sign up for OpenRouter.
        
        OpenRouter aggregates multiple LLM APIs:
        1. Go to openrouter.ai
        2. Sign up with email
        3. Verify email
        4. Get API key
        """
        
        if not PLAYWRIGHT_AVAILABLE:
            return SignupResult(
                success=False,
                service_name="openrouter",
                message="Browser automation not available"
            )
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
                page = await browser.new_page()
                
                try:
                    print("[OPENROUTER] Navigating to signup...")
                    await page.goto("https://openrouter.ai/auth/signup", wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(2)
                    
                    # Fill form
                    email_input = await page.query_selector('input[type="email"]')
                    if email_input:
                        await email_input.fill(self.email)
                    
                    password_input = await page.query_selector('input[type="password"]')
                    if password_input:
                        await password_input.fill(self.password)
                    
                    # Submit
                    submit_btn = await page.query_selector('button[type="submit"]')
                    if submit_btn:
                        await submit_btn.click()
                        await asyncio.sleep(5)
                    
                    # Wait for verification
                    verification = await self.gmail_reader.wait_for_verification_email(
                        from_service="openrouter",
                        timeout_seconds=120
                    )
                    
                    if verification and verification.link:
                        await page.goto(verification.link, wait_until='networkidle')
                        await asyncio.sleep(3)
                    
                    # Get API key
                    await page.goto("https://openrouter.ai/keys", wait_until='networkidle')
                    await asyncio.sleep(2)
                    
                    api_key = await self._extract_api_key_from_page(page, "sk-or-")
                    
                    return SignupResult(
                        success=True,
                        service_name="openrouter",
                        message="Signed up for OpenRouter!",
                        account_email=self.email,
                        api_key=api_key
                    )
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            return SignupResult(
                success=False,
                service_name="openrouter",
                message=f"Signup failed: {str(e)}"
            )
    
    async def _get_recaptcha_key(self, page: Page) -> Optional[str]:
        """Extract reCAPTCHA site key from page"""
        try:
            # Look for reCAPTCHA iframe or div
            recaptcha = await page.query_selector('.g-recaptcha, [data-sitekey]')
            if recaptcha:
                return await recaptcha.get_attribute('data-sitekey')
        except:
            pass
        return None
    
    async def _extract_api_key_from_page(self, page: Page, prefix: str = "") -> Optional[str]:
        """Extract API key from the current page"""
        try:
            # Get page content
            content = await page.content()
            
            # Common patterns for API keys
            patterns = [
                r'(sk-[a-zA-Z0-9]{20,})',
                r'(gsk_[a-zA-Z0-9]{20,})',
                r'(hf_[a-zA-Z0-9]{20,})',
                r'(sk-or-[a-zA-Z0-9]{20,})',
                r'([a-zA-Z0-9]{32,})',  # Generic long alphanumeric
            ]
            
            if prefix:
                patterns.insert(0, rf'({re.escape(prefix)}[a-zA-Z0-9_\-]{{20,}})')
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    key = match.group(1)
                    # Validate it's not just random page content
                    if len(key) >= 20 and not key.startswith('http'):
                        return key
            
            # Try clicking any "copy" or "show" buttons
            copy_btn = await page.query_selector('button:has-text("Copy"), button:has-text("Show")')
            if copy_btn:
                await copy_btn.click()
                await asyncio.sleep(1)
                
                # Check clipboard or visible text
                content = await page.content()
                for pattern in patterns:
                    match = re.search(pattern, content)
                    if match:
                        return match.group(1)
            
        except Exception as e:
            print(f"[BROWSER] Error extracting API key: {e}")
        
        return None


class ServiceSignupAutomation:
    """
    Main class for automated service signup.
    
    Orchestrates the signup process:
    1. Check if service is blocked
    2. Get AI identity credentials
    3. Run browser automation
    4. Wait for verification emails
    5. Store credentials securely
    """
    
    SIGNUP_METHODS = {
        "groq": "signup_groq",
        "together": "signup_together",
        "huggingface": "signup_huggingface",
        "openrouter": "signup_openrouter",
    }
    
    def __init__(self, email: str, password: str = None):
        self.browser = BrowserAutomation(email, password)
    
    async def signup(self, service_name: str, user_id: str) -> SignupResult:
        """
        Sign up for a service.
        
        Returns:
            SignupResult with status and credentials
        """
        
        # Check if blocked
        blocked, reason = ServiceRegistry.is_blocked(service_name)
        if blocked:
            return SignupResult(
                success=False,
                service_name=service_name,
                blocked_reason=reason,
                message=f"Service blocked: {reason}"
            )
        
        # Get signup method
        method_name = self.SIGNUP_METHODS.get(service_name.lower())
        if not method_name:
            return SignupResult(
                success=False,
                service_name=service_name,
                message=f"No automated signup available for {service_name}. Please sign up manually."
            )
        
        # Run signup
        method = getattr(self.browser, method_name)
        return await method(user_id)
    
    @classmethod
    def get_available_services(cls) -> list:
        """Get list of services with automated signup"""
        return list(cls.SIGNUP_METHODS.keys())
