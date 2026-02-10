"""
IMAGE GENERATION SERVICE
========================
Real image generation using multiple providers:
- Together AI (FLUX model - free tier)
- Replicate
- Stability AI
- OpenAI DALL-E

Returns actual image URLs, not fake responses.
"""

import os
import asyncio
import aiohttp
import base64
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """
    Real image generation service with multiple provider fallback.
    """
    
    def __init__(self):
        self.together_key = os.getenv("TOGETHER_API_KEY")
        self.replicate_key = os.getenv("REPLICATE_API_KEY")
        self.stability_key = os.getenv("STABILITY_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        # Track which providers are available
        self.available_providers = []
        if self.together_key:
            self.available_providers.append("together")
        if self.replicate_key:
            self.available_providers.append("replicate")
        if self.stability_key:
            self.available_providers.append("stability")
        if self.openai_key:
            self.available_providers.append("openai")
    
    def has_providers(self) -> bool:
        """Check if any image generation provider is available"""
        return len(self.available_providers) > 0
    
    async def generate_images(
        self,
        prompt: str,
        num_images: int = 1,
        style: str = "logo",
        width: int = 1024,
        height: int = 1024
    ) -> Dict:
        """
        Generate images using available providers.
        
        Returns:
            {
                "success": bool,
                "images": [{"url": "...", "id": "..."}],
                "provider": "which provider was used",
                "error": "error message if failed"
            }
        """
        
        if not self.has_providers():
            return {
                "success": False,
                "error": "No image generation provider configured. Set TOGETHER_API_KEY, OPENAI_API_KEY, or STABILITY_API_KEY.",
                "fallback_tools": self._get_fallback_tools()
            }
        
        # Enhance prompt for better results
        enhanced_prompt = self._enhance_prompt(prompt, style)
        
        # Try providers in order of preference
        for provider in self.available_providers:
            try:
                if provider == "together":
                    result = await self._generate_with_together(enhanced_prompt, num_images, width, height)
                elif provider == "replicate":
                    result = await self._generate_with_replicate(enhanced_prompt, num_images, width, height)
                elif provider == "stability":
                    result = await self._generate_with_stability(enhanced_prompt, num_images, width, height)
                elif provider == "openai":
                    result = await self._generate_with_openai(enhanced_prompt, num_images, width, height)
                else:
                    continue
                
                if result.get("success"):
                    result["provider"] = provider
                    return result
                    
            except Exception as e:
                logger.error(f"Image generation failed with {provider}: {str(e)}")
                continue
        
        return {
            "success": False,
            "error": "All image generation providers failed",
            "fallback_tools": self._get_fallback_tools()
        }
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance prompt for better image generation results"""
        
        style_modifiers = {
            "logo": "professional logo design, clean vector graphics, minimalist, brand identity, high contrast, centered composition",
            "icon": "app icon, simple flat design, recognizable, bold colors, clean edges",
            "illustration": "detailed illustration, artistic, colorful, professional quality",
            "photo": "photorealistic, high quality, professional photography, sharp focus",
            "banner": "wide banner design, promotional, eye-catching, professional marketing material",
            "poster": "poster design, bold typography, promotional, event marketing"
        }
        
        modifier = style_modifiers.get(style, style_modifiers["logo"])
        return f"{prompt}, {modifier}, white or transparent background, 4k quality"
    
    async def _generate_with_together(
        self,
        prompt: str,
        num_images: int,
        width: int,
        height: int
    ) -> Dict:
        """Generate images using Together AI's FLUX model"""
        
        async with aiohttp.ClientSession() as session:
            # Generate images one at a time (API limitation)
            images = []
            
            for i in range(num_images):
                try:
                    async with session.post(
                        "https://api.together.xyz/v1/images/generations",
                        headers={
                            "Authorization": f"Bearer {self.together_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "black-forest-labs/FLUX.1-schnell-Free",
                            "prompt": prompt,
                            "n": 1,
                            "width": min(width, 1024),  # FLUX max is 1024
                            "height": min(height, 1024),
                            "steps": 4  # Schnell model uses 4 steps
                        },
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("data") and len(data["data"]) > 0:
                                image_url = data["data"][0].get("url", "")
                                if image_url:
                                    images.append({
                                        "id": f"img_{uuid.uuid4().hex[:8]}",
                                        "url": image_url,
                                        "index": i + 1
                                    })
                        else:
                            text = await response.text()
                            logger.error(f"Together AI error: {response.status} - {text}")
                            
                except Exception as e:
                    logger.error(f"Together AI image {i+1} failed: {str(e)}")
            
            if images:
                return {
                    "success": True,
                    "images": images,
                    "prompt": prompt
                }
            
            return {"success": False, "error": "Together AI failed to generate images"}
    
    async def _generate_with_replicate(
        self,
        prompt: str,
        num_images: int,
        width: int,
        height: int
    ) -> Dict:
        """Generate images using Replicate API"""
        
        async with aiohttp.ClientSession() as session:
            # Start prediction
            async with session.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {self.replicate_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": "ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",  # SDXL
                    "input": {
                        "prompt": prompt,
                        "width": width,
                        "height": height,
                        "num_outputs": num_images
                    }
                },
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 201:
                    return {"success": False, "error": f"Replicate API error: {response.status}"}
                
                prediction = await response.json()
                prediction_id = prediction.get("id")
            
            # Poll for completion
            for _ in range(60):  # Max 60 seconds
                await asyncio.sleep(1)
                
                async with session.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers={"Authorization": f"Token {self.replicate_key}"}
                ) as response:
                    result = await response.json()
                    
                    if result.get("status") == "succeeded":
                        output = result.get("output", [])
                        images = [
                            {"id": f"img_{uuid.uuid4().hex[:8]}", "url": url, "index": i+1}
                            for i, url in enumerate(output)
                        ]
                        return {"success": True, "images": images, "prompt": prompt}
                    
                    elif result.get("status") == "failed":
                        return {"success": False, "error": result.get("error", "Generation failed")}
            
            return {"success": False, "error": "Timeout waiting for image generation"}
    
    async def _generate_with_stability(
        self,
        prompt: str,
        num_images: int,
        width: int,
        height: int
    ) -> Dict:
        """Generate images using Stability AI"""
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {self.stability_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "text_prompts": [{"text": prompt, "weight": 1}],
                    "cfg_scale": 7,
                    "width": width,
                    "height": height,
                    "samples": num_images,
                    "steps": 30
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    return {"success": False, "error": f"Stability API error: {response.status}"}
                
                data = await response.json()
                images = []
                
                for i, artifact in enumerate(data.get("artifacts", [])):
                    if artifact.get("base64"):
                        # Convert base64 to data URL
                        image_data = f"data:image/png;base64,{artifact['base64']}"
                        images.append({
                            "id": f"img_{uuid.uuid4().hex[:8]}",
                            "url": image_data,
                            "index": i + 1
                        })
                
                if images:
                    return {"success": True, "images": images, "prompt": prompt}
                
                return {"success": False, "error": "No images returned"}
    
    async def _generate_with_openai(
        self,
        prompt: str,
        num_images: int,
        width: int,
        height: int
    ) -> Dict:
        """Generate images using OpenAI DALL-E 3"""
        
        # DALL-E 3 only supports 1 image at a time
        images = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(num_images):
                try:
                    async with session.post(
                        "https://api.openai.com/v1/images/generations",
                        headers={
                            "Authorization": f"Bearer {self.openai_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "dall-e-3",
                            "prompt": prompt,
                            "n": 1,
                            "size": "1024x1024",
                            "quality": "standard"
                        },
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("data") and len(data["data"]) > 0:
                                image_url = data["data"][0].get("url", "")
                                if image_url:
                                    images.append({
                                        "id": f"img_{uuid.uuid4().hex[:8]}",
                                        "url": image_url,
                                        "index": i + 1
                                    })
                        else:
                            text = await response.text()
                            logger.error(f"OpenAI DALL-E error: {response.status} - {text}")
                            
                except Exception as e:
                    logger.error(f"OpenAI image {i+1} failed: {str(e)}")
        
        if images:
            return {"success": True, "images": images, "prompt": prompt}
        
        return {"success": False, "error": "OpenAI DALL-E failed to generate images"}
    
    def _get_fallback_tools(self) -> List[Dict]:
        """Return list of free fallback tools when no API is available"""
        return [
            {
                "name": "Canva Logo Maker",
                "url": "https://www.canva.com/create/logos/",
                "description": "Free drag-and-drop logo design"
            },
            {
                "name": "Looka",
                "url": "https://looka.com/",
                "description": "AI-powered logo generator"
            },
            {
                "name": "Bing Image Creator",
                "url": "https://www.bing.com/images/create",
                "description": "Free DALL-E powered image generation"
            },
            {
                "name": "Leonardo AI",
                "url": "https://leonardo.ai/",
                "description": "Free tier AI image generation"
            },
            {
                "name": "Ideogram",
                "url": "https://ideogram.ai/",
                "description": "Free AI image generation with good text"
            }
        ]


# Singleton instance
_image_service: Optional[ImageGenerationService] = None


def get_image_service() -> ImageGenerationService:
    """Get singleton image service instance"""
    global _image_service
    if _image_service is None:
        _image_service = ImageGenerationService()
    return _image_service
