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

        # Verify the URL is accessible
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.head(image_url, follow_redirects=True)
            if response.status_code >= 400:
                return PrimitiveResult(
                    success=False,
                    output=f"Image generation failed (status {response.status_code}).",
                    error=f"HTTP {response.status_code}",
                )

        return PrimitiveResult(
            success=True,
            output=f"Image generated successfully!\nURL: {image_url}\nPrompt: {prompt}",
            data={"image_url": image_url, "prompt": prompt, "seed": seed},
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
        page = await browser.new_page()
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
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
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
