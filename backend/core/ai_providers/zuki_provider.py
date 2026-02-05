"""
Zukijourney API Provider - Free OpenAI-compatible API
Alternative free provider with various models
"""
import os
import time
import httpx
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
import json

from .base_provider import BaseAIProvider, ProviderConfig, AIResponse, ProviderStatus


class ZukiProvider(BaseAIProvider):
    """
    Zukijourney API provider.
    Free OpenAI-compatible API with various models.
    Based on zukijourney/example-api patterns.
    """
    
    config = ProviderConfig(
        name="zuki",
        supports_streaming=True,
        supports_vision=True,
        supports_function_calling=True,
        supports_json_mode=True,
        is_local=False,
        is_free=True,
        base_url="https://zukijourney.xyzbot.net/v1",  # Default endpoint
        models=[
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            "llama-3.1-70b",
            "llama-3.1-405b",
            "mixtral-8x7b",
            "gemini-pro"
        ],
        default_model="gpt-4o-mini",
        timeout=120,
        cost_per_1k_tokens=0.0
    )
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("ZUKI_API_KEY", "")
        self.base_url = os.getenv("ZUKI_BASE_URL", self.config.base_url)
        self._client = httpx.AsyncClient(timeout=self.config.timeout)
        
        if self.api_key:
            self._status = ProviderStatus.AVAILABLE
        else:
            self._status = ProviderStatus.UNAVAILABLE
            self._last_error = "ZUKI_API_KEY not set"
    
    async def health_check(self) -> bool:
        """Check if Zuki API is accessible"""
        if not self.api_key:
            return False
        
        try:
            response = await self._client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            if response.status_code == 200:
                self._status = ProviderStatus.AVAILABLE
                return True
            self._status = ProviderStatus.UNAVAILABLE
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
        """Generate completion using Zuki API (OpenAI-compatible)"""
        
        if not self.api_key:
            raise Exception("Zuki API key not configured")
        
        model = model or self.config.default_model
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        try:
            if stream:
                return self._stream_generate(headers, payload, model, start_time)
            
            response = await self._client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code != 200:
                error_msg = response.text
                self._record_error(f"HTTP {response.status_code}: {error_msg}")
                raise Exception(f"Zuki API error: {error_msg}")
            
            data = response.json()
            self._record_latency(latency_ms)
            self._reset_errors()
            
            choice = data.get("choices", [{}])[0]
            usage = data.get("usage", {})
            
            return AIResponse(
                content=choice.get("message", {}).get("content", ""),
                model=model,
                provider="zuki",
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                },
                finish_reason=choice.get("finish_reason", "stop"),
                latency_ms=latency_ms,
                raw_response=data
            )
            
        except Exception as e:
            self._record_error(str(e))
            raise
    
    async def _stream_generate(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        model: str,
        start_time: float
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Zuki API"""
        try:
            async with self._client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
            
            self._record_latency((time.time() - start_time) * 1000)
            self._reset_errors()
            
        except Exception as e:
            self._record_error(str(e))
            raise
    
    async def generate_embedding(
        self,
        text: Union[str, List[str]],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings using Zuki API"""
        if not self.api_key:
            raise Exception("Zuki API key not configured")
        
        model = model or "text-embedding-3-small"
        texts = [text] if isinstance(text, str) else text
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self._client.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json={"model": model, "input": texts}
            )
            
            if response.status_code == 200:
                data = response.json()
                return [d["embedding"] for d in data.get("data", [])]
            else:
                raise Exception(f"Embedding error: {response.text}")
        except Exception as e:
            self._record_error(str(e))
            raise


# Singleton
_zuki_provider: Optional[ZukiProvider] = None


def get_zuki_provider() -> ZukiProvider:
    """Get or create Zuki provider singleton"""
    global _zuki_provider
    if _zuki_provider is None:
        _zuki_provider = ZukiProvider()
    return _zuki_provider
