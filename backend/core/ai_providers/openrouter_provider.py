"""
OpenRouter Provider - Unified access to 200+ AI models
Primary provider with broad model support and competitive pricing
"""
import os
import time
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
import json
import httpx

from .base_provider import BaseAIProvider, ProviderConfig, AIResponse, ProviderStatus


class OpenRouterProvider(BaseAIProvider):
    """
    OpenRouter API provider.
    Access 200+ models through a single API including:
    - Claude (Anthropic)
    - GPT-4 (OpenAI)
    - Llama (Meta)
    - Mistral
    - And many more
    
    Uses OpenAI-compatible API format.
    """
    
    config = ProviderConfig(
        name="openrouter",
        supports_streaming=True,
        supports_vision=True,
        supports_function_calling=True,
        supports_json_mode=True,
        is_local=False,
        is_free=False,  # Pay per token, but many free models available
        base_url="https://openrouter.ai/api/v1",
        models=[
            # Free models
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemini-2.0-flash-exp:free",
            "deepseek/deepseek-r1:free",
            "qwen/qwen-2.5-72b-instruct:free",
            # Popular paid models
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "google/gemini-pro-1.5",
            "meta-llama/llama-3.1-405b-instruct",
            "mistralai/mistral-large",
        ],
        default_model="meta-llama/llama-3.3-70b-instruct:free",  # Free and capable
        timeout=120,
        cost_per_1k_tokens=0.001  # Varies significantly by model
    )
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"
        self._client = None
        
        if self.api_key:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8000"),
                    "X-Title": "Super Manager AI",
                    "Content-Type": "application/json"
                },
                timeout=120.0
            )
            self._status = ProviderStatus.AVAILABLE
        else:
            self._status = ProviderStatus.UNAVAILABLE
            self._last_error = "OPENROUTER_API_KEY not set"
    
    async def health_check(self) -> bool:
        """Check if OpenRouter API is accessible"""
        if not self._client:
            return False
        
        try:
            # Check models endpoint
            response = await self._client.get("/models")
            if response.status_code == 200:
                self._status = ProviderStatus.AVAILABLE
                return True
            else:
                self._status = ProviderStatus.UNAVAILABLE
                self._record_error(f"API returned {response.status_code}")
                return False
        except Exception as e:
            self._status = ProviderStatus.UNAVAILABLE
            self._record_error(str(e))
            return False
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        json_mode: bool = False,
        **kwargs
    ) -> Union[AIResponse, AsyncGenerator[str, None]]:
        """Generate completion using OpenRouter"""
        
        if not self._client:
            raise Exception("OpenRouter client not initialized - check OPENROUTER_API_KEY")
        
        model = model or self.config.default_model
        start_time = time.time()
        
        # Build request body (OpenAI-compatible format)
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        
        # Add any extra kwargs
        body.update(kwargs)
        
        if stream:
            return self._stream_generate(body, start_time)
        else:
            return await self._sync_generate(body, start_time, model)
    
    async def _sync_generate(
        self, 
        body: Dict[str, Any], 
        start_time: float,
        model: str
    ) -> AIResponse:
        """Non-streaming generation"""
        try:
            response = await self._client.post("/chat/completions", json=body)
            
            if response.status_code != 200:
                error_text = response.text
                self._record_error(f"API error {response.status_code}: {error_text}")
                raise Exception(f"OpenRouter API error: {error_text}")
            
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            
            latency = time.time() - start_time
            self._record_success(latency)
            
            return AIResponse(
                content=content,
                model=model,
                provider="openrouter",
                tokens_used=usage.get("total_tokens", 0),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                latency=latency,
                raw_response=data
            )
        except Exception as e:
            self._record_error(str(e))
            raise
    
    async def _stream_generate(
        self, 
        body: Dict[str, Any],
        start_time: float
    ) -> AsyncGenerator[str, None]:
        """Streaming generation"""
        try:
            async with self._client.stream("POST", "/chat/completions", json=body) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"OpenRouter API error: {error_text}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
                
                latency = time.time() - start_time
                self._record_success(latency)
        except Exception as e:
            self._record_error(str(e))
            raise
    
    async def list_models(self) -> List[str]:
        """List available models from OpenRouter"""
        if not self._client:
            return self.config.models
        
        try:
            response = await self._client.get("/models")
            if response.status_code == 200:
                data = response.json()
                return [m["id"] for m in data.get("data", [])]
        except Exception:
            pass
        
        return self.config.models
    
    async def generate_embedding(
        self,
        text: Union[str, List[str]],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for text(s).
        OpenRouter doesn't natively support embeddings, so we return a placeholder.
        For real embeddings, use a dedicated embedding service.
        """
        # OpenRouter doesn't have embedding support
        # Return a simple hash-based placeholder
        import hashlib
        
        if isinstance(text, str):
            texts = [text]
        else:
            texts = text
        
        embeddings = []
        for t in texts:
            # Create a deterministic pseudo-embedding from text hash
            hash_bytes = hashlib.sha256(t.encode()).digest()
            # Convert to list of floats (normalized between -1 and 1)
            embedding = [(b - 128) / 128 for b in hash_bytes[:128]]
            # Pad to standard embedding size
            while len(embedding) < 384:
                embedding.extend(embedding[:min(384 - len(embedding), len(embedding))])
            embeddings.append(embedding[:384])
        
        return embeddings
    
    def _record_success(self, latency: float):
        """Record successful request"""
        self._record_latency(latency * 1000)  # Convert to ms
        self._reset_errors()
    
    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()


# Singleton instance
_openrouter_provider: Optional[OpenRouterProvider] = None


def get_openrouter_provider(api_key: Optional[str] = None) -> OpenRouterProvider:
    """Get or create OpenRouter provider instance"""
    global _openrouter_provider
    
    if _openrouter_provider is None:
        _openrouter_provider = OpenRouterProvider(api_key=api_key)
    
    return _openrouter_provider
