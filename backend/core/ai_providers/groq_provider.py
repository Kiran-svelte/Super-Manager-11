"""
Groq Provider - Ultra-fast inference with Llama, Mixtral
Secondary fallback with great speed
"""
import os
import time
from typing import Dict, Any, List, Optional, AsyncGenerator, Union

from .base_provider import BaseAIProvider, ProviderConfig, AIResponse, ProviderStatus

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class GroqProvider(BaseAIProvider):
    """
    Groq API provider.
    Ultra-fast inference with open models.
    """
    
    config = ProviderConfig(
        name="groq",
        supports_streaming=True,
        supports_vision=True,  # llava on groq
        supports_function_calling=True,
        supports_json_mode=True,
        is_local=False,
        is_free=True,  # Has generous free tier
        base_url="https://api.groq.com/openai/v1",
        models=[
            "llama-3.3-70b-versatile",
            "llama-3.2-90b-text-preview",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "llama3-groq-70b-8192-tool-use-preview",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "llava-v1.5-7b-4096-preview"
        ],
        default_model="llama-3.3-70b-versatile",
        timeout=60,  # Groq is fast
        cost_per_1k_tokens=0.0  # Free tier
    )
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self._client = None
        
        if self.api_key and GROQ_AVAILABLE:
            self._client = AsyncGroq(api_key=self.api_key)
            self._status = ProviderStatus.AVAILABLE
        else:
            self._status = ProviderStatus.UNAVAILABLE
            if not GROQ_AVAILABLE:
                self._last_error = "groq package not installed"
            else:
                self._last_error = "GROQ_API_KEY not set"
    
    async def health_check(self) -> bool:
        """Check if Groq API is accessible"""
        if not self._client:
            return False
        
        try:
            # Quick test with minimal tokens
            response = await self._client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1
            )
            self._status = ProviderStatus.AVAILABLE
            return True
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
        """Generate completion using Groq"""
        
        if not self._client:
            raise Exception("Groq client not initialized")
        
        model = model or self.config.default_model
        start_time = time.time()
        
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        if json_mode:
            params["response_format"] = {"type": "json_object"}
        
        # Tool use support
        if "tools" in kwargs:
            params["tools"] = kwargs["tools"]
        
        try:
            if stream:
                return self._stream_generate(params, model, start_time)
            
            response = await self._client.chat.completions.create(**params)
            
            latency_ms = (time.time() - start_time) * 1000
            self._record_latency(latency_ms)
            self._reset_errors()
            
            choice = response.choices[0]
            
            return AIResponse(
                content=choice.message.content or "",
                model=model,
                provider="groq",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                finish_reason=choice.finish_reason or "stop",
                latency_ms=latency_ms,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            self._record_error(str(e))
            raise
    
    async def _stream_generate(
        self,
        params: Dict[str, Any],
        model: str,
        start_time: float
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Groq"""
        try:
            stream = await self._client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
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
        """Groq doesn't support embeddings - raise error"""
        raise NotImplementedError("Groq does not support embeddings. Use Ollama or OpenAI.")


# Singleton
_groq_provider: Optional[GroqProvider] = None


def get_groq_provider() -> GroqProvider:
    """Get or create Groq provider singleton"""
    global _groq_provider
    if _groq_provider is None:
        _groq_provider = GroqProvider()
    return _groq_provider
