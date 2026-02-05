"""
AI Providers Module - Multi-provider AI routing with smart fallbacks
Supports: Ollama (local), Zukijourney API, OpenAI, Groq
"""

from .base_provider import BaseAIProvider, ProviderConfig, AIResponse
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .groq_provider import GroqProvider
from .zuki_provider import ZukiProvider
from .router import AIRouter, get_ai_router

__all__ = [
    'BaseAIProvider',
    'ProviderConfig', 
    'AIResponse',
    'OllamaProvider',
    'OpenAIProvider',
    'GroqProvider',
    'ZukiProvider',
    'AIRouter',
    'get_ai_router'
]
