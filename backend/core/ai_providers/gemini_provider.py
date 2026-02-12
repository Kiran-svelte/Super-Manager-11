"""
Gemini Provider - Google's free AI via OpenAI-compatible API
Free tier: 15 req/min, 1500 req/day
Uses the OpenAI SDK against Google's compatibility endpoint.
"""
import os
import time
from typing import Dict, Any, List, Optional, AsyncGenerator, Union

from .base_provider import BaseAIProvider, ProviderConfig, AIResponse, ProviderStatus

try:
    from openai import AsyncOpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini API provider via OpenAI-compatible endpoint.
    Free tier with generous limits.
    """

    config = ProviderConfig(
        name="gemini",
        supports_streaming=True,
        supports_vision=True,
        supports_function_calling=True,
        supports_json_mode=True,
        is_local=False,
        is_free=True,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        models=[
            "gemini-2.5-flash-preview-05-20",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ],
        default_model="gemini-2.0-flash",
        timeout=120,
        cost_per_1k_tokens=0.0,
    )

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self._client = None

        if self.api_key and OPENAI_SDK_AVAILABLE:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.config.base_url,
            )
            self._status = ProviderStatus.AVAILABLE
        else:
            self._status = ProviderStatus.UNAVAILABLE
            if not OPENAI_SDK_AVAILABLE:
                self._last_error = "openai package not installed"
            else:
                self._last_error = "GEMINI_API_KEY not set"

    async def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            response = await self._client.chat.completions.create(
                model="gemini-2.0-flash-lite",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
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
        **kwargs,
    ) -> Union[AIResponse, AsyncGenerator[str, None]]:
        if not self._client:
            raise Exception("Gemini client not initialized")

        model = model or self.config.default_model
        start_time = time.time()

        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if json_mode:
            params["response_format"] = {"type": "json_object"}

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
                provider="gemini",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                finish_reason=choice.finish_reason or "stop",
                latency_ms=latency_ms,
                raw_response=response.model_dump() if hasattr(response, "model_dump") else None,
            )

        except Exception as e:
            self._record_error(str(e))
            raise

    async def _stream_generate(
        self,
        params: Dict[str, Any],
        model: str,
        start_time: float,
    ) -> AsyncGenerator[str, None]:
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
        model: Optional[str] = None,
    ) -> List[List[float]]:
        if not self._client:
            raise Exception("Gemini client not initialized")

        model = model or "text-embedding-004"
        texts = [text] if isinstance(text, str) else text

        try:
            response = await self._client.embeddings.create(
                model=model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            self._record_error(str(e))
            raise


_gemini_provider: Optional[GeminiProvider] = None


def get_gemini_provider() -> GeminiProvider:
    global _gemini_provider
    if _gemini_provider is None:
        _gemini_provider = GeminiProvider()
    return _gemini_provider
