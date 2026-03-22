"""
Chunk 7: Confirmation System Tests
==================================

Tests for README requirements:
- Confirmation workflow for risky actions
- Risk classification: SAFE/RISKY/BLOCKED
- PendingAction management
- User approval workflow
"""

import pytest
from unittest.mock import patch, MagicMock


# =============================================================================
# PendingAction Tests
# =============================================================================

class TestPendingAction:
    """Test PendingAction class"""
    
    def test_pending_action_class_exists(self):
        """PendingAction class should exist"""
        from backend.core.confirmation_manager import PendingAction
        assert PendingAction is not None
    
    def test_pending_action_has_required_fields(self):
        """PendingAction should have required fields"""
        from backend.core.confirmation_manager import PendingAction
        
        action = PendingAction(
            action_type="send_email",
            description="Send email to user@example.com",
            parameters={"to": "user@example.com"},
            plugin="email"
        )
        
        assert action.action_type == "send_email"
        assert action.description == "Send email to user@example.com"
        assert action.parameters == {"to": "user@example.com"}
        assert action.plugin == "email"
    
    def test_pending_action_has_unique_id(self):
        """PendingAction should have unique ID"""
        from backend.core.confirmation_manager import PendingAction
        
        action1 = PendingAction("test", "desc", {}, "plugin")
        action2 = PendingAction("test", "desc", {}, "plugin")
        
        assert action1.id != action2.id
    
    def test_pending_action_default_status_is_pending(self):
        """PendingAction default status should be pending"""
        from backend.core.confirmation_manager import PendingAction
        
        action = PendingAction("test", "desc", {}, "plugin")
        assert action.status == "pending"
    
    def test_pending_action_has_to_dict(self):
        """PendingAction should have to_dict method"""
        from backend.core.confirmation_manager import PendingAction
        
        action = PendingAction("test", "desc", {}, "plugin")
        data = action.to_dict()
        
        assert "id" in data
        assert "action_type" in data
        assert "status" in data


# =============================================================================
# ConfirmationManager Tests
# =============================================================================

class TestConfirmationManager:
    """Test ConfirmationManager class"""
    
    def test_confirmation_manager_exists(self):
        """ConfirmationManager should exist"""
        from backend.core.confirmation_manager import ConfirmationManager
        assert ConfirmationManager is not None
    
    def test_get_confirmation_manager_exists(self):
        """get_confirmation_manager function should exist"""
        from backend.core.confirmation_manager import get_confirmation_manager
        assert get_confirmation_manager is not None
    
    def test_confirmation_manager_has_pending_actions(self):
        """ConfirmationManager should have pending_actions storage"""
        from backend.core.confirmation_manager import ConfirmationManager
        
        manager = ConfirmationManager()
        assert hasattr(manager, 'pending_actions')
        assert isinstance(manager.pending_actions, dict)
    
    def test_create_confirmation_request(self):
        """ConfirmationManager should create confirmation requests"""
        from backend.core.confirmation_manager import ConfirmationManager
        
        manager = ConfirmationManager()
        
        plan = {
            "steps": [
                {"action": "send_email", "parameters": {"to": "user@example.com"}}
            ]
        }
        
        result = manager.create_confirmation_request(
            session_id="test-session",
            plan=plan,
            user_input="Send email"
        )
        
        assert "session_id" in result
        assert "requires_confirmation" in result


# =============================================================================
# RiskClassifier Tests
# =============================================================================

class TestRiskClassifier:
    """Test RiskClassifier for risk levels"""
    
    def test_risk_classifier_exists(self):
        """RiskClassifier should exist"""
        from backend.core.sandbox import RiskClassifier
        assert RiskClassifier is not None
    
    def test_classifier_has_classify_method(self):
        """RiskClassifier should have classify method"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert hasattr(classifier, 'classify')
    
    def test_classify_safe_primitives(self):
        """Classifier should mark safe primitives as safe"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        
        code = 'result = web_search("test query")'
        result = classifier.classify(code)
        
        assert result["risk"] == "safe"
    
    def test_classify_risky_primitives(self):
        """Classifier should mark risky primitives as risky"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        
        code = 'result = run_python("print(1)")'
        result = classifier.classify(code)
        
        assert result["risk"] == "risky"
    
    def test_classify_blocked_patterns(self):
        """Classifier should block forbidden patterns"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        
        code = 'import os\nos.system("rm -rf /")'
        result = classifier.classify(code)
        
        assert result["risk"] == "blocked"
    
    def test_classifier_returns_primitives_used(self):
        """Classifier should return primitives used"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        
        code = 'result = web_search("test")'
        result = classifier.classify(code)
        
        assert "primitives_used" in result


# =============================================================================
# Safe/Risky Primitive Sets Tests
# =============================================================================

class TestPrimitiveSets:
    """Test primitive risk categorization"""
    
    def test_safe_primitives_defined(self):
        """SAFE_PRIMITIVES should be defined"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert hasattr(classifier, 'SAFE_PRIMITIVES')
        assert 'web_search' in classifier.SAFE_PRIMITIVES
        assert 'browse_page' in classifier.SAFE_PRIMITIVES
    
    def test_risky_primitives_defined(self):
        """RISKY_PRIMITIVES should be defined"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert hasattr(classifier, 'RISKY_PRIMITIVES')
        assert 'fill_form' in classifier.RISKY_PRIMITIVES
        assert 'run_python' in classifier.RISKY_PRIMITIVES
    
    def test_generate_image_is_safe(self):
        """generate_image should be in SAFE_PRIMITIVES"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert 'generate_image' in classifier.SAFE_PRIMITIVES
    
    def test_scrape_data_is_safe(self):
        """scrape_data should be in SAFE_PRIMITIVES"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert 'scrape_data' in classifier.SAFE_PRIMITIVES


# =============================================================================
# Forbidden Pattern Tests
# =============================================================================

class TestForbiddenPatterns:
    """Test forbidden pattern detection"""
    
    def test_forbidden_patterns_defined(self):
        """FORBIDDEN_PATTERNS should be defined"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert hasattr(classifier, 'FORBIDDEN_PATTERNS')
        assert len(classifier.FORBIDDEN_PATTERNS) > 0
    
    def test_os_import_blocked(self):
        """import os should be blocked"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        result = classifier.classify("import os")
        
        assert result["risk"] == "blocked"
    
    def test_subprocess_blocked(self):
        """subprocess should be blocked"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        result = classifier.classify("import subprocess")
        
        assert result["risk"] == "blocked"
    
    def test_eval_blocked(self):
        """eval() should be blocked"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        result = classifier.classify('eval("malicious")')
        
        assert result["risk"] == "blocked"
    
    def test_exec_blocked(self):
        """exec() should be blocked"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        result = classifier.classify('exec("malicious")')
        
        assert result["risk"] == "blocked"


# =============================================================================
# Validate Action Tests
# =============================================================================

class TestValidateAction:
    """Test validate_action method"""
    
    def test_validate_action_exists(self):
        """validate_action method should exist"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        assert hasattr(classifier, 'validate_action')
    
    def test_validate_safe_action(self):
        """validate_action should classify safe primitives"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        result = classifier.validate_action("web_search")
        
        assert result["risk"] == "safe"
    
    def test_validate_risky_action(self):
        """validate_action should classify risky primitives"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        result = classifier.validate_action("fill_form")
        
        assert result["risk"] == "risky"


# =============================================================================
# Tool Registry Integration Tests
# =============================================================================

class TestToolRegistryIntegration:
    """Test integration with ToolRegistry for risk levels"""
    
    def test_tool_registry_has_risk_level(self):
        """ToolRegistry tools should have risk_level"""
        from backend.core.tool_registry import ToolDef
        
        tool = ToolDef(
            name="test_tool",
            description="Test tool",
            parameters="param: str",
            returns="result: str",
            source="test",
            risk_level="safe"
        )
        
        assert hasattr(tool, 'risk_level')
        assert tool.risk_level == "safe"
    
    def test_tool_info_has_required_fields(self):
        """ToolDef should have required fields"""
        from backend.core.tool_registry import ToolDef
        
        # Should have these fields
        assert hasattr(ToolDef, '__dataclass_fields__')
        fields = ToolDef.__dataclass_fields__
        
        assert 'name' in fields
        assert 'description' in fields
        assert 'risk_level' in fields


# =============================================================================
# Confirmation Flow Integration Tests  
# =============================================================================

class TestConfirmationFlowIntegration:
    """Test the confirmation workflow"""
    
    def test_risky_action_requires_confirmation(self):
        """Risky actions should require confirmation"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        
        # fill_form is risky
        result = classifier.validate_action("fill_form")
        assert result["risk"] == "risky"
        
        # Risky actions need confirmation
        needs_confirmation = result["risk"] in ("risky",)
        assert needs_confirmation
    
    def test_safe_action_no_confirmation(self):
        """Safe actions should not require confirmation"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        
        result = classifier.validate_action("web_search")
        assert result["risk"] == "safe"
        
        needs_confirmation = result["risk"] in ("risky",)
        assert not needs_confirmation
    
    def test_blocked_action_rejected(self):
        """Blocked actions should be rejected entirely"""
        from backend.core.sandbox import RiskClassifier
        
        classifier = RiskClassifier()
        
        result = classifier.classify("import os")
        assert result["risk"] == "blocked"
        
        # Blocked means rejected, no execution
        should_execute = result["risk"] != "blocked"
        assert not should_execute
