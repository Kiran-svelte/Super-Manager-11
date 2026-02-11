"""
Web Search Tool - DuckDuckGo
=============================
Search the web for information using DuckDuckGo HTML scraping.
Free, no API key needed.
"""

import re
from urllib.parse import unquote
import httpx

from .base import Tool, ToolResult


class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for information using DuckDuckGo"
    parameters = {
        "query": {"description": "Search terms", "required": True, "type": "string"},
        "max_results": {"description": "Number of results to return", "required": False, "type": "integer", "default": 5},
    }
    requires_confirmation = False

    async def execute(self, **params) -> ToolResult:
        query = params.get("query", "")
        max_results = params.get("max_results", 5)

        if not query:
            return ToolResult(success=False, output="No search query provided.", error="missing_query")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": query},
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    timeout=15.0,
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
                    return ToolResult(
                        success=True,
                        output=f"No results found for '{query}'.",
                        data={"results": []},
                    )

                # Format output for LLM
                output_lines = [f"Search results for '{query}':"]
                for i, r in enumerate(results, 1):
                    output_lines.append(f"{i}. {r['title']}")
                    output_lines.append(f"   URL: {r['url']}")
                    if r["snippet"]:
                        output_lines.append(f"   {r['snippet'][:150]}")
                    output_lines.append("")

                return ToolResult(
                    success=True,
                    output="\n".join(output_lines),
                    data={"results": results, "query": query},
                )

        except Exception as e:
            return ToolResult(success=False, output=f"Search failed: {str(e)}", error=str(e))
