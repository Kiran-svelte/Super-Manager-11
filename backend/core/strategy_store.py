"""
Strategy Store - Learn From Success (Layer 10: Learning Loop)
===============================================================
Caches successful task execution patterns for faster repeat execution.
Implements README requirements:
- Cache successful strategies
- Confidence scoring with decay
- Feedback → improvement loop
- Preference persistence

Uses JSON file storage + optional Supabase for cloud sync.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# Confidence scoring parameters
INITIAL_CONFIDENCE = 0.5
MAX_CONFIDENCE = 1.0
MIN_CONFIDENCE = 0.1
CONFIDENCE_BOOST_POSITIVE = 0.15  # Thumbs up
CONFIDENCE_DECAY_NEGATIVE = 0.25  # Thumbs down
CONFIDENCE_DECAY_UNUSED = 0.05    # Per day unused
DAYS_UNTIL_DECAY_STARTS = 7       # Grace period


@dataclass
class Step:
    """A single step in a strategy"""
    step_type: str  # "action", "code", "ask"
    description: str
    primitive_or_code: str  # primitive name or code snippet
    params_template: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Strategy:
    """A cached task execution strategy with confidence scoring"""
    task_type: str  # e.g., "book_resort", "search_compare", "send_email"
    keywords: List[str]  # keywords that trigger this strategy
    steps: List[Step]
    success_count: int = 0
    failure_count: int = 0
    confidence: float = INITIAL_CONFIDENCE  # Learning confidence score
    positive_feedback: int = 0  # Thumbs up count
    negative_feedback: int = 0  # Thumbs down count
    last_used: str = ""
    last_feedback: str = ""
    created: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Strategy":
        steps = [Step(**s) for s in data.get("steps", [])]
        return cls(
            task_type=data.get("task_type", ""),
            keywords=data.get("keywords", []),
            steps=steps,
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            confidence=data.get("confidence", INITIAL_CONFIDENCE),
            positive_feedback=data.get("positive_feedback", 0),
            negative_feedback=data.get("negative_feedback", 0),
            last_used=data.get("last_used", ""),
            last_feedback=data.get("last_feedback", ""),
            created=data.get("created", ""),
        )
    
    def apply_decay(self):
        """Apply confidence decay based on unused time"""
        if not self.last_used:
            return
        
        try:
            last_used_dt = datetime.fromisoformat(self.last_used)
            days_since = (datetime.now() - last_used_dt).days
            
            if days_since > DAYS_UNTIL_DECAY_STARTS:
                decay_days = days_since - DAYS_UNTIL_DECAY_STARTS
                decay_amount = decay_days * CONFIDENCE_DECAY_UNUSED
                self.confidence = max(MIN_CONFIDENCE, self.confidence - decay_amount)
        except Exception:
            pass
    
    def record_success(self):
        """Record successful execution"""
        self.success_count += 1
        self.last_used = datetime.now().isoformat()
        # Slight confidence boost on success
        self.confidence = min(MAX_CONFIDENCE, self.confidence + 0.02)
    
    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.confidence = max(MIN_CONFIDENCE, self.confidence - 0.1)
    
    def record_feedback(self, positive: bool):
        """Record user feedback (thumbs up/down)"""
        self.last_feedback = datetime.now().isoformat()
        if positive:
            self.positive_feedback += 1
            self.confidence = min(MAX_CONFIDENCE, self.confidence + CONFIDENCE_BOOST_POSITIVE)
        else:
            self.negative_feedback += 1
            self.confidence = max(MIN_CONFIDENCE, self.confidence - CONFIDENCE_DECAY_NEGATIVE)


class StrategyStore:
    """
    Cache successful task patterns for faster repeat execution.
    
    Implements README Learning Loop requirements:
    - Cache successful strategies
    - Confidence scoring (decays over time, boosted by positive feedback)
    - Feedback integration (thumbs up/down → confidence adjustment)
    - Strategy pruning (low confidence → eventually removed)
    """

    def __init__(self, path: str = None):
        if path is None:
            # Default to backend/data/strategies.json
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            path = os.path.join(data_dir, "strategies.json")

        self.path = path
        self.strategies: List[Strategy] = self._load()
        self._apply_decay_to_all()  # Apply decay on load

    def _load(self) -> List[Strategy]:
        """Load strategies from JSON file"""
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Strategy.from_dict(s) for s in data]
        except Exception as e:
            logger.error(f"Failed to load strategies: {e}")
            return []
    
    def _apply_decay_to_all(self):
        """Apply confidence decay to all strategies and prune dead ones"""
        for strategy in self.strategies:
            strategy.apply_decay()
        
        # Remove strategies with very low confidence (essentially forgotten)
        original_count = len(self.strategies)
        self.strategies = [s for s in self.strategies if s.confidence > MIN_CONFIDENCE]
        pruned = original_count - len(self.strategies)
        
        if pruned > 0:
            logger.info(f"[StrategyStore] Pruned {pruned} low-confidence strategies")
            self._save()

    def _save(self):
        """Save strategies to JSON file"""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([s.to_dict() for s in self.strategies], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save strategies: {e}")

    def find_similar(self, task_description: str, min_confidence: float = 0.3) -> Optional[Strategy]:
        """
        Find a matching strategy based on keyword overlap.
        Only returns strategies above minimum confidence threshold.
        """
        if not self.strategies:
            return None

        task_words = set(task_description.lower().split())
        best_match = None
        best_score = 0

        for strategy in self.strategies:
            # Skip low-confidence strategies
            if strategy.confidence < min_confidence:
                continue
                
            # Count keyword matches
            matches = sum(1 for kw in strategy.keywords if kw.lower() in task_words)
            
            # Weight by confidence - higher confidence strategies rank higher
            weighted_score = matches * strategy.confidence
            
            # Require at least 2 keyword matches for relevance
            if matches >= 2 and weighted_score > best_score:
                best_score = weighted_score
                best_match = strategy

        return best_match

    def save_strategy(
        self,
        task_type: str,
        keywords: List[str],
        steps: List[Dict[str, Any]],
    ):
        """
        Save a successful task execution as a strategy.
        If a similar strategy exists, update it instead of creating a new one.
        """
        # Check for existing strategy with same task_type
        existing = next((s for s in self.strategies if s.task_type == task_type), None)

        if existing:
            existing.record_success()  # Use new method with confidence boost
            # Update keywords (union)
            existing.keywords = list(set(existing.keywords + keywords))
        else:
            strategy = Strategy(
                task_type=task_type,
                keywords=keywords,
                steps=[Step(**s) if isinstance(s, dict) else s for s in steps],
                success_count=1,
                confidence=INITIAL_CONFIDENCE,
                last_used=datetime.now().isoformat(),
                created=datetime.now().isoformat(),
            )
            self.strategies.append(strategy)

        self._save()
        logger.info(f"Strategy saved: {task_type} (confidence: {existing.confidence if existing else INITIAL_CONFIDENCE:.2f})")
    
    def record_failure(self, task_type: str):
        """Record a failed execution for a strategy"""
        strategy = next((s for s in self.strategies if s.task_type == task_type), None)
        if strategy:
            strategy.record_failure()
            self._save()
            logger.info(f"Strategy failure recorded: {task_type} (confidence: {strategy.confidence:.2f})")
    
    def apply_feedback(self, task_type: str, positive: bool):
        """
        Apply user feedback to a strategy.
        Thumbs up → increases confidence
        Thumbs down → decreases confidence
        """
        strategy = next((s for s in self.strategies if s.task_type == task_type), None)
        if strategy:
            strategy.record_feedback(positive)
            self._save()
            feedback_type = "positive" if positive else "negative"
            logger.info(f"Strategy {feedback_type} feedback: {task_type} (confidence: {strategy.confidence:.2f})")
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get learning statistics for monitoring"""
        if not self.strategies:
            return {
                "total_strategies": 0,
                "avg_confidence": 0,
                "total_successes": 0,
                "total_failures": 0
            }
        
        return {
            "total_strategies": len(self.strategies),
            "avg_confidence": sum(s.confidence for s in self.strategies) / len(self.strategies),
            "high_confidence_count": len([s for s in self.strategies if s.confidence >= 0.7]),
            "low_confidence_count": len([s for s in self.strategies if s.confidence < 0.3]),
            "total_successes": sum(s.success_count for s in self.strategies),
            "total_failures": sum(s.failure_count for s in self.strategies),
            "positive_feedback": sum(s.positive_feedback for s in self.strategies),
            "negative_feedback": sum(s.negative_feedback for s in self.strategies),
        }

    def get_strategy_hint(self, task_description: str) -> str:
        """
        Get a hint from cached strategies that can help the LLM.
        Returns a text hint or empty string.
        Only uses high-confidence strategies.
        """
        strategy = self.find_similar(task_description, min_confidence=0.4)
        if not strategy:
            return ""

        confidence_label = "high" if strategy.confidence >= 0.7 else "medium" if strategy.confidence >= 0.4 else "low"
        
        lines = [f"STRATEGY HINT ({confidence_label} confidence: {strategy.confidence:.0%}):"]
        lines.append(f"Previously successful pattern for '{strategy.task_type}':")
        for i, step in enumerate(strategy.steps, 1):
            lines.append(f"  Step {i}: {step.description} ({step.step_type})")
        lines.append(f"  Success rate: {strategy.success_count}/{strategy.success_count + strategy.failure_count}")
        lines.append("You can follow this pattern or adapt it as needed.")

        return "\n".join(lines)
