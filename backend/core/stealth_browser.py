"""
Stealth Browser - Anti-Detection Browser Automation
===================================================
v6 NEW - Browser automation with anti-detection capabilities.

Launch Priority:
1. Camoufox (AsyncCamoufox) - Best anti-detect Firefox
2. playwright-stealth - Stealth plugin for Playwright
3. Plain Playwright - Fallback (current behavior in primitives.py)

CAPTCHA Handling:
- Detects CAPTCHAs (reCAPTCHA, hCaptcha, Cloudflare, Turnstile)
- Triggers human_fallback instead of trying to solve
- Logs encounter for analysis

Registers 3 tools with ToolRegistry:
- stealth_browse(url) - SAFE
- stealth_fill_form(url, fields, submit) - RISKY
- stealth_screenshot(url) - SAFE
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .primitives import PrimitiveResult

logger = logging.getLogger(__name__)


# =============================================================================
# BROWSER LAUNCH MODES
# =============================================================================

@dataclass
class BrowserConfig:
    """Configuration for browser launch"""
    headless: bool = True
    timeout: int = 20000
    user_agent: Optional[str] = None
    viewport: Dict[str, int] = None
    
    def __post_init__(self):
        if self.viewport is None:
            self.viewport = {"width": 1920, "height": 1080}


class StealthBrowser:
    """
    Browser automation with anti-detection capabilities.
    
    Automatically selects the best available browser:
    1. Camoufox - Most stealthy (if installed)
    2. Playwright with stealth plugin - Good stealth (if installed)
    3. Plain Playwright - Fallback
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self.browser = None
        self.context = None
        self.page = None
        self.mode = None  # "camoufox", "playwright-stealth", or "playwright"
    
    async def launch(self) -> None:
        """
        Launch browser with best available stealth mode.
        
        Raises:
            Exception: If no browser is available
        """
        # Try Camoufox first
        try:
            from camoufox.async_api import AsyncCamoufox
            
            self.browser = await AsyncCamoufox(
                headless=self.config.headless,
                humanize=True,  # Enable humanization features
            )
            self.context = await self.browser.new_context(
                viewport=self.config.viewport,
                user_agent=self.config.user_agent,
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.config.timeout)
            self.mode = "camoufox"
            logger.info("Launched Camoufox browser (best stealth)")
            return
        
        except ImportError:
            logger.info("Camoufox not available, trying playwright-stealth")
        except Exception as e:
            logger.warning(f"Camoufox launch failed: {e}, trying playwright-stealth")
        
        # Try Playwright with stealth plugin
        try:
            from playwright.async_api import async_playwright
            from playwright_stealth import stealth_async
            
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.config.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            self.context = await self.browser.new_context(
                viewport=self.config.viewport,
                user_agent=self.config.user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.config.timeout)
            
            # Apply stealth plugin
            await stealth_async(self.page)
            
            self.mode = "playwright-stealth"
            logger.info("Launched Playwright with stealth plugin")
            return
        
        except ImportError:
            logger.info("playwright-stealth not available, trying plain Playwright")
        except Exception as e:
            logger.warning(f"Playwright-stealth launch failed: {e}, trying plain Playwright")
        
        # Fallback to plain Playwright
        try:
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.config.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )
            self.context = await self.browser.new_context(
                viewport=self.config.viewport,
                user_agent=self.config.user_agent,
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.config.timeout)
            self.mode = "playwright"
            logger.info("Launched plain Playwright (minimal stealth)")
            return
        
        except ImportError:
            raise Exception("Playwright not installed. Install with: pip install playwright && playwright install chromium")
        except Exception as e:
            raise Exception(f"Failed to launch any browser: {e}")
    
    async def detect_captcha(self) -> Dict[str, Any]:
        """
        Detect if current page has a CAPTCHA challenge.
        
        Returns:
            Dict with detected=bool, type=str, selectors=list
        """
        if not self.page:
            return {"detected": False, "type": None, "selectors": []}
        
        detected_captchas = []
        
        try:
            # reCAPTCHA v2
            recaptcha_frame = await self.page.query_selector('iframe[src*="recaptcha"]')
            if recaptcha_frame:
                detected_captchas.append({
                    "type": "recaptcha_v2",
                    "selector": 'iframe[src*="recaptcha"]',
                })
            
            # reCAPTCHA v3 (invisible)
            recaptcha_badge = await self.page.query_selector('.grecaptcha-badge')
            if recaptcha_badge:
                detected_captchas.append({
                    "type": "recaptcha_v3",
                    "selector": ".grecaptcha-badge",
                })
            
            # hCaptcha
            hcaptcha_frame = await self.page.query_selector('iframe[src*="hcaptcha"]')
            if hcaptcha_frame:
                detected_captchas.append({
                    "type": "hcaptcha",
                    "selector": 'iframe[src*="hcaptcha"]',
                })
            
            # Cloudflare challenge
            cloudflare_challenge = await self.page.query_selector('#challenge-form, .cf-challenge-running, .cf-browser-verification')
            if cloudflare_challenge:
                detected_captchas.append({
                    "type": "cloudflare",
                    "selector": "#challenge-form",
                })
            
            # Cloudflare Turnstile
            turnstile_frame = await self.page.query_selector('iframe[src*="challenges.cloudflare.com"]')
            if turnstile_frame:
                detected_captchas.append({
                    "type": "cloudflare_turnstile",
                    "selector": 'iframe[src*="challenges.cloudflare.com"]',
                })
            
            # Check for generic CAPTCHA indicators in page text
            page_text = await self.page.content()
            captcha_keywords = ["captcha", "bot check", "verify you are human", "prove you are not a robot"]
            page_text_lower = page_text.lower()
            
            for keyword in captcha_keywords:
                if keyword in page_text_lower:
                    detected_captchas.append({
                        "type": "generic_captcha",
                        "selector": "page text contains: " + keyword,
                    })
                    break
            
            if detected_captchas:
                logger.info(f"CAPTCHA detected: {detected_captchas}")
                return {
                    "detected": True,
                    "captchas": detected_captchas,
                    "count": len(detected_captchas),
                }
            
            return {"detected": False, "captchas": [], "count": 0}
        
        except Exception as e:
            logger.error(f"Error detecting CAPTCHA: {e}")
            return {"detected": False, "captchas": [], "count": 0, "error": str(e)}
    
    async def navigate(self, url: str) -> str:
        """
        Navigate to a URL and extract text content.
        
        Args:
            url: URL to visit
        
        Returns:
            Page text content
        
        Raises:
            Exception: If navigation fails
        """
        if not self.page:
            await self.launch()
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        await self.page.goto(url, wait_until="domcontentloaded")
        await self.page.wait_for_timeout(2000)
        
        # Check for CAPTCHA
        captcha_result = await self.detect_captcha()
        if captcha_result["detected"]:
            captcha_types = [c["type"] for c in captcha_result["captchas"]]
            raise Exception(f"CAPTCHA detected: {', '.join(captcha_types)}")
        
        # Extract text content
        text = await self.page.evaluate("""() => {
            const remove = document.querySelectorAll('script, style, nav, footer, header, aside, .ad, .advertisement, .sidebar');
            remove.forEach(el => el.remove());
            return document.body.innerText;
        }""")
        
        return text
    
    async def fill_form(self, url: str, fields: Dict[str, str], submit: bool = False) -> Dict[str, Any]:
        """
        Navigate to URL and fill form fields.
        
        Args:
            url: Page URL with form
            fields: Dict of CSS selector -> value to fill
            submit: Whether to click submit button
        
        Returns:
            Dict with filled/failed fields and current URL
        
        Raises:
            Exception: If navigation fails or CAPTCHA detected
        """
        if not self.page:
            await self.launch()
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        await self.page.goto(url, wait_until="domcontentloaded")
        await self.page.wait_for_timeout(2000)
        
        # Check for CAPTCHA before filling
        captcha_result = await self.detect_captcha()
        if captcha_result["detected"]:
            captcha_types = [c["type"] for c in captcha_result["captchas"]]
            raise Exception(f"CAPTCHA detected before form fill: {', '.join(captcha_types)}")
        
        filled = []
        failed = []
        
        for selector, value in fields.items():
            try:
                element = await self.page.query_selector(selector)
                if element:
                    tag = await element.evaluate("el => el.tagName.toLowerCase()")
                    input_type = await element.evaluate("el => el.type || ''")
                    
                    if tag == "select":
                        await element.select_option(value=value)
                    elif input_type in ("checkbox", "radio"):
                        if value.lower() in ("true", "yes", "1", "checked"):
                            await element.check()
                        else:
                            await element.uncheck()
                    else:
                        await element.fill(value)
                    
                    filled.append(f"{selector} = {value}")
                else:
                    failed.append(f"{selector} (not found)")
            except Exception as e:
                failed.append(f"{selector} ({str(e)[:50]})")
        
        # Optionally submit
        if submit and filled:
            try:
                submit_btn = await self.page.query_selector('button[type="submit"], input[type="submit"], .submit-btn, #submit')
                if submit_btn:
                    await submit_btn.click()
                    await self.page.wait_for_timeout(3000)
                    filled.append("Form submitted")
                else:
                    failed.append("Submit button not found")
            except Exception as e:
                failed.append(f"Submit failed: {str(e)[:50]}")
        
        # Check for CAPTCHA after filling
        captcha_result = await self.detect_captcha()
        if captcha_result["detected"]:
            captcha_types = [c["type"] for c in captcha_result["captchas"]]
            raise Exception(f"CAPTCHA detected after form fill: {', '.join(captcha_types)}")
        
        current_url = self.page.url
        
        return {
            "filled": filled,
            "failed": failed,
            "current_url": current_url,
            "submitted": submit and "Form submitted" in filled,
        }
    
    async def screenshot(self) -> bytes:
        """
        Take a screenshot of the current page.
        
        Returns:
            Screenshot bytes (PNG format)
        
        Raises:
            Exception: If no page is loaded
        """
        if not self.page:
            raise Exception("No page loaded. Call navigate() first.")
        
        screenshot_bytes = await self.page.screenshot()
        return screenshot_bytes
    
    async def close(self):
        """Close the browser and cleanup resources."""
        if self.page:
            await self.page.close()
            self.page = None
        
        if self.context:
            await self.context.close()
            self.context = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        logger.info(f"Closed {self.mode} browser")


# =============================================================================
# TOOL FUNCTIONS (Registered with ToolRegistry)
# =============================================================================

async def stealth_browse(url: str) -> PrimitiveResult:
    """
    Visit a URL using stealth browser and extract text content.
    SAFE - Auto-execute.
    
    Args:
        url: URL to visit
    
    Returns:
        PrimitiveResult with page text
    """
    browser = StealthBrowser()
    
    try:
        text = await browser.navigate(url)
        
        # Truncate to avoid massive context
        max_chars = 6000
        truncated = len(text) > max_chars
        if truncated:
            text = text[:max_chars]
        
        output = f"Content from {url} (stealth mode: {browser.mode}):\n\n{text}"
        if truncated:
            output += "\n\n... (truncated, full page has more content)"
        
        return PrimitiveResult(
            success=True,
            output=output,
            data={
                "url": url,
                "content_length": len(text),
                "truncated": truncated,
                "stealth_mode": browser.mode,
            },
        )
    
    except Exception as e:
        error_msg = str(e)
        
        # If CAPTCHA detected, return special result (not an error)
        if "CAPTCHA detected" in error_msg:
            return PrimitiveResult(
                success=False,
                output=f"CAPTCHA detected on {url}: {error_msg}\n\nThis requires human intervention. Consider using human_fallback.",
                error="captcha_detected",
                data={"url": url, "captcha_info": error_msg},
            )
        
        return PrimitiveResult(
            success=False,
            output=f"Failed to browse {url}: {error_msg}",
            error=error_msg,
        )
    
    finally:
        await browser.close()


async def stealth_fill_form(url: str, fields: Dict[str, str], submit: bool = False) -> PrimitiveResult:
    """
    Navigate to URL and fill form fields using stealth browser.
    RISKY - Requires user confirmation.
    
    Args:
        url: Page URL with form
        fields: Dict of CSS selector -> value
        submit: Whether to submit form
    
    Returns:
        PrimitiveResult with form filling status
    """
    browser = StealthBrowser()
    
    try:
        result = await browser.fill_form(url, fields, submit)
        
        output_lines = [f"Form filling on {url} (stealth mode: {browser.mode}):"]
        if result["filled"]:
            output_lines.append(f"Filled: {', '.join(result['filled'])}")
        if result["failed"]:
            output_lines.append(f"Failed: {', '.join(result['failed'])}")
        output_lines.append(f"Current page: {result['current_url']}")
        
        return PrimitiveResult(
            success=len(result["filled"]) > 0,
            output="\n".join(output_lines),
            data={
                "url": url,
                "stealth_mode": browser.mode,
                **result,
            },
        )
    
    except Exception as e:
        error_msg = str(e)
        
        # If CAPTCHA detected, return special result
        if "CAPTCHA detected" in error_msg:
            return PrimitiveResult(
                success=False,
                output=f"CAPTCHA detected on {url}: {error_msg}\n\nThis requires human intervention. Consider using human_fallback.",
                error="captcha_detected",
                data={"url": url, "fields": fields, "captcha_info": error_msg},
            )
        
        return PrimitiveResult(
            success=False,
            output=f"Form filling failed: {error_msg}",
            error=error_msg,
        )
    
    finally:
        await browser.close()


async def stealth_screenshot(url: str) -> PrimitiveResult:
    """
    Take a screenshot of a URL using stealth browser.
    SAFE - Auto-execute.
    
    Args:
        url: URL to screenshot
    
    Returns:
        PrimitiveResult with screenshot data (base64)
    """
    browser = StealthBrowser()
    
    try:
        await browser.navigate(url)
        screenshot_bytes = await browser.screenshot()
        
        # Convert to base64 for transmission
        import base64
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        return PrimitiveResult(
            success=True,
            output=f"Screenshot captured from {url} (stealth mode: {browser.mode})",
            data={
                "url": url,
                "screenshot_base64": screenshot_b64,
                "screenshot_size": len(screenshot_bytes),
                "stealth_mode": browser.mode,
            },
        )
    
    except Exception as e:
        error_msg = str(e)
        
        if "CAPTCHA detected" in error_msg:
            return PrimitiveResult(
                success=False,
                output=f"CAPTCHA detected on {url}: {error_msg}",
                error="captcha_detected",
                data={"url": url, "captcha_info": error_msg},
            )
        
        return PrimitiveResult(
            success=False,
            output=f"Screenshot failed: {error_msg}",
            error=error_msg,
        )
    
    finally:
        await browser.close()


# =============================================================================
# TOOL REGISTRATION
# =============================================================================

def register_stealth_tools():
    """
    Register stealth browser tools with ToolRegistry.
    Should be called on application startup.
    """
    try:
        from .tool_registry import get_tool_registry, ToolDef
        
        registry = get_tool_registry()
        
        # stealth_browse
        registry.register(ToolDef(
            name="stealth_browse",
            description="Visit a URL using anti-detection browser and extract text content",
            parameters={
                "url": {"type": "string", "description": "URL to visit"},
            },
            risk_level="safe",
            source="stealth",
            handler=stealth_browse,
        ))
        
        # stealth_fill_form
        registry.register(ToolDef(
            name="stealth_fill_form",
            description="Fill form fields on a webpage using stealth browser",
            parameters={
                "url": {"type": "string", "description": "Page URL with form"},
                "fields": {"type": "object", "description": "Dict of CSS selector -> value"},
                "submit": {"type": "boolean", "description": "Whether to submit form (default False)"},
            },
            risk_level="risky",
            source="stealth",
            handler=stealth_fill_form,
        ))
        
        # stealth_screenshot
        registry.register(ToolDef(
            name="stealth_screenshot",
            description="Take a screenshot of a URL using stealth browser",
            parameters={
                "url": {"type": "string", "description": "URL to screenshot"},
            },
            risk_level="safe",
            source="stealth",
            handler=stealth_screenshot,
        ))
        
        logger.info("Registered 3 stealth browser tools")
    
    except Exception as e:
        logger.error(f"Failed to register stealth tools: {e}")
