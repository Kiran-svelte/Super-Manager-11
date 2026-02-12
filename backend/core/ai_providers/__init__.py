"""
AI Providers Module - Multi-provider AI routing with smart fallbacks
Supports: Groq, Gemini, SambaNova, Ollama (local), OpenAI, Zukijourney
"""

from .base_provider import BaseAIProvider, ProviderConfig, AIResponse
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .groq_provider import GroqProvider
from .zuki_provider import ZukiProvider
from .sambanova_provider import SambaNovaProvider
from .gemini_provider import GeminiProvider
from .router import AIRouter, get_ai_router

__all__ = [
    'BaseAIProvider',
    'ProviderConfig',
    'AIResponse',
    'OllamaProvider',
    'OpenAIProvider',
    'GroqProvider',
    'ZukiProvider',
    'SambaNovaProvider',
    'GeminiProvider',
    'AIRouter',
    'get_ai_router'
]
