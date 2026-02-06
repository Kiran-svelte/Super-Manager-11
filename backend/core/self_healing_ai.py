\"\"\"
SELF-HEALING AI CONVERSATION MANAGER
BACKWARD COMPATIBLE WRAPPER - Now uses human_ai.py for truly human-like responses
\"\"\"
# Redirect all imports to the human AI module
from .human_ai import (
    HumanAIManager,
    get_human_ai_manager as get_ai_manager,
    Personality,
    EmotionalState
)

# Aliases for backward compatibility
SelfHealingAIManager = HumanAIManager
IntelligentAIManager = HumanAIManager

__all__ = [
    'SelfHealingAIManager', 
    'IntelligentAIManager',
    'HumanAIManager',
    'get_ai_manager',
    'Personality',
    'EmotionalState'
]
