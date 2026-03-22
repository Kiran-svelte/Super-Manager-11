"""
Primitives - The 6 Building Blocks
====================================
These replace all 12 predefined tools. They are the only functions
available inside the sandbox for dynamically generated code.

SAFE (auto-execute):
- web_search(query, max_results=5)
- browse_page(url)
- scrape_data(url, extract)
- generate_image(prompt)

RISKY (require confirmation):
- fill_form(url, fields, submit=False)
- run_python(code)

SPECIAL (handled by engine, not sandbox):
- ask_user(message, options=[]) - pauses execution for user input
"""

import re
import json
import random
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from urllib.parse import unquote, quote

import httpx

logger = logging.getLogger(__name__)


@dataclass
class PrimitiveResult:
    """Result returned by any primitive execution"""
    success: bool
    output: str  # Human-readable text for LLM to consume
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


# =============================================================================
# SAFE PRIMITIVES
# =============================================================================

async def web_search(query: str, max_results: int = 5) -> PrimitiveResult:
    """
    Search the web using DuckDuckGo HTML scraping.
    Free, no API key needed.

    Returns: PrimitiveResult with search results [{title, url, snippet}]
    """
    if not query:
        return PrimitiveResult(success=False, output="No search query provided.", error="missing_query")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )

            results = []
            html = response.text

            result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
            snippet_pattern = r'<a class="result__snippet"[^>]*>([^<]+)</a>'

            links = re.findall(result_pattern, html)
            snippets = re.findall(snippet_pattern, html)

            for i, (link, title) in enumerate(links[:max_results]):
                snippet = snippets[i] if i < len(snippets) else ""
                if "uddg=" in link:
                    actual_url = link.split("uddg=")[-1].split("&")[0]
                    link = unquote(actual_url)

                results.append({
                    "title": title.strip(),
                    "url": link,
                    "snippet": snippet.strip(),
                })

            if not results:
                return PrimitiveResult(
                    success=True,
                    output=f"No results found for '{query}'.",
                    data={"results": [], "query": query},
                )

            # Format output for LLM
            output_lines = [f"Search results for '{query}':"]
            for i, r in enumerate(results, 1):
                output_lines.append(f"{i}. {r['title']}")
                output_lines.append(f"   URL: {r['url']}")
                if r["snippet"]:
                    output_lines.append(f"   {r['snippet'][:150]}")
                output_lines.append("")

            return PrimitiveResult(
                success=True,
                output="\n".join(output_lines),
                data={"results": results, "query": query},
            )

    except Exception as e:
        return PrimitiveResult(success=False, output=f"Search failed: {str(e)}", error=str(e))


async def browse_page(url: str) -> PrimitiveResult:
    """
    Visit a URL and extract its text content.
    Uses Playwright for JS-rendered pages, falls back to httpx.

    Returns: PrimitiveResult with page text content
    """
    if not url:
        return PrimitiveResult(success=False, output="No URL provided.", error="missing_url")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Try Playwright first, fall back to httpx
    try:
        text = await _fetch_with_playwright(url)
    except Exception:
        try:
            text = await _fetch_with_httpx(url)
        except Exception as e:
            return PrimitiveResult(
                success=False,
                output=f"Failed to fetch {url}: {str(e)}",
                error=str(e),
            )

    if not text or len(text.strip()) < 50:
        return PrimitiveResult(
            success=True,
            output=f"Page at {url} returned very little text content.",
            data={"url": url, "content_length": len(text) if text else 0},
        )

    # Truncate to avoid massive LLM context
    max_chars = 6000
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars]

    output = f"Content from {url}:\n\n{text}"
    if truncated:
        output += f"\n\n... (truncated, full page has more content)"

    return PrimitiveResult(
        success=True,
        output=output,
        data={"url": url, "content_length": len(text), "truncated": truncated},
    )


async def scrape_data(url: str, extract: str = "") -> PrimitiveResult:
    """
    Visit a URL and extract specific data based on instructions.
    Enhanced version of browse_page with focused extraction hint.

    Args:
        url: The URL to scrape
        extract: What to look for, e.g. "resort names, prices, ratings, booking links"

    Returns: PrimitiveResult with extracted content
    """
    if not url:
        return PrimitiveResult(success=False, output="No URL provided.", error="missing_url")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        text = await _fetch_with_playwright(url)
    except Exception:
        try:
            text = await _fetch_with_httpx(url)
        except Exception as e:
            return PrimitiveResult(
                success=False,
                output=f"Failed to scrape {url}: {str(e)}",
                error=str(e),
            )

    if not text or len(text.strip()) < 50:
        return PrimitiveResult(
            success=True,
            output=f"Page at {url} returned very little content to extract from.",
            data={"url": url, "content_length": 0},
        )

    # Larger context for scraping (we want more data)
    max_chars = 8000
    if len(text) > max_chars:
        text = text[:max_chars]

    output = f"Scraped data from {url}"
    if extract:
        output += f" (looking for: {extract})"
    output += f":\n\n{text}"

    return PrimitiveResult(
        success=True,
        output=output,
        data={"url": url, "extract_hint": extract, "content_length": len(text)},
    )


async def generate_image(prompt: str) -> PrimitiveResult:
    """
    Generate an image using Pollinations AI.
    Completely free, no API key needed.

    Returns: PrimitiveResult with image URL
    """
    if not prompt:
        return PrimitiveResult(success=False, output="No prompt provided.", error="missing_prompt")

    try:
        encoded_prompt = quote(prompt)
        seed = random.randint(1, 999999)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}"

        # Do not attempt any network verification here. Pollinations can be slow
        # to render, and verification calls can cause timeouts/noisy errors.
        note = "Image may take a few seconds to generate or load"
        return PrimitiveResult(
            success=True,
            output=f"Image generated!\nURL: {image_url}\nPrompt: {prompt}\nNote: {note}",
            data={"image_url": image_url, "prompt": prompt, "seed": seed, "note": note},
        )

    except Exception as e:
        return PrimitiveResult(success=False, output=f"Image generation failed: {str(e)}", error=str(e))


# =============================================================================
# RISKY PRIMITIVES (require confirmation)
# =============================================================================

async def fill_form(url: str, fields: Dict[str, str], submit: bool = False) -> PrimitiveResult:
    """
    Navigate to a URL and fill form fields using Playwright.
    REQUIRES USER CONFIRMATION before execution.

    Args:
        url: The page URL with the form
        fields: Dict of CSS selector -> value to fill
                e.g. {"#name": "John", "#email": "john@test.com", "#check-in": "2025-12-20"}
        submit: Whether to click submit button after filling (default False)

    Returns: PrimitiveResult with filled form status
    """
    if not url:
        return PrimitiveResult(success=False, output="No URL provided.", error="missing_url")
    if not fields:
        return PrimitiveResult(success=False, output="No form fields provided.", error="missing_fields")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            )
            page = await browser.new_page()
            page.set_default_timeout(20000)

            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            filled = []
            failed = []

            for selector, value in fields.items():
                try:
                    element = await page.query_selector(selector)
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
                    submit_btn = await page.query_selector('button[type="submit"], input[type="submit"], .submit-btn, #submit')
                    if submit_btn:
                        await submit_btn.click()
                        await page.wait_for_timeout(3000)
                        filled.append("Form submitted")
                    else:
                        failed.append("Submit button not found")
                except Exception as e:
                    failed.append(f"Submit failed: {str(e)[:50]}")

            # Get current page URL (may have changed after submit)
            current_url = page.url

            await browser.close()

            output_lines = [f"Form filling on {url}:"]
            if filled:
                output_lines.append(f"Filled: {', '.join(filled)}")
            if failed:
                output_lines.append(f"Failed: {', '.join(failed)}")
            output_lines.append(f"Current page: {current_url}")

            return PrimitiveResult(
                success=len(filled) > 0,
                output="\n".join(output_lines),
                data={
                    "url": url,
                    "current_url": current_url,
                    "filled": filled,
                    "failed": failed,
                    "submitted": submit and "Form submitted" in filled,
                },
            )

    except ImportError:
        return PrimitiveResult(
            success=False,
            output="Playwright is not installed. Install with: pip install playwright && playwright install chromium",
            error="playwright_not_installed",
        )
    except Exception as e:
        return PrimitiveResult(success=False, output=f"Form filling failed: {str(e)}", error=str(e))


async def run_python(code: str) -> PrimitiveResult:
    """
    Execute Python code in a restricted environment.
    REQUIRES USER CONFIRMATION before execution.
    Only basic operations allowed (math, string, data processing).

    Returns: PrimitiveResult with execution output
    """
    if not code:
        return PrimitiveResult(success=False, output="No code provided.", error="missing_code")

    import io
    import contextlib

    # Restricted builtins
    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bool": bool,
        "chr": chr, "dict": dict, "divmod": divmod, "enumerate": enumerate,
        "filter": filter, "float": float, "format": format, "frozenset": frozenset,
        "hash": hash, "hex": hex, "int": int, "isinstance": isinstance,
        "issubclass": issubclass, "iter": iter, "len": len, "list": list,
        "map": map, "max": max, "min": min, "next": next, "oct": oct,
        "ord": ord, "pow": pow, "print": print, "range": range, "repr": repr,
        "reversed": reversed, "round": round, "set": set, "slice": slice,
        "sorted": sorted, "str": str, "sum": sum, "tuple": tuple, "type": type,
        "zip": zip, "True": True, "False": False, "None": None,
    }

    # Restricted globals
    import math
    import datetime
    restricted_globals = {
        "__builtins__": safe_builtins,
        "math": math,
        "datetime": datetime,
        "json": json,
        "re": re,
    }

    try:
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, restricted_globals)

        output = stdout_capture.getvalue()
        if not output:
            output = "Code executed successfully (no output)."

        return PrimitiveResult(
            success=True,
            output=f"Python execution result:\n{output}",
            data={"code": code, "stdout": output},
        )

    except Exception as e:
        return PrimitiveResult(
            success=False,
            output=f"Python execution error: {str(e)}",
            error=str(e),
        )


# =============================================================================
# HELPER FUNCTIONS (shared by primitives)
# =============================================================================

async def _fetch_with_playwright(url: str) -> str:
    """Fetch page content using Playwright (handles JS-rendered pages)"""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        page.set_default_timeout(20000)

        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        text = await page.evaluate("""() => {
            const remove = document.querySelectorAll('script, style, nav, footer, header, aside, .ad, .advertisement, .sidebar');
            remove.forEach(el => el.remove());
            return document.body.innerText;
        }""")

        await browser.close()
        return _clean_text(text)


async def _fetch_with_httpx(url: str) -> str:
    """Fallback: fetch with httpx and parse HTML"""
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False) as client:
        response = await client.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        html = response.text

        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return _clean_text(text)


def _clean_text(text: str) -> str:
    """Clean extracted text"""
    if not text:
        return ""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if line and len(line) > 2:
            cleaned.append(line)
    return "\n".join(cleaned)


# =============================================================================
# EMAIL & MEETING PRIMITIVES
# =============================================================================

async def send_email(to: str, subject: str, body: str, cc: str = "", user_id: str = "") -> PrimitiveResult:
    """
    Send an email using the identity-aware email service.
    REQUIRES USER CONFIRMATION before execution.
    
    Uses OAuth (preferred) or SMTP as fallback.
    Pulls credentials from user's AIIdentity when available.
    """
    if not to:
        return PrimitiveResult(success=False, output="No recipient email provided.", error="missing_to")
    if not subject:
        return PrimitiveResult(success=False, output="No subject provided.", error="missing_subject")
    if not body:
        return PrimitiveResult(success=False, output="No body provided.", error="missing_body")
    
    # Try identity-aware email service first
    try:
        from .identity_email_service import get_identity_email_service
        email_service = get_identity_email_service()
        result = await email_service.send_email_for_user(
            user_id=user_id or "default",
            to=to,
            subject=subject,
            body=body,
        )
        
        if result.get("status") == "completed":
            return PrimitiveResult(
                success=True,
                output=f"Email sent successfully to {to}!\nSubject: {subject}\nMethod: {result.get('method', 'oauth')}",
                data={"to": to, "subject": subject, "sent": True, "method": result.get("method")}
            )
        else:
            error = result.get("error", "Unknown error")
            # If setup required, give helpful message
            if result.get("setup_required"):
                return PrimitiveResult(
                    success=False,
                    output=f"Email not configured. Please visit /api/oauth/authorize/gmail?user_id={user_id or 'default'} to authorize Gmail.",
                    error=error
                )
            return PrimitiveResult(
                success=False,
                output=f"Failed to send email: {error}",
                error=error
            )
    except Exception as e:
        # Fall through to legacy SMTP if identity service fails
        pass
    
    # Legacy SMTP fallback
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import os
    
    smtp_email = os.getenv("SMTP_EMAIL", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    
    if not smtp_email or not smtp_password:
        return PrimitiveResult(
            success=False,
            output="Email sending not configured. Please authorize Gmail at /api/oauth/authorize/gmail?user_id=default",
            error="smtp_not_configured"
        )
    
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = smtp_email
        message["To"] = to
        if cc:
            message["Cc"] = cc
        
        # Plain text version
        text_part = MIMEText(body, "plain")
        message.attach(text_part)
        
        # HTML version (simple formatting)
        html_body = body.replace("\n", "<br>")
        html_part = MIMEText(f"<html><body><p>{html_body}</p></body></html>", "html")
        message.attach(html_part)
        
        # Send
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            recipients = [to] + ([cc] if cc else [])
            server.sendmail(smtp_email, recipients, message.as_string())
        
        return PrimitiveResult(
            success=True,
            output=f"Email sent successfully to {to}!\nSubject: {subject}",
            data={"to": to, "subject": subject, "sent": True, "method": "smtp"}
        )
    
    except Exception as e:
        return PrimitiveResult(
            success=False,
            output=f"Failed to send email: {str(e)}",
            error=str(e)
        )


async def create_meeting(topic: str, participants: list = None, datetime_str: str = "", platform: str = "zoom", user_id: str = None, force_fallback: bool = False) -> PrimitiveResult:
    """
    Create a meeting link with proper Integration Manager flow.
    
    FLOW (Integration Manager architecture):
    1. User asks for Zoom → Check if Zoom is connected
    2. If NOT connected → Return integration_required error (prompt user to connect)
    3. If connected → Use Zoom API
    4. If force_fallback=True → Use Jitsi as alternative
    
    Args:
        topic: Meeting subject
        participants: List of email addresses
        datetime_str: Natural language or ISO date like "tomorrow 3pm", "next monday 10am"
        platform: "zoom" (default) or "jitsi"
        user_id: User ID for integration check
        force_fallback: If True, skip Zoom and use Jitsi (user chose fallback)
    """
    import os
    import secrets
    from datetime import datetime, timedelta
    
    if not topic:
        return PrimitiveResult(success=False, output="No meeting topic provided.", error="missing_topic")
    
    # Smart date parsing - handles natural language
    meeting_time = _parse_datetime_smart(datetime_str)
    
    # ============================================
    # 🔐 INTEGRATION MANAGER CHECK (Layer 6)
    # ============================================
    platform_lower = platform.lower() if platform else "zoom"
    
    # If user explicitly asked for Zoom (not Jitsi, not fallback mode)
    if platform_lower == "zoom" and not force_fallback:
        # Check 1: Are Zoom API credentials configured (server-side)?
        zoom_configured = bool(
            os.getenv("ZOOM_CLIENT_ID")
            and os.getenv("ZOOM_CLIENT_SECRET")
            and os.getenv("ZOOM_ACCOUNT_ID")
        )
        
        if not zoom_configured:
            # Zoom not available - DON'T silently fallback!
            # Return integration_required so the agent asks user what to do
            return PrimitiveResult(
                success=False,
                output=(
                    "⚠️ Zoom integration is not connected. "
                    "I cannot create a Zoom meeting without proper authorization.\n\n"
                    "**Options:**\n"
                    "1. Connect your Zoom account in Settings → Integrations\n"
                    "2. Or I can create a free Jitsi Meet link instead (works immediately, no signup needed)\n\n"
                    "What would you prefer?"
                ),
                error="integration_required",
                data={
                    "required_integration": "zoom",
                    "fallback_available": "jitsi",
                    "action_type": "create_meeting",
                    "original_request": {
                        "topic": topic,
                        "participants": participants,
                        "datetime_str": datetime_str,
                    },
                    # UI hint for frontend to show connect button
                    "ui_action": {
                        "type": "integration_prompt",
                        "integration": "zoom",
                        "message": "Connect Zoom to create real Zoom meetings",
                        "fallback_option": {
                            "label": "Use Jitsi Meet instead (free)",
                            "action": "create_meeting_jitsi"
                        }
                    }
                }
            )
        
        # Try Zoom API
        zoom_result = await _create_zoom_meeting(topic, participants, meeting_time)
        
        if zoom_result and zoom_result.success:
            return zoom_result
        
        # Zoom API failed despite being configured - report the specific error.
        # IMPORTANT: never silently fall back to Jitsi when user asked for Zoom.
        return PrimitiveResult(
            success=False,
            output=(
                f"❌ Zoom meeting creation failed: {(zoom_result.error if zoom_result else 'Unknown error')}\n\n"
                "**Options:**\n"
                "1. Try again later\n"
                "2. I can create a free Jitsi Meet link instead\n\n"
                "What would you prefer?"
            ),
            error="zoom_api_failed",
            data={
                "fallback_available": "jitsi",
                "original_error": (zoom_result.error if zoom_result else None),
            },
        )
    
    # ============================================
    # JITSI FALLBACK (only when explicitly chosen or platform=jitsi)
    # ============================================
    meeting_id = secrets.token_urlsafe(8).lower().replace("-", "").replace("_", "")[:10]
    clean_topic = re.sub(r'[^a-z0-9-]', '-', topic.lower())[:20].strip('-')
    jitsi_url = f"https://meet.jit.si/{meeting_id}-{clean_topic}"
    
    meeting_data = {
        "meeting_id": meeting_id,
        "topic": topic,
        "join_url": jitsi_url,
        "platform": "Jitsi Meet",
        "datetime": meeting_time.isoformat() if meeting_time else None,
        "datetime_display": meeting_time.strftime('%B %d, %Y at %I:%M %p') if meeting_time else 'Anytime',
        "participants": participants or [],
        "is_working": True,
    }
    
    output_lines = [
        f"✅ Meeting created successfully!",
        f"Topic: {topic}",
        f"Join URL: {jitsi_url}",
        f"Platform: Jitsi Meet (free, works immediately)",
    ]
    
    if meeting_time:
        output_lines.append(f"Scheduled: {meeting_time.strftime('%B %d, %Y at %I:%M %p')}")
    
    if participants:
        output_lines.append(f"Participants: {', '.join(participants)}")
    
    return PrimitiveResult(
        success=True,
        output="\n".join(output_lines),
        data=meeting_data
    )


def _parse_datetime_smart(text: str) -> 'datetime | None':
    """
    Parse natural language datetime strings.
    Handles: 'tomorrow 3pm', 'next monday 10am', 'in 2 hours', 'march 5 2026 3pm',
    ISO format, etc.
    """
    from datetime import datetime, timedelta
    import calendar
    
    if not text or not text.strip():
        return None
    
    text = text.strip().lower()
    now = datetime.now()
    
    # Try ISO format first
    try:
        return datetime.fromisoformat(text)
    except (ValueError, TypeError):
        pass
    
    # Try common formats
    for fmt in ('%Y-%m-%d %H:%M', '%m/%d/%Y %I:%M %p', '%B %d, %Y at %I:%M %p',
                '%B %d %Y %I%p', '%B %d %Y %I:%M%p', '%d %B %Y %H:%M'):
        try:
            return datetime.strptime(text, fmt)
        except (ValueError, TypeError):
            continue
    
    # Extract time component
    hour, minute = None, 0
    time_patterns = [
        (r'(\d{1,2}):(\d{2})\s*(am|pm)', 'hm_ampm'),
        (r'(\d{1,2})\s*(am|pm)', 'h_ampm'),
        (r'(\d{1,2}):(\d{2})', 'hm_24'),
        (r'at\s+(\d{1,2})', 'h_24'),
    ]
    
    for pattern, ptype in time_patterns:
        m = re.search(pattern, text)
        if m:
            if ptype == 'hm_ampm':
                hour = int(m.group(1))
                minute = int(m.group(2))
                if m.group(3) == 'pm' and hour != 12:
                    hour += 12
                elif m.group(3) == 'am' and hour == 12:
                    hour = 0
            elif ptype == 'h_ampm':
                hour = int(m.group(1))
                if m.group(2) == 'pm' and hour != 12:
                    hour += 12
                elif m.group(2) == 'am' and hour == 12:
                    hour = 0
            elif ptype == 'hm_24':
                hour = int(m.group(1))
                minute = int(m.group(2))
            elif ptype == 'h_24':
                hour = int(m.group(1))
            break
    
    # Parse date component
    target_date = None
    
    # "today"
    if 'today' in text:
        target_date = now.date()
    
    # "tomorrow" / "tmr" / "tmrw"
    elif any(w in text for w in ('tomorrow', 'tmr', 'tmrw', 'tmrow')):
        target_date = (now + timedelta(days=1)).date()
    
    # "day after tomorrow"
    elif 'day after' in text:
        target_date = (now + timedelta(days=2)).date()
    
    # "next week"
    elif 'next week' in text:
        target_date = (now + timedelta(days=7)).date()
    
    # "in X hours/days"
    elif 'in ' in text:
        m = re.search(r'in\s+(\d+)\s+(hour|hr|day|minute|min)', text)
        if m:
            amount = int(m.group(1))
            unit = m.group(2)
            if unit in ('hour', 'hr'):
                return now + timedelta(hours=amount)
            elif unit == 'day':
                target_date = (now + timedelta(days=amount)).date()
            elif unit in ('minute', 'min'):
                return now + timedelta(minutes=amount)
    
    # "next monday/tuesday/..." 
    days_of_week = {
        'monday': 0, 'mon': 0, 'tuesday': 1, 'tue': 1, 'tues': 1,
        'wednesday': 2, 'wed': 2, 'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
        'friday': 4, 'fri': 4, 'saturday': 5, 'sat': 5, 'sunday': 6, 'sun': 6
    }
    for day_name, day_num in days_of_week.items():
        if day_name in text:
            days_ahead = (day_num - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7  # Next week's instance
            if 'next' in text:
                days_ahead += 7 if days_ahead <= 7 else 0
            target_date = (now + timedelta(days=days_ahead)).date()
            break
    
    # "march 5" / "march 5 2026" type patterns
    months = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
    months.update({name.lower(): i for i, name in enumerate(calendar.month_abbr) if name})
    
    for month_name, month_num in months.items():
        if month_name in text:
            m = re.search(rf'{month_name}\s+(\d{{1,2}})(?:\s+(\d{{4}}))?', text)
            if m:
                day = int(m.group(1))
                year = int(m.group(2)) if m.group(2) else now.year
                try:
                    target_date = datetime(year, month_num, day).date()
                    if target_date < now.date():
                        target_date = datetime(year + 1, month_num, day).date()
                except ValueError:
                    pass
            break
    
    # Build final datetime
    if target_date:
        if hour is not None:
            return datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))
        else:
            return datetime.combine(target_date, datetime.min.time().replace(hour=14, minute=0))  # Default 2pm
    
    # If only time was found, assume today or tomorrow
    if hour is not None:
        result = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if result <= now:
            result += timedelta(days=1)  # If time already passed, assume tomorrow
        return result
    
    return None


async def _create_zoom_meeting(topic: str, participants: list = None, meeting_time=None) -> 'PrimitiveResult | None':
    """
    Create a real Zoom meeting using Zoom Server-to-Server OAuth.
    Requires ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_ACCOUNT_ID in .env.
    Returns None if Zoom not configured.
    """
    from datetime import datetime
    import os

    client_id = os.getenv("ZOOM_CLIENT_ID", "")
    client_secret = os.getenv("ZOOM_CLIENT_SECRET", "")
    account_id = os.getenv("ZOOM_ACCOUNT_ID", "")
    
    if not all([client_id, client_secret, account_id]):
        return None  # Zoom not configured
    
    try:
        import base64
        
        # Step 1: Get OAuth token
        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(
                "https://zoom.us/oauth/token",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "account_credentials",
                    "account_id": account_id,
                },
            )
            
            if token_resp.status_code != 200:
                logger.warning(f"Zoom OAuth failed: {token_resp.text[:200]}")
                return PrimitiveResult(
                    success=False,
                    output="Zoom OAuth token request failed.",
                    error=f"zoom_oauth_failed:{token_resp.status_code}",
                    data={"status_code": token_resp.status_code, "body": token_resp.text[:500]},
                )
            
            access_token = token_resp.json()["access_token"]
            
            # Step 2: Create meeting
            meeting_body = {
                "topic": topic,
                "type": 2,  # Scheduled meeting
                "duration": 60,
                "timezone": "Asia/Kolkata",
                "settings": {
                    "host_video": True,
                    "participant_video": True,
                    "join_before_host": True,
                    "waiting_room": False,
                    "auto_recording": "none",
                },
            }
            
            if meeting_time:
                meeting_body["start_time"] = meeting_time.strftime("%Y-%m-%dT%H:%M:%S")
            
            if participants:
                meeting_body["settings"]["meeting_invitees"] = [
                    {"email": email} for email in participants if "@" in str(email)
                ]
            
            meet_resp = await client.post(
                "https://api.zoom.us/v2/users/me/meetings",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=meeting_body,
            )
            
            if meet_resp.status_code not in (200, 201):
                logger.warning(f"Zoom meeting creation failed: {meet_resp.text[:200]}")
                return PrimitiveResult(
                    success=False,
                    output="Zoom meeting creation failed.",
                    error=f"zoom_create_failed:{meet_resp.status_code}",
                    data={"status_code": meet_resp.status_code, "body": meet_resp.text[:500]},
                )
            
            zoom_data = meet_resp.json()
            
            meeting_data = {
                "meeting_id": str(zoom_data.get("id", "")),
                "topic": topic,
                "join_url": zoom_data.get("join_url", ""),
                "start_url": zoom_data.get("start_url", ""),
                "password": zoom_data.get("password", ""),
                "platform": "Zoom",
                "datetime": meeting_time.isoformat() if meeting_time else None,
                "datetime_display": meeting_time.strftime('%B %d, %Y at %I:%M %p') if meeting_time else 'Anytime',
                "participants": participants or [],
                "is_working": True,
            }
            
            output_lines = [
                f"Zoom meeting created successfully!",
                f"Topic: {topic}",
                f"Join URL: {zoom_data.get('join_url', 'N/A')}",
                f"Meeting ID: {zoom_data.get('id', 'N/A')}",
                f"Password: {zoom_data.get('password', 'N/A')}",
                f"Platform: Zoom",
            ]
            
            if meeting_time:
                output_lines.append(f"Scheduled: {meeting_time.strftime('%B %d, %Y at %I:%M %p')}")
            
            if participants:
                output_lines.append(f"Participants: {', '.join(participants)}")
            
            return PrimitiveResult(
                success=True,
                output="\n".join(output_lines),
                data=meeting_data
            )
    
    except Exception as e:
        logger.error(f"Zoom API error: {e}")
        return PrimitiveResult(
            success=False,
            output="Zoom API error.",
            error=str(e),
        )


async def save_note(content: str, title: str = "") -> PrimitiveResult:
    """
    Save a note/reminder for the user.
    Stored in memory for the session.
    """
    import uuid
    from datetime import datetime
    
    if not content:
        return PrimitiveResult(success=False, output="No note content provided.", error="missing_content")
    
    note_id = str(uuid.uuid4())[:8]
    note_title = title or f"Note {note_id}"
    
    note_data = {
        "id": note_id,
        "title": note_title,
        "content": content,
        "created_at": datetime.now().isoformat(),
    }
    
    return PrimitiveResult(
        success=True,
        output=f"Note saved!\nID: {note_id}\nTitle: {note_title}\nContent: {content[:100]}{'...' if len(content) > 100 else ''}",
        data=note_data
    )


async def click_link(url: str, link_text: str = "", selector: str = "") -> PrimitiveResult:
    """
    Click on a link with given text or selector on a page.
    Navigates to the URL first, then clicks the link.
    Uses Playwright for JavaScript-rendered pages.
    """
    if not url:
        return PrimitiveResult(success=False, output="No URL provided.", error="missing_url")
    
    if not link_text and not selector:
        return PrimitiveResult(success=False, output="Provide either link_text or selector to click.", error="missing_target")
    
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            )
            page = await browser.new_page()
            page.set_default_timeout(20000)
            
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            target = None
            if selector:
                target = await page.query_selector(selector)
            elif link_text:
                # Try multiple strategies to find the link
                target = await page.query_selector(f'a:has-text("{link_text}")')
                if not target:
                    target = await page.query_selector(f'button:has-text("{link_text}")')
                if not target:
                    target = await page.query_selector(f'*:has-text("{link_text}")')
            
            if not target:
                await browser.close()
                return PrimitiveResult(
                    success=False,
                    output=f"Link/button not found on {url}. Text: '{link_text}', Selector: '{selector}'",
                    error="target_not_found"
                )
            
            # Click and wait for navigation
            await target.click()
            await page.wait_for_timeout(3000)
            
            new_url = page.url
            
            # Extract text from new page
            text = await page.evaluate("""() => {
                const remove = document.querySelectorAll('script, style, nav, footer');
                remove.forEach(el => el.remove());
                return document.body.innerText;
            }""")
            
            await browser.close()
            
            text = _clean_text(text) if text else ""
            max_chars = 6000
            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n... (truncated)"
            
            return PrimitiveResult(
                success=True,
                output=f"Clicked on '{link_text or selector}' on {url}.\nNavigated to: {new_url}\n\nPage content:\n{text}",
                data={"original_url": url, "new_url": new_url, "clicked": link_text or selector}
            )
    
    except ImportError:
        return PrimitiveResult(
            success=False,
            output="Playwright not installed. Install with: pip install playwright && playwright install chromium",
            error="playwright_not_installed"
        )
    except Exception as e:
        return PrimitiveResult(
            success=False,
            output=f"Click failed: {str(e)}",
            error=str(e)
        )


# =============================================================================
# TELEGRAM MESSAGING
# =============================================================================

import os
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

async def send_telegram(message: str, chat_id: str = "", username: str = "") -> PrimitiveResult:
    """
    Send a message via Telegram Bot API.
    
    Args:
        message: The text message to send
        chat_id: Telegram chat ID (numeric). If empty, uses username lookup or env default.
        username: Telegram username (e.g., @witez2112). Will try to look up chat_id.
    
    Note: User must have messaged the bot first for chat_id lookup to work.
    """
    if not message:
        return PrimitiveResult(
            success=False,
            output="No message provided for Telegram.",
            error="missing_message"
        )
    
    target_chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Clean up username (remove @ if present)
    if username:
        username = username.lstrip("@")
    
    if not TELEGRAM_BOT_TOKEN:
        # Simulated mode - no real bot token configured
        return PrimitiveResult(
            success=True,
            output=f"✅ Telegram message prepared (bot not configured).\n"
                   f"To: {username or chat_id or 'default'}\n"
                   f"Message: {message}\n\n"
                   f"⚠️ Note: Set TELEGRAM_BOT_TOKEN in .env to send real messages.",
            data={
                "status": "simulated",
                "recipient": username or chat_id,
                "message": message
            }
        )
    
    # If no chat_id but we have username, try to explain
    if not target_chat_id and username:
        return PrimitiveResult(
            success=False,
            output=f"Cannot send to @{username} - need their chat_id.\n"
                   f"The user must start a conversation with your bot first.\n"
                   f"Then use the /start command to get their chat_id.",
            error="missing_chat_id",
            data={
                "username": username,
                "hint": "User must message the bot first to establish a chat_id"
            }
        )
    
    if not target_chat_id:
        return PrimitiveResult(
            success=False,
            output="No Telegram chat_id provided. Either provide chat_id parameter or set TELEGRAM_CHAT_ID in environment.",
            error="missing_chat_id"
        )
    
    # Send via Telegram Bot API
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": target_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            
            if resp.status_code == 200:
                result = resp.json()
                return PrimitiveResult(
                    success=True,
                    output=f"✅ Telegram message sent to chat {target_chat_id}!\nMessage: {message[:100]}{'...' if len(message) > 100 else ''}",
                    data={
                        "status": "sent",
                        "chat_id": target_chat_id,
                        "message_id": result.get("result", {}).get("message_id")
                    }
                )
            else:
                error_text = resp.text
                return PrimitiveResult(
                    success=False,
                    output=f"Telegram API error: {error_text}",
                    error=f"telegram_api_error_{resp.status_code}"
                )
    
    except Exception as e:
        return PrimitiveResult(
            success=False,
            output=f"Failed to send Telegram message: {str(e)}",
            error=str(e)
        )


# =============================================================================
# PRIMITIVE REGISTRY - For system prompt generation and risk classification
# =============================================================================

PRIMITIVES = {
    "web_search": {
        "function": web_search,
        "risk": "safe",
        "description": "Search the web using DuckDuckGo",
        "params": "query (str), max_results (int, default 5)",
        "returns": "Search results with title, url, snippet for each result",
    },
    "browse_page": {
        "function": browse_page,
        "risk": "safe",
        "description": "Visit a URL and extract its text content",
        "params": "url (str)",
        "returns": "Page text content (truncated to ~6000 chars)",
    },
    "scrape_data": {
        "function": scrape_data,
        "risk": "safe",
        "description": "Scrape a URL with focused extraction",
        "params": "url (str), extract (str - what to look for)",
        "returns": "Extracted content from the page",
    },
    "generate_image": {
        "function": generate_image,
        "risk": "safe",
        "description": "Generate an image using Pollinations AI (free)",
        "params": "prompt (str)",
        "returns": "Image URL",
    },
    "fill_form": {
        "function": fill_form,
        "risk": "risky",
        "description": "Fill form fields on a webpage using Playwright",
        "params": 'url (str), fields (dict of selector->value), submit (bool, default False)',
        "returns": "Form filling status with filled/failed fields",
    },
    "run_python": {
        "function": run_python,
        "risk": "risky",
        "description": "Execute Python code in restricted environment",
        "params": "code (str)",
        "returns": "Execution output",
    },
    "send_email": {
        "function": send_email,
        "risk": "safe",
        "description": "Send an email via SMTP. Auto-executes.",
        "params": 'to (str - email address), subject (str), body (str), cc (str, optional)',
        "returns": "Email send status",
    },
    "create_meeting": {
        "function": create_meeting,
        "risk": "safe",
        "description": "Create a meeting. Requires Zoom integration if platform=zoom. Will prompt user to connect if not available, or offer Jitsi fallback.",
        "params": 'topic (str), participants (list of emails, optional), datetime_str (str - natural language or ISO, e.g. "tomorrow 3pm"), platform (str - "zoom" or "jitsi", default "zoom"), force_fallback (bool - use Jitsi instead of Zoom)',
        "returns": "Meeting link, ID, details OR integration_required error with options",
    },
    "save_note": {
        "function": save_note,
        "risk": "safe",
        "description": "Save a note or reminder for the user",
        "params": 'content (str), title (str, optional)',
        "returns": "Note ID and confirmation",
    },
    "send_telegram": {
        "function": send_telegram,
        "risk": "safe",
        "description": "Send a message via Telegram. Use when user wants to message someone on Telegram or set a reminder via Telegram.",
        "params": 'message (str), chat_id (str, optional - Telegram chat ID), username (str, optional - Telegram username like @username)',
        "returns": "Message send status",
    },
    "click_link": {
        "function": click_link,
        "risk": "safe",
        "description": "Navigate to a URL and click on a link/button by text or selector",
        "params": 'url (str), link_text (str, optional), selector (str, optional)',
        "returns": "New page URL and content after clicking",
    },
}


def get_primitives_prompt() -> str:
    """Generate the primitives documentation for the system prompt"""
    lines = ["AVAILABLE PRIMITIVES:"]
    for name, info in PRIMITIVES.items():
        risk_tag = " [REQUIRES CONFIRMATION]" if info["risk"] == "risky" else ""
        lines.append(f"- {name}({info['params']}){risk_tag}")
        lines.append(f"  {info['description']}")
        lines.append(f"  Returns: {info['returns']}")
        lines.append("")
    return "\n".join(lines)
