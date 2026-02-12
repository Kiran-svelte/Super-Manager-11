"""
Strategy Store - Learn From Success
=====================================
Caches successful task execution patterns for faster repeat execution.
Uses simple JSON file storage - no database needed.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class Step:
    """A single step in a strategy"""
    step_type: str  # "action", "code", "ask"
    description: str
    primitive_or_code: str  # primitive name or code snippet
    params_template: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Strategy:
    """A cached task execution strategy"""
    task_type: str  # e.g., "book_resort", "search_compare", "send_email"
    keywords: List[str]  # keywords that trigger this strategy
    steps: List[Step]
    success_count: int = 0
    last_used: str = ""
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
            last_used=data.get("last_used", ""),
            created=data.get("created", ""),
        )


class StrategyStore:
    """
    Cache successful task patterns for faster repeat execution.
    Simple JSON file storage.
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

    def _save(self):
        """Save strategies to JSON file"""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([s.to_dict() for s in self.strategies], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save strategies: {e}")

    def find_similar(self, task_description: str) -> Optional[Strategy]:
        """
        Find a matching strategy based on keyword overlap.
        Returns the best matching strategy if found.
        """
        if not self.strategies:
            return None

        task_words = set(task_description.lower().split())
        best_match = None
        best_score = 0

        for strategy in self.strategies:
            # Count keyword matches
            matches = sum(1 for kw in strategy.keywords if kw.lower() in task_words)
            # Require at least 2 keyword matches for relevance
            if matches >= 2 and matches > best_score:
                best_score = matches
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
            existing.success_count += 1
            existing.last_used = datetime.now().isoformat()
            # Update keywords (union)
            existing.keywords = list(set(existing.keywords + keywords))
        else:
            strategy = Strategy(
                task_type=task_type,
                keywords=keywords,
                steps=[Step(**s) if isinstance(s, dict) else s for s in steps],
                success_count=1,
                last_used=datetime.now().isoformat(),
                created=datetime.now().isoformat(),
            )
            self.strategies.append(strategy)

        self._save()
        logger.info(f"Strategy saved: {task_type} (keywords: {keywords})")

    def get_strategy_hint(self, task_description: str) -> str:
        """
        Get a hint from cached strategies that can help the LLM.
        Returns a text hint or empty string.
        """
        strategy = self.find_similar(task_description)
        if not strategy:
            return ""

        lines = [f"STRATEGY HINT (from previous successful execution of '{strategy.task_type}'):"]
        for i, step in enumerate(strategy.steps, 1):
            lines.append(f"  Step {i}: {step.description} ({step.step_type})")
        lines.append(f"  (Used successfully {strategy.success_count} times)")
        lines.append("You can follow this pattern or adapt it as needed.")

        return "\n".join(lines)
