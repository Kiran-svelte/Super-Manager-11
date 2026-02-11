"""
Image Generation Tool - Pollinations AI
=========================================
Generate images from text descriptions.
Uses Pollinations AI (completely free, no API key needed).
Falls back to Together AI if available.
"""

import os
import secrets
from urllib.parse import quote
import httpx

from .base import Tool, ToolResult


class ImageGenerationTool(Tool):
    name = "generate_image"
    description = "Generate an image from a text description using AI"
    parameters = {
        "prompt": {"description": "Detailed description of the image to generate", "required": True, "type": "string"},
        "count": {"description": "Number of images to generate (1-4)", "required": False, "type": "integer", "default": 1},
        "style": {"description": "Style hint: logo, icon, photo, illustration, banner", "required": False, "type": "string"},
    }
    requires_confirmation = False

    async def execute(self, **params) -> ToolResult:
        prompt = params.get("prompt", "")
        count = min(params.get("count", 1), 4)
        style = params.get("style", "")

        if not prompt:
            return ToolResult(success=False, output="No image prompt provided.", error="missing_prompt")

        # Enhance prompt with style
        if style:
            style_mods = {
                "logo": "professional logo design, minimalist, vector style, clean lines, centered, white background",
                "icon": "app icon, flat design, simple, bold colors",
                "illustration": "detailed illustration, colorful, artistic",
                "photo": "photorealistic, high quality, sharp focus, 8K",
                "banner": "wide banner, promotional, eye-catching",
            }
            mod = style_mods.get(style, style)
            prompt = f"{prompt}, {mod}"

        # Try Together AI first if key available, then Pollinations
        together_key = os.getenv("TOGETHER_API_KEY", "")
        if together_key:
            try:
                return await self._generate_together(prompt, count, together_key)
            except Exception:
                pass

        # Pollinations AI (always free, no key)
        return await self._generate_pollinations(prompt, count)

    async def _generate_pollinations(self, prompt: str, count: int) -> ToolResult:
        """Generate using Pollinations AI (FREE, no API key)"""
        images = []
        base_url = "https://image.pollinations.ai/prompt"

        for i in range(count):
            seed = secrets.randbelow(1000000)
            encoded_prompt = quote(f"{prompt}, seed:{seed}")
            image_url = f"{base_url}/{encoded_prompt}?width=1024&height=1024&nologo=true"
            images.append({
                "id": f"img_{secrets.token_hex(4)}",
                "url": image_url,
                "alt": f"Generated image {i + 1}",
                "prompt": prompt,
                "downloadable": True,
                "index": i + 1,
            })

        output_lines = [f"Generated {count} image(s) for: '{prompt}'"]
        for img in images:
            output_lines.append(f"- Image {img['index']}: {img['url']}")

        return ToolResult(
            success=True,
            output="\n".join(output_lines),
            data={
                "images": images,
                "provider": "pollinations_ai",
                "ui_components": {
                    "type": "image_gallery",
                    "images": images,
                },
            },
        )

    async def _generate_together(self, prompt: str, count: int, api_key: str) -> ToolResult:
        """Generate using Together AI FLUX model"""
        images = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i in range(count):
                response = await client.post(
                    "https://api.together.xyz/v1/images/generations",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "black-forest-labs/FLUX.1-schnell-Free",
                        "prompt": prompt,
                        "n": 1,
                        "width": 1024,
                        "height": 1024,
                        "steps": 4,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data") and len(data["data"]) > 0:
                        url = data["data"][0].get("url", "")
                        if url:
                            images.append({
                                "id": f"img_{secrets.token_hex(4)}",
                                "url": url,
                                "alt": f"Generated image {i + 1}",
                                "prompt": prompt,
                                "downloadable": True,
                                "index": i + 1,
                            })

        if not images:
            raise Exception("Together AI returned no images")

        output_lines = [f"Generated {len(images)} image(s) for: '{prompt}'"]
        for img in images:
            output_lines.append(f"- Image {img['index']}: {img['url']}")

        return ToolResult(
            success=True,
            output="\n".join(output_lines),
            data={
                "images": images,
                "provider": "together_ai",
                "ui_components": {
                    "type": "image_gallery",
                    "images": images,
                },
            },
        )
