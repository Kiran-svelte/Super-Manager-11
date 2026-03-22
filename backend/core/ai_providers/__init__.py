"""
AI Providers Module - Multi-provider AI routing with smart fallbacks
Supports: OpenRouter (primary), Groq, Gemini, SambaNova, Ollama (local), OpenAI, Zukijourney
"""

from .base_provider import BaseAIProvider, ProviderConfig, AIResponse
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .groq_provider import GroqProvider
from .zuki_provider import ZukiProvider
from .sambanova_provider import SambaNovaProvider
from .gemini_provider import GeminiProvider
from .openrouter_provider import OpenRouterProvider, get_openrouter_provider
from .router import AIRouter, get_ai_router

__all__ = [
    'BaseAIProvider',
    'ProviderConfig',
    'AIResponse',
    'OpenRouterProvider',
    'get_openrouter_provider',
    'OllamaProvider',
    'OpenAIProvider',
    'GroqProvider',
    'ZukiProvider',
    'SambaNovaProvider',
    'GeminiProvider',
    'AIRouter',
    'get_ai_router'
]
