"""
Chunk 9: Memory & Learning Tests
=================================

Tests for README requirements:
- User memory/preferences storage
- Strategy caching for faster repeat execution
- Confidence scoring
- Learning from successful patterns
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock


# =============================================================================
# MemoryManager Tests
# =============================================================================

class TestMemoryManager:
    """Test MemoryManager class"""
    
    def test_memory_manager_exists(self):
        """MemoryManager should exist"""
        from backend.core.memory import MemoryManager
        assert MemoryManager is not None
    
    def test_memory_manager_has_cache(self):
        """MemoryManager should have cache"""
        from backend.core.memory import MemoryManager
        
        manager = MemoryManager()
        assert hasattr(manager, 'cache')
        assert isinstance(manager.cache, dict)
    
    def test_memory_manager_has_get_memory(self):
        """MemoryManager should have get_memory method"""
        from backend.core.memory import MemoryManager
        
        manager = MemoryManager()
        assert hasattr(manager, 'get_memory')
    
    def test_memory_manager_has_set_memory(self):
        """MemoryManager should have set_memory method"""
        from backend.core.memory import MemoryManager
        
        manager = MemoryManager()
        assert hasattr(manager, 'set_memory')
    
    def test_memory_manager_has_get_user_preferences(self):
        """MemoryManager should have get_user_preferences method"""
        from backend.core.memory import MemoryManager
        
        manager = MemoryManager()
        assert hasattr(manager, 'get_user_preferences')


# =============================================================================
# StrategyStore Tests
# =============================================================================

class TestStrategyStore:
    """Test StrategyStore class"""
    
    def test_strategy_store_exists(self):
        """StrategyStore should exist"""
        from backend.core.strategy_store import StrategyStore
        assert StrategyStore is not None
    
    def test_strategy_store_has_path(self):
        """StrategyStore should have configurable path"""
        from backend.core.strategy_store import StrategyStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_strategies.json")
            store = StrategyStore(path=path)
            
            assert store.path == path
    
    def test_strategy_store_has_find_similar(self):
        """StrategyStore should have find_similar method"""
        from backend.core.strategy_store import StrategyStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_strategies.json")
            store = StrategyStore(path=path)
            
            assert hasattr(store, 'find_similar')
    
    def test_strategy_store_has_save_strategy(self):
        """StrategyStore should have save_strategy method"""
        from backend.core.strategy_store import StrategyStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_strategies.json")
            store = StrategyStore(path=path)
            
            assert hasattr(store, 'save_strategy')


# =============================================================================
# Strategy Dataclass Tests
# =============================================================================

class TestStrategyDataclass:
    """Test Strategy dataclass"""
    
    def test_strategy_exists(self):
        """Strategy dataclass should exist"""
        from backend.core.strategy_store import Strategy
        assert Strategy is not None
    
    def test_strategy_has_required_fields(self):
        """Strategy should have required fields"""
        from backend.core.strategy_store import Strategy
        
        strategy = Strategy(
            task_type="book_hotel",
            keywords=["book", "hotel", "reservation"],
            steps=[]
        )
        
        assert strategy.task_type == "book_hotel"
        assert strategy.keywords == ["book", "hotel", "reservation"]
    
    def test_strategy_has_success_count(self):
        """Strategy should track success count"""
        from backend.core.strategy_store import Strategy
        
        strategy = Strategy(
            task_type="test",
            keywords=[],
            steps=[],
            success_count=5
        )
        
        assert strategy.success_count == 5
    
    def test_strategy_has_to_dict(self):
        """Strategy should have to_dict method"""
        from backend.core.strategy_store import Strategy
        
        strategy = Strategy(
            task_type="test",
            keywords=["test"],
            steps=[]
        )
        
        data = strategy.to_dict()
        assert "task_type" in data
        assert "keywords" in data
    
    def test_strategy_from_dict(self):
        """Strategy should have from_dict classmethod"""
        from backend.core.strategy_store import Strategy
        
        data = {
            "task_type": "search",
            "keywords": ["search", "find"],
            "steps": [],
            "success_count": 3
        }
        
        strategy = Strategy.from_dict(data)
        assert strategy.task_type == "search"
        assert strategy.success_count == 3


# =============================================================================
# Step Dataclass Tests
# =============================================================================

class TestStepDataclass:
    """Test Step dataclass"""
    
    def test_step_exists(self):
        """Step dataclass should exist"""
        from backend.core.strategy_store import Step
        assert Step is not None
    
    def test_step_has_required_fields(self):
        """Step should have required fields"""
        from backend.core.strategy_store import Step
        
        step = Step(
            step_type="action",
            description="Search for hotels",
            primitive_or_code="web_search"
        )
        
        assert step.step_type == "action"
        assert step.description == "Search for hotels"
        assert step.primitive_or_code == "web_search"


# =============================================================================
# Confidence Score Tests
# =============================================================================

class TestConfidenceScoring:
    """Test confidence scoring"""
    
    def test_intent_parser_has_confidence(self):
        """Intent parser should calculate confidence"""
        from backend.core.intent_parser import IntentParser
        
        parser = IntentParser()
        assert hasattr(parser, '_calculate_confidence')
    
    def test_intent_classifier_has_confidence(self):
        """Intent classifier should return confidence"""
        from backend.core.intent_classifier import IntentClassifier
        
        classifier = IntentClassifier()
        result = classifier.classify("book a hotel in Paris")
        
        assert "confidence" in result


# =============================================================================
# Learning Integration Tests
# =============================================================================

class TestLearningIntegration:
    """Test learning from successful patterns"""
    
    def test_strategy_matching(self):
        """StrategyStore should find matching strategies"""
        from backend.core.strategy_store import StrategyStore, Strategy, Step
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_strategies.json")
            store = StrategyStore(path=path)
            
            # Add a strategy
            store.strategies = [
                Strategy(
                    task_type="book_hotel",
                    keywords=["book", "hotel", "reservation", "stay"],
                    steps=[Step("action", "Search hotels", "web_search")],
                    success_count=10
                )
            ]
            
            # Should find matching
            result = store.find_similar("I want to book a hotel")
            assert result is not None
            assert result.task_type == "book_hotel"
    
    def test_no_match_when_insufficient_keywords(self):
        """No match when insufficient keyword overlap"""
        from backend.core.strategy_store import StrategyStore, Strategy, Step
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_strategies.json")
            store = StrategyStore(path=path)
            
            store.strategies = [
                Strategy(
                    task_type="book_hotel",
                    keywords=["book", "hotel", "reservation"],
                    steps=[],
                    success_count=1
                )
            ]
            
            # Only one keyword match - not enough
            result = store.find_similar("book a flight")
            assert result is None


# =============================================================================
# Teaching Mode Tests
# =============================================================================

class TestTeachingMode:
    """Test teaching/workflow learning mode"""
    
    def test_teaching_module_exists(self):
        """Teaching mode module should exist"""
        from backend.core import teaching_mode
        assert teaching_mode is not None
    
    def test_workflow_step_exists(self):
        """WorkflowStep dataclass should exist"""
        from backend.core.teaching_mode import WorkflowStep
        assert WorkflowStep is not None
    
    def test_learned_workflow_exists(self):
        """WorkflowDef dataclass should exist"""
        from backend.core.teaching_mode import WorkflowDef
        assert WorkflowDef is not None


# =============================================================================
# Memory Persistence Tests
# =============================================================================

class TestMemoryPersistence:
    """Test memory persistence"""
    
    def test_strategy_store_saves_to_file(self):
        """StrategyStore should save to JSON file"""
        from backend.core.strategy_store import StrategyStore, Strategy
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_strategies.json")
            store = StrategyStore(path=path)
            
            # Add strategy and save
            store.strategies = [
                Strategy(
                    task_type="test",
                    keywords=["test"],
                    steps=[],
                    success_count=1
                )
            ]
            store._save()
            
            # File should exist
            assert os.path.exists(path)
    
    def test_strategy_store_loads_from_file(self):
        """StrategyStore should load from JSON file"""
        from backend.core.strategy_store import StrategyStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_strategies.json")
            
            # Write test data
            test_data = [
                {
                    "task_type": "search",
                    "keywords": ["find", "search"],
                    "steps": [],
                    "success_count": 5,
                    "last_used": "",
                    "created": ""
                }
            ]
            with open(path, "w") as f:
                json.dump(test_data, f)
            
            # Load
            store = StrategyStore(path=path)
            
            assert len(store.strategies) == 1
            assert store.strategies[0].task_type == "search"
