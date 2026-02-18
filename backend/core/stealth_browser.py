"""
Stealth Browser - Anti-Detect Browser Automation
==================================================
Wraps Playwright with anti-detection capabilities for accessing
sites that block standard automation (travel booking, form filling, etc.).

Launch priority:
1. Camoufox (anti-detect Firefox with fingerprint randomization)
2. Playwright + stealth plugin (basic anti-detection)
3. Plain Playwright (fallback, current behavior)

CAPTCHA handling: Detects CAPTCHAs and triggers human_fallback
instead of attempting automated solving.
"""

import os
import re
import random
import asyncio
import logging
from typing import Dict, Any, Optional, List

from .primitives import PrimitiveResult, _clean_text

logger = logging.getLogger(__name__)

# Feature detection
CAMOUFOX_AVAILABLE = False
PLAYWRIGHT_STEALTH_AVAILABLE = False
PLAYWRIGHT_AVAILABLE = False

try:
    from camoufox.async_api import AsyncCamoufox
    CAMOUFOX_AVAILABLE = True
except ImportError:
    pass

try:
    from playwright_stealth import stealth_async
    PLAYWRIGHT_STEALTH_AVAILABLE = True
except ImportError:
    pass

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


# CAPTCHA detection patterns
CAPTCHA_PATTERNS = [
    r'class="g-recaptcha"',
    r'class="h-captcha"',
    r'data-sitekey=',
    r'captcha-container',
    r'cf-turnstile',
    r'id="challenge-running"',
    r'id="challenge-form"',
    r'<iframe[^>]*recaptcha',
    r'<iframe[^>]*hcaptcha',
    r'Please verify you are a human',
    r'Verify you are human',
    r'complete the security check',
    r'Just a moment\.\.\.',  # Cloudflare challenge page
]


async def _detect_captcha(page_content: str) -> bool:
    """Check if page content contains CAPTCHA indicators"""
    for pattern in CAPTCHA_PATTERNS:
        if re.search(pattern, page_content, re.IGNORECASE):
            return True
    return False


class StealthBrowser:
    """
    Anti-detect browser with human-like behavior.
    Falls back gracefully through available implementations.
    """

    def __init__(self):
        self._browser = None
        self._context = None
        self._page = None
        self._engine = None  # "camoufox", "playwright_stealth", "playwright"

    async def launch(self):
        """Launch browser with best available anti-detection"""
        if CAMOUFOX_AVAILABLE:
            try:
                self._browser = await AsyncCamoufox(headless=True).__aenter__()
                self._page = await self._browser.new_page()
                self._engine = "camoufox"
                logger.info("[STEALTH] Launched Camoufox (anti-detect Firefox)")
                return
            except Exception as e:
                logger.warning(f"[STEALTH] Camoufox failed, falling back: {e}")

        if PLAYWRIGHT_AVAILABLE:
            pw = await async_playwright().__aenter__()
            self._browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            self._context = await self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            self._page = await self._context.new_page()

            if PLAYWRIGHT_STEALTH_AVAILABLE:
                await stealth_async(self._page)
                self._engine = "playwright_stealth"
                logger.info("[STEALTH] Launched Playwright + stealth plugin")
            else:
                self._engine = "playwright"
                logger.info("[STEALTH] Launched plain Playwright (no stealth)")
        else:
            raise RuntimeError("No browser engine available. Install playwright or camoufox.")

    async def _human_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """Add human-like random delay"""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)

    async def navigate(self, url: str) -> str:
        """Navigate to URL and return page text content"""
        if not self._page:
            await self.launch()

        await self._page.goto(url, wait_until="domcontentloaded")
        await self._human_delay(1000, 3000)

        # Check for CAPTCHA
        html = await self._page.content()
        if await _detect_captcha(html):
            logger.warning(f"[STEALTH] CAPTCHA detected on {url}")
            return f"[CAPTCHA_DETECTED] A CAPTCHA was detected on {url}. Use human_fallback to ask the user to complete this step."

        # Extract text
        text = await self._page.evaluate("""() => {
            const remove = document.querySelectorAll('script, style, nav, footer, header, aside, .ad, .advertisement, .sidebar');
            remove.forEach(el => el.remove());
            return document.body.innerText;
        }""")

        return _clean_text(text) if text else ""

    async def fill_form_fields(self, url: str, fields: Dict[str, str], submit: bool = False) -> Dict[str, Any]:
        """Navigate to URL and fill form fields with human-like behavior"""
        if not self._page:
            await self.launch()

        await self._page.goto(url, wait_until="domcontentloaded")
        await self._human_delay(1000, 2500)

        # Check for CAPTCHA
        html = await self._page.content()
        if await _detect_captcha(html):
            return {
                "success": False,
                "captcha_detected": True,
                "url": url,
                "filled": [],
                "failed": list(fields.keys()),
            }

        filled = []
        failed = []

        for selector, value in fields.items():
            try:
                element = await self._page.query_selector(selector)
                if element:
                    tag = await element.evaluate("el => el.tagName.toLowerCase()")
                    input_type = await element.evaluate("el => el.type || ''")

                    # Human-like typing delay
                    await self._human_delay(200, 800)

                    if tag == "select":
                        await element.select_option(value=value)
                    elif input_type in ("checkbox", "radio"):
                        if value.lower() in ("true", "yes", "1", "checked"):
                            await element.check()
                        else:
                            await element.uncheck()
                    else:
                        # Clear and type character by character for human-like behavior
                        await element.click()
                        await self._human_delay(100, 300)
                        await element.fill("")
                        for char in value:
                            await element.type(char, delay=random.randint(30, 150))

                    filled.append(selector)
                else:
                    failed.append(f"{selector} (not found)")
            except Exception as e:
                failed.append(f"{selector} ({str(e)[:50]})")

        # Optionally submit
        submitted = False
        if submit and filled:
            await self._human_delay(500, 1500)
            try:
                submit_btn = await self._page.query_selector(
                    'button[type="submit"], input[type="submit"], .submit-btn, #submit'
                )
                if submit_btn:
                    await submit_btn.click()
                    await self._human_delay(2000, 4000)
                    submitted = True
                else:
                    failed.append("Submit button not found")
            except Exception as e:
                failed.append(f"Submit failed: {str(e)[:50]}")

        return {
            "success": len(filled) > 0,
            "captcha_detected": False,
            "url": url,
            "current_url": self._page.url,
            "filled": filled,
            "failed": failed,
            "submitted": submitted,
        }

    async def screenshot(self) -> Optional[bytes]:
        """Take screenshot of current page"""
        if not self._page:
            return None
        try:
            return await self._page.screenshot(full_page=False)
        except Exception:
            return None

    async def close(self):
        """Close browser"""
        try:
            if self._browser:
                await self._browser.close()
        except Exception:
            pass
        self._browser = None
        self._context = None
        self._page = None
        self._engine = None

    @property
    def engine_name(self) -> str:
        return self._engine or "none"


# =============================================================================
# TOOL FUNCTIONS (registered with ToolRegistry)
# =============================================================================

async def stealth_browse(url: str) -> PrimitiveResult:
    """
    Browse a URL using anti-detect browser.
    Falls back to standard Playwright if stealth not available.
    """
    if not url:
        return PrimitiveResult(success=False, output="No URL provided.", error="missing_url")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    browser = StealthBrowser()
    try:
        await browser.launch()
        text = await browser.navigate(url)

        if not text or len(text.strip()) < 50:
            return PrimitiveResult(
                success=True,
                output=f"Page at {url} returned very little content. (Engine: {browser.engine_name})",
                data={"url": url, "engine": browser.engine_name, "content_length": len(text) if text else 0},
            )

        # Truncate for LLM context
        max_chars = 6000
        truncated = len(text) > max_chars
        if truncated:
            text = text[:max_chars]

        output = f"Content from {url} (via {browser.engine_name}):\n\n{text}"
        if truncated:
            output += "\n\n... (truncated)"

        return PrimitiveResult(
            success=True,
            output=output,
            data={"url": url, "engine": browser.engine_name, "content_length": len(text), "truncated": truncated},
        )

    except Exception as e:
        return PrimitiveResult(success=False, output=f"Stealth browse failed: {str(e)}", error=str(e))
    finally:
        await browser.close()


async def stealth_fill_form(url: str, fields: str = "", submit: bool = False) -> PrimitiveResult:
    """
    Fill form fields using anti-detect browser with human-like typing.
    Fields format: "selector1=value1,selector2=value2"
    """
    if not url:
        return PrimitiveResult(success=False, output="No URL provided.", error="missing_url")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Parse fields from string format (LLM-friendly)
    field_dict: Dict[str, str] = {}
    if fields:
        for pair in fields.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                field_dict[k.strip()] = v.strip()

    if not field_dict:
        return PrimitiveResult(success=False, output="No form fields provided.", error="missing_fields")

    browser = StealthBrowser()
    try:
        await browser.launch()
        result = await browser.fill_form_fields(url, field_dict, submit)

        if result.get("captcha_detected"):
            return PrimitiveResult(
                success=False,
                output=f"CAPTCHA detected on {url}. Use human_fallback to ask the user to complete this step manually.",
                data={"captcha_detected": True, "url": url},
                error="captcha_detected",
            )

        output_lines = [f"Form filling on {url} (via {browser.engine_name}):"]
        if result["filled"]:
            output_lines.append(f"Filled: {', '.join(result['filled'])}")
        if result["failed"]:
            output_lines.append(f"Failed: {', '.join(result['failed'])}")
        if result.get("submitted"):
            output_lines.append("Form submitted.")
        output_lines.append(f"Current page: {result.get('current_url', url)}")

        return PrimitiveResult(
            success=result["success"],
            output="\n".join(output_lines),
            data=result,
        )

    except Exception as e:
        return PrimitiveResult(success=False, output=f"Stealth form fill failed: {str(e)}", error=str(e))
    finally:
        await browser.close()


async def stealth_screenshot(url: str) -> PrimitiveResult:
    """Take a screenshot of a URL using anti-detect browser."""
    if not url:
        return PrimitiveResult(success=False, output="No URL provided.", error="missing_url")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    browser = StealthBrowser()
    try:
        await browser.launch()
        await browser.navigate(url)
        screenshot_bytes = await browser.screenshot()

        if not screenshot_bytes:
            return PrimitiveResult(
                success=False,
                output="Failed to capture screenshot.",
                error="screenshot_failed",
            )

        # Save screenshot to a temporary location
        import tempfile
        import base64

        b64_data = base64.b64encode(screenshot_bytes).decode()

        return PrimitiveResult(
            success=True,
            output=f"Screenshot captured of {url} ({len(screenshot_bytes)} bytes). Engine: {browser.engine_name}",
            data={
                "url": url,
                "engine": browser.engine_name,
                "screenshot_base64": b64_data[:100] + "...",  # truncated for context
                "screenshot_size": len(screenshot_bytes),
            },
        )

    except Exception as e:
        return PrimitiveResult(success=False, output=f"Screenshot failed: {str(e)}", error=str(e))
    finally:
        await browser.close()


def register_stealth_tools():
    """Register stealth browser tools with the ToolRegistry"""
    try:
        from .tool_registry import get_tool_registry, ToolDef

        registry = get_tool_registry()

        registry.register(ToolDef(
            name="stealth_browse",
            description="Browse a URL using anti-detect browser (bypasses basic bot detection)",
            parameters="url (str)",
            returns="Page text content (truncated to ~6000 chars)",
            risk_level="safe",
            source="stealth",
            handler=stealth_browse,
        ))

        registry.register(ToolDef(
            name="stealth_fill_form",
            description="Fill form fields using anti-detect browser with human-like typing",
            parameters='url (str), fields (str, "selector1=value1,selector2=value2"), submit (bool, default False)',
            returns="Form filling status with filled/failed fields",
            risk_level="risky",
            source="stealth",
            handler=stealth_fill_form,
        ))

        registry.register(ToolDef(
            name="stealth_screenshot",
            description="Take a screenshot of a URL using anti-detect browser",
            parameters="url (str)",
            returns="Screenshot capture confirmation with metadata",
            risk_level="safe",
            source="stealth",
            handler=stealth_screenshot,
        ))

        engines = []
        if CAMOUFOX_AVAILABLE:
            engines.append("camoufox")
        if PLAYWRIGHT_STEALTH_AVAILABLE:
            engines.append("playwright-stealth")
        if PLAYWRIGHT_AVAILABLE:
            engines.append("playwright")

        logger.info(f"[STEALTH] Registered 3 stealth browser tools. Available engines: {engines or ['none']}")

    except Exception as e:
        logger.warning(f"[STEALTH] Failed to register: {e}")
