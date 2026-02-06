"""
INTELLIGENT AI MANAGER
Wrapper module - now redirects to human_ai.py for truly human-like responses
"""
# Redirect all imports to the new human AI module
from .human_ai import (
    HumanAIManager, 
    get_human_ai_manager as get_ai_manager,
    Personality,
    EmotionalState,
    Emotion
)

# Backward compatible aliases
IntelligentAIManager = HumanAIManager
SelfHealingAIManager = HumanAIManager

__all__ = [
    'IntelligentAIManager', 
    'SelfHealingAIManager', 
    'HumanAIManager',
    'get_ai_manager',
    'Personality',
    'EmotionalState',
    'Emotion'
]
