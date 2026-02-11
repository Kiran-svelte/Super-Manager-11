"""
Browse Website Tool - Playwright
=================================
Visit a URL and extract its text content.
Uses Playwright for JavaScript-rendered pages.
Falls back to httpx for simple pages.
"""

import re
import httpx

from .base import Tool, ToolResult


class BrowseWebsiteTool(Tool):
    name = "browse_website"
    description = "Visit a URL and extract its text content for analysis"
    parameters = {
        "url": {"description": "The URL to visit", "required": True, "type": "string"},
        "extract": {"description": "What to look for, e.g. 'prices', 'main article', 'contact info'", "required": False, "type": "string"},
    }
    requires_confirmation = False

    async def execute(self, **params) -> ToolResult:
        url = params.get("url", "")
        extract_hint = params.get("extract", "")

        if not url:
            return ToolResult(success=False, output="No URL provided.", error="missing_url")

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # Try Playwright first, fall back to httpx
        try:
            text = await self._fetch_with_playwright(url)
        except Exception:
            try:
                text = await self._fetch_with_httpx(url)
            except Exception as e:
                return ToolResult(
                    success=False,
                    output=f"Failed to fetch {url}: {str(e)}",
                    error=str(e),
                )

        if not text or len(text.strip()) < 50:
            return ToolResult(
                success=True,
                output=f"Page at {url} returned very little text content.",
                data={"url": url, "content_length": len(text) if text else 0},
            )

        # Truncate to avoid massive LLM context
        max_chars = 4000
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n... (truncated, {len(text)} total characters)"

        output = f"Content from {url}:\n\n{text}"
        if extract_hint:
            output = f"Content from {url} (looking for: {extract_hint}):\n\n{text}"

        return ToolResult(
            success=True,
            output=output,
            data={"url": url, "content_length": len(text)},
        )

    async def _fetch_with_playwright(self, url: str) -> str:
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
            # Wait a bit for dynamic content
            await page.wait_for_timeout(2000)

            # Extract text content
            text = await page.evaluate("""() => {
                // Remove script, style, nav, footer elements
                const remove = document.querySelectorAll('script, style, nav, footer, header, aside, .ad, .advertisement, .sidebar');
                remove.forEach(el => el.remove());
                return document.body.innerText;
            }""")

            await browser.close()
            return self._clean_text(text)

    async def _fetch_with_httpx(self, url: str) -> str:
        """Fallback: fetch with httpx and parse HTML"""
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )
            html = response.text

            # Strip HTML tags
            text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return self._clean_text(text)

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        # Remove excessive whitespace
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 2:
                cleaned.append(line)
        return "\n".join(cleaned)
