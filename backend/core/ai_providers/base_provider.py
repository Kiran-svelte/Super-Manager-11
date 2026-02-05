"""
Base AI Provider - Abstract interface for all AI providers
Inspired by zukijourney/example-api patterns
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from enum import Enum
import time


class ProviderStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


@dataclass
class ProviderConfig:
    """Configuration for an AI provider"""
    name: str
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_function_calling: bool = True
    supports_json_mode: bool = True
    is_local: bool = False
    is_free: bool = False
    base_url: Optional[str] = None
    models: List[str] = field(default_factory=list)
    default_model: Optional[str] = None
    timeout: int = 120
    max_retries: int = 3
    cost_per_1k_tokens: float = 0.0  # For cost tracking


@dataclass
class AIResponse:
    """Standardized response from any AI provider"""
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    latency_ms: float = 0
    cached: bool = False
    raw_response: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "latency_ms": self.latency_ms,
            "cached": self.cached
        }


class BaseAIProvider(ABC):
    """
    Abstract base class for AI providers.
    All providers must implement these methods.
    """
    config: ProviderConfig
    
    def __init__(self):
        self._status = ProviderStatus.AVAILABLE
        self._last_error: Optional[str] = None
        self._error_count = 0
        self._request_count = 0
        self._total_latency = 0.0
    
    @property
    def status(self) -> ProviderStatus:
        return self._status
    
    @property
    def avg_latency(self) -> float:
        if self._request_count == 0:
            return 0.0
        return self._total_latency / self._request_count
    
    def _record_latency(self, latency_ms: float):
        """Record latency for monitoring"""
        self._request_count += 1
        self._total_latency += latency_ms
    
    def _record_error(self, error: str):
        """Record error and potentially mark provider as unavailable"""
        self._error_count += 1
        self._last_error = error
        if self._error_count >= self.config.max_retries:
            self._status = ProviderStatus.ERROR
    
    def _reset_errors(self):
        """Reset error count on successful request"""
        self._error_count = 0
        self._status = ProviderStatus.AVAILABLE
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available and responding"""
        pass
    
    @abstractmethod
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
        """
        Generate a completion from the AI model.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to provider's default)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            json_mode: Whether to force JSON output
            **kwargs: Additional provider-specific parameters
        
        Returns:
            AIResponse object or async generator for streaming
        """
        pass
    
    @abstractmethod
    async def generate_embedding(
        self,
        text: Union[str, List[str]],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for text(s).
        
        Args:
            text: Single string or list of strings
            model: Embedding model to use
        
        Returns:
            List of embedding vectors
        """
        pass
    
    def get_models(self) -> List[str]:
        """Return list of available models"""
        return self.config.models
    
    def supports_model(self, model: str) -> bool:
        """Check if provider supports a specific model"""
        return model in self.config.models
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics"""
        return {
            "name": self.config.name,
            "status": self._status.value,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "avg_latency_ms": round(self.avg_latency, 2),
            "last_error": self._last_error,
            "is_local": self.config.is_local,
            "is_free": self.config.is_free
        }
