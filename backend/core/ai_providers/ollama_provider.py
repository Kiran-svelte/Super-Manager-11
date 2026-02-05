"""
Ollama Provider - Local LLM inference
Primary provider for privacy and cost (FREE)
"""
import os
import time
import httpx
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
import json

from .base_provider import BaseAIProvider, ProviderConfig, AIResponse, ProviderStatus


class OllamaProvider(BaseAIProvider):
    """
    Ollama local LLM provider.
    Runs models locally - completely free and private.
    """
    
    config = ProviderConfig(
        name="ollama",
        supports_streaming=True,
        supports_vision=True,  # llava, bakllava
        supports_function_calling=True,
        supports_json_mode=True,
        is_local=True,
        is_free=True,
        base_url="http://localhost:11434",
        models=[
            "llama3.2",
            "llama3.2:1b",
            "llama3.1",
            "llama3.1:70b",
            "mistral",
            "mistral-nemo",
            "mixtral",
            "codellama",
            "deepseek-coder-v2",
            "qwen2.5",
            "qwen2.5-coder",
            "phi3",
            "gemma2",
            "llava",  # Vision
            "bakllava"  # Vision
        ],
        default_model="llama3.2",
        timeout=300,  # Local models can be slower
        cost_per_1k_tokens=0.0
    )
    
    def __init__(self):
        super().__init__()
        self.base_url = os.getenv("OLLAMA_BASE_URL", self.config.base_url)
        self._client = httpx.AsyncClient(timeout=self.config.timeout)
        self._available_models: List[str] = []
    
    async def health_check(self) -> bool:
        """Check if Ollama is running and responsive"""
        try:
            response = await self._client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                self._available_models = [m["name"] for m in data.get("models", [])]
                self._status = ProviderStatus.AVAILABLE
                return True
            self._status = ProviderStatus.UNAVAILABLE
            return False
        except Exception as e:
            self._status = ProviderStatus.UNAVAILABLE
            self._record_error(str(e))
            return False
    
    async def list_local_models(self) -> List[Dict[str, Any]]:
        """Get list of locally installed models"""
        try:
            response = await self._client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
            return []
        except Exception:
            return []
    
    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama library"""
        try:
            response = await self._client.post(
                f"{self.base_url}/api/pull",
                json={"name": model},
                timeout=600  # Models can be large
            )
            return response.status_code == 200
        except Exception:
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
        """Generate completion using Ollama"""
        
        model = model or self.config.default_model
        start_time = time.time()
        
        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if json_mode:
            payload["format"] = "json"
        
        # Add any extra options
        if "system" in kwargs:
            payload["system"] = kwargs["system"]
        
        try:
            if stream:
                return self._stream_generate(payload, model, start_time)
            
            response = await self._client.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.config.timeout
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code != 200:
                self._record_error(f"HTTP {response.status_code}")
                raise Exception(f"Ollama error: {response.text}")
            
            data = response.json()
            self._record_latency(latency_ms)
            self._reset_errors()
            
            return AIResponse(
                content=data.get("message", {}).get("content", ""),
                model=model,
                provider="ollama",
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                },
                finish_reason=data.get("done_reason", "stop"),
                latency_ms=latency_ms,
                raw_response=data
            )
            
        except Exception as e:
            self._record_error(str(e))
            raise
    
    async def _stream_generate(
        self,
        payload: Dict[str, Any],
        model: str,
        start_time: float
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama"""
        try:
            async with self._client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.config.timeout
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if data.get("done"):
                                self._record_latency((time.time() - start_time) * 1000)
                                self._reset_errors()
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            self._record_error(str(e))
            raise
    
    async def generate_embedding(
        self,
        text: Union[str, List[str]],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings using Ollama"""
        model = model or "nomic-embed-text"
        
        texts = [text] if isinstance(text, str) else text
        embeddings = []
        
        for t in texts:
            try:
                response = await self._client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": model, "prompt": t}
                )
                if response.status_code == 200:
                    data = response.json()
                    embeddings.append(data.get("embedding", []))
                else:
                    embeddings.append([])
            except Exception:
                embeddings.append([])
        
        return embeddings


# Singleton instance
_ollama_provider: Optional[OllamaProvider] = None


def get_ollama_provider() -> OllamaProvider:
    """Get or create Ollama provider singleton"""
    global _ollama_provider
    if _ollama_provider is None:
        _ollama_provider = OllamaProvider()
    return _ollama_provider
