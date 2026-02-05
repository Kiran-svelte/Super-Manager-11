"""
AI Router - Intelligent provider selection with automatic fallback
Routes requests to optimal provider based on:
- Availability
- Cost (prefers free/local)
- Latency
- Capability requirements
"""
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from enum import Enum
import logging

from .base_provider import BaseAIProvider, AIResponse, ProviderStatus
from .ollama_provider import OllamaProvider, get_ollama_provider
from .openai_provider import OpenAIProvider, get_openai_provider
from .groq_provider import GroqProvider, get_groq_provider
from .zuki_provider import ZukiProvider, get_zuki_provider

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Provider selection strategy"""
    COST_OPTIMIZED = "cost"      # Prefer free/local first
    SPEED_OPTIMIZED = "speed"    # Prefer fastest provider
    QUALITY_OPTIMIZED = "quality"  # Prefer most capable
    ROUND_ROBIN = "round_robin"  # Distribute load


class AIRouter:
    """
    Intelligent AI router with automatic failover.
    
    Priority order (COST_OPTIMIZED - default):
    1. Ollama (local, free, private)
    2. Groq (fast, free tier)
    3. Zuki (free API)
    4. OpenAI (paid, most capable)
    """
    
    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.COST_OPTIMIZED):
        self.strategy = strategy
        self._providers: Dict[str, BaseAIProvider] = {}
        self._initialized = False
        self._cache: Dict[str, AIResponse] = {}  # Simple response cache
        self._cache_ttl = 3600  # 1 hour cache
    
    async def initialize(self):
        """Initialize all providers and check availability"""
        if self._initialized:
            return
        
        logger.info("[AI_ROUTER] Initializing providers...")
        
        # Initialize providers in priority order
        self._providers = {
            "ollama": get_ollama_provider(),
            "groq": get_groq_provider(),
            "zuki": get_zuki_provider(),
            "openai": get_openai_provider()
        }
        
        # Check health of all providers concurrently
        health_checks = []
        for name, provider in self._providers.items():
            health_checks.append(self._check_provider_health(name, provider))
        
        await asyncio.gather(*health_checks, return_exceptions=True)
        
        self._initialized = True
        
        # Log available providers
        available = [n for n, p in self._providers.items() if p.status == ProviderStatus.AVAILABLE]
        logger.info(f"[AI_ROUTER] Available providers: {available}")
    
    async def _check_provider_health(self, name: str, provider: BaseAIProvider):
        """Check single provider health"""
        try:
            is_healthy = await provider.health_check()
            status = "✅" if is_healthy else "❌"
            logger.info(f"[AI_ROUTER] {name}: {status}")
        except Exception as e:
            logger.warning(f"[AI_ROUTER] {name}: ❌ ({e})")
    
    def _get_provider_priority(self) -> List[str]:
        """Get provider priority based on strategy"""
        if self.strategy == RoutingStrategy.COST_OPTIMIZED:
            return ["ollama", "groq", "zuki", "openai"]
        elif self.strategy == RoutingStrategy.SPEED_OPTIMIZED:
            # Sort by average latency
            providers = list(self._providers.items())
            providers.sort(key=lambda x: x[1].avg_latency if x[1].avg_latency > 0 else float('inf'))
            return [p[0] for p in providers]
        elif self.strategy == RoutingStrategy.QUALITY_OPTIMIZED:
            return ["openai", "groq", "zuki", "ollama"]
        else:
            return list(self._providers.keys())
    
    def _select_provider(
        self,
        required_capabilities: Optional[List[str]] = None,
        preferred_model: Optional[str] = None
    ) -> Optional[BaseAIProvider]:
        """Select best available provider"""
        
        priority = self._get_provider_priority()
        
        for provider_name in priority:
            provider = self._providers.get(provider_name)
            if not provider or provider.status != ProviderStatus.AVAILABLE:
                continue
            
            # Check model support
            if preferred_model and not provider.supports_model(preferred_model):
                continue
            
            # Check capabilities
            if required_capabilities:
                config = provider.config
                if "vision" in required_capabilities and not config.supports_vision:
                    continue
                if "streaming" in required_capabilities and not config.supports_streaming:
                    continue
                if "function_calling" in required_capabilities and not config.supports_function_calling:
                    continue
            
            return provider
        
        return None
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        json_mode: bool = False,
        required_capabilities: Optional[List[str]] = None,
        use_cache: bool = True,
        **kwargs
    ) -> Union[AIResponse, AsyncGenerator[str, None]]:
        """
        Generate AI response with automatic failover.
        
        Tries providers in priority order until one succeeds.
        """
        if not self._initialized:
            await self.initialize()
        
        # Simple cache check for non-streaming requests
        if use_cache and not stream:
            cache_key = f"{messages[-1].get('content', '')}:{model}:{temperature}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                cached.cached = True
                return cached
        
        errors = []
        priority = self._get_provider_priority()
        
        for provider_name in priority:
            provider = self._providers.get(provider_name)
            if not provider or provider.status != ProviderStatus.AVAILABLE:
                continue
            
            # Check capability requirements
            if required_capabilities:
                config = provider.config
                skip = False
                for cap in required_capabilities:
                    if cap == "vision" and not config.supports_vision:
                        skip = True
                    if cap == "function_calling" and not config.supports_function_calling:
                        skip = True
                if skip:
                    continue
            
            # Try model on this provider
            actual_model = model
            if model and not provider.supports_model(model):
                # Use provider's default model
                actual_model = provider.config.default_model
            
            try:
                logger.info(f"[AI_ROUTER] Trying {provider_name} with model {actual_model}")
                
                result = await provider.generate(
                    messages=messages,
                    model=actual_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    json_mode=json_mode,
                    **kwargs
                )
                
                # Cache successful non-streaming responses
                if use_cache and not stream and isinstance(result, AIResponse):
                    cache_key = f"{messages[-1].get('content', '')}:{model}:{temperature}"
                    self._cache[cache_key] = result
                
                return result
                
            except Exception as e:
                error_msg = f"{provider_name}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"[AI_ROUTER] {error_msg}")
                continue
        
        # All providers failed
        raise Exception(f"All AI providers failed: {'; '.join(errors)}")
    
    async def generate_embedding(
        self,
        text: Union[str, List[str]],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings with fallback"""
        if not self._initialized:
            await self.initialize()
        
        # Embedding priority: Ollama > OpenAI > Zuki (Groq doesn't support)
        embedding_priority = ["ollama", "openai", "zuki"]
        
        for provider_name in embedding_priority:
            provider = self._providers.get(provider_name)
            if not provider or provider.status != ProviderStatus.AVAILABLE:
                continue
            
            try:
                return await provider.generate_embedding(text, model)
            except NotImplementedError:
                continue
            except Exception as e:
                logger.warning(f"[AI_ROUTER] Embedding failed on {provider_name}: {e}")
                continue
        
        raise Exception("No embedding provider available")
    
    def get_status(self) -> Dict[str, Any]:
        """Get router and all providers status"""
        return {
            "initialized": self._initialized,
            "strategy": self.strategy.value,
            "cache_size": len(self._cache),
            "providers": {
                name: provider.get_stats()
                for name, provider in self._providers.items()
            }
        }
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return [
            name for name, provider in self._providers.items()
            if provider.status == ProviderStatus.AVAILABLE
        ]
    
    def get_all_models(self) -> Dict[str, List[str]]:
        """Get all models from all providers"""
        return {
            name: provider.config.models
            for name, provider in self._providers.items()
        }


# Global router singleton
_ai_router: Optional[AIRouter] = None


def get_ai_router() -> AIRouter:
    """Get or create the global AI router"""
    global _ai_router
    if _ai_router is None:
        _ai_router = AIRouter(strategy=RoutingStrategy.COST_OPTIMIZED)
    return _ai_router


async def quick_generate(
    prompt: str,
    system: str = "You are a helpful AI assistant.",
    json_mode: bool = False,
    **kwargs
) -> str:
    """
    Quick helper for simple generation.
    
    Usage:
        response = await quick_generate("What is 2+2?")
        data = await quick_generate("List 3 colors", json_mode=True)
    """
    router = get_ai_router()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    
    result = await router.generate(
        messages=messages,
        json_mode=json_mode,
        **kwargs
    )
    
    if isinstance(result, AIResponse):
        return result.content
    else:
        # Streaming - collect all chunks
        chunks = []
        async for chunk in result:
            chunks.append(chunk)
        return "".join(chunks)
