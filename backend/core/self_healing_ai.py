"""
SELF-HEALING AI CONVERSATION MANAGER
BACKWARD COMPATIBLE WRAPPER - Now uses intelligent_ai.py with Ollama support
"""
# Redirect all imports to the new intelligent AI module
from .intelligent_ai import IntelligentAIManager, get_ai_manager

# Alias for backward compatibility
SelfHealingAIManager = IntelligentAIManager

__all__ = ['SelfHealingAIManager', 'get_ai_manager', 'IntelligentAIManager']

