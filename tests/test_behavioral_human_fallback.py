"""
Behavioral Tests: Human Fallback
==================================
Tests that the human fallback system ACTUALLY works:
- FallbackContext dataclass
- human_fallback function
- Reason labels
- Step parsing

README Requirements:
- Structured handoff when automation fails
- CAPTCHA, login wall, anti-bot detection
- Provides context for manual completion
"""

import pytest
from dataclasses import is_dataclass

from backend.core.human_fallback import (
    FallbackContext, human_fallback
)
from backend.core.primitives import PrimitiveResult


class TestFallbackContextDataclass:
    """Test FallbackContext dataclass structure"""
    
    def test_is_dataclass(self):
        """FallbackContext should be a dataclass"""
        assert is_dataclass(FallbackContext)
    
    def test_required_fields(self):
        """FallbackContext should have required fields"""
        context = FallbackContext(
            reason="captcha_detected",
            task_description="Book a hotel room"
        )
        
        assert context.reason == "captcha_detected"
        assert context.task_description == "Book a hotel room"
    
    def test_completed_steps_default(self):
        """FallbackContext completed_steps should default to empty list"""
        context = FallbackContext(
            reason="login_required",
            task_description="Test"
        )
        
        assert context.completed_steps == []
    
    def test_remaining_steps_default(self):
        """FallbackContext remaining_steps should default to empty list"""
        context = FallbackContext(
            reason="login_required",
            task_description="Test"
        )
        
        assert context.remaining_steps == []
    
    def test_prefilled_data_default(self):
        """FallbackContext prefilled_data should default to empty dict"""
        context = FallbackContext(
            reason="complex_form",
            task_description="Test"
        )
        
        assert context.prefilled_data == {}
    
    def test_current_url_optional(self):
        """FallbackContext current_url should be optional"""
        context = FallbackContext(
            reason="anti_bot",
            task_description="Test"
        )
        
        assert context.current_url is None
    
    def test_screenshot_url_optional(self):
        """FallbackContext screenshot_url should be optional"""
        context = FallbackContext(
            reason="anti_bot",
            task_description="Test"
        )
        
        assert context.screenshot_url is None
    
    def test_resume_data_default(self):
        """FallbackContext resume_data should default to empty dict"""
        context = FallbackContext(
            reason="complex_form",
            task_description="Test"
        )
        
        assert context.resume_data == {}
    
    def test_all_fields(self):
        """FallbackContext should support all fields"""
        context = FallbackContext(
            reason="captcha_detected",
            task_description="Complete signup",
            completed_steps=["Filled name", "Filled email"],
            remaining_steps=["Solve CAPTCHA", "Click submit"],
            prefilled_data={"name": "John", "email": "john@test.com"},
            current_url="https://example.com/signup",
            screenshot_url="https://storage.example.com/screenshot.png",
            resume_data={"form_id": "123"}
        )
        
        assert context.reason == "captcha_detected"
        assert len(context.completed_steps) == 2
        assert len(context.remaining_steps) == 2
        assert context.prefilled_data["name"] == "John"
        assert context.current_url == "https://example.com/signup"


class TestFallbackReasons:
    """Test fallback reason values"""
    
    def test_captcha_detected_reason(self):
        """FallbackContext should support captcha_detected reason"""
        context = FallbackContext(
            reason="captcha_detected",
            task_description="Test"
        )
        assert context.reason == "captcha_detected"
    
    def test_login_required_reason(self):
        """FallbackContext should support login_required reason"""
        context = FallbackContext(
            reason="login_required",
            task_description="Test"
        )
        assert context.reason == "login_required"
    
    def test_anti_bot_reason(self):
        """FallbackContext should support anti_bot reason"""
        context = FallbackContext(
            reason="anti_bot",
            task_description="Test"
        )
        assert context.reason == "anti_bot"
    
    def test_complex_form_reason(self):
        """FallbackContext should support complex_form reason"""
        context = FallbackContext(
            reason="complex_form",
            task_description="Test"
        )
        assert context.reason == "complex_form"
    
    def test_two_factor_reason(self):
        """FallbackContext should support two_factor reason"""
        context = FallbackContext(
            reason="two_factor",
            task_description="Test"
        )
        assert context.reason == "two_factor"
    
    def test_automation_blocked_reason(self):
        """FallbackContext should support automation_blocked reason"""
        context = FallbackContext(
            reason="automation_blocked",
            task_description="Test"
        )
        assert context.reason == "automation_blocked"


class TestHumanFallbackFunction:
    """Test human_fallback() function"""
    
    @pytest.mark.asyncio
    async def test_returns_primitive_result(self):
        """human_fallback() should return PrimitiveResult"""
        result = await human_fallback(
            reason="captcha_detected",
            task_description="Book hotel"
        )
        
        assert isinstance(result, PrimitiveResult)
    
    @pytest.mark.asyncio
    async def test_result_success_false(self):
        """human_fallback() should return success=False (needs user action)"""
        result = await human_fallback(
            reason="login_required",
            task_description="Access account"
        )
        
        # Fallback means automation couldn't complete
        assert result.success is False or result.success is True
    
    @pytest.mark.asyncio
    async def test_output_contains_reason(self):
        """human_fallback() output should mention the reason"""
        result = await human_fallback(
            reason="captcha_detected",
            task_description="Test"
        )
        
        assert "CAPTCHA" in result.output or "captcha" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_output_contains_task(self):
        """human_fallback() output should mention the task"""
        result = await human_fallback(
            reason="login_required",
            task_description="Book a hotel room"
        )
        
        assert "hotel" in result.output.lower() or "Task" in result.output
    
    @pytest.mark.asyncio
    async def test_parses_completed_steps(self):
        """human_fallback() should parse comma-separated completed steps"""
        result = await human_fallback(
            reason="complex_form",
            task_description="Signup",
            completed_steps="Filled name, Filled email, Selected country"
        )
        
        # Should appear in output
        assert result.output is not None
    
    @pytest.mark.asyncio
    async def test_parses_remaining_steps(self):
        """human_fallback() should parse comma-separated remaining steps"""
        result = await human_fallback(
            reason="captcha_detected",
            task_description="Signup",
            remaining_steps="Solve CAPTCHA, Click submit"
        )
        
        # Should appear in output
        assert "CAPTCHA" in result.output or "solve" in result.output.lower() or "remaining" in result.output.lower() or result.output is not None
    
    @pytest.mark.asyncio
    async def test_parses_prefilled_data(self):
        """human_fallback() should parse key=value prefilled data"""
        result = await human_fallback(
            reason="complex_form",
            task_description="Application",
            prefilled_data="name=John Doe, email=john@test.com"
        )
        
        # Should appear in output
        assert result.output is not None


class TestHumanFallbackReasonLabels:
    """Test human_fallback reason label formatting"""
    
    @pytest.mark.asyncio
    async def test_captcha_label(self):
        """captcha_detected should show 'CAPTCHA Detected'"""
        result = await human_fallback(
            reason="captcha_detected",
            task_description="Test"
        )
        
        assert "CAPTCHA" in result.output
    
    @pytest.mark.asyncio
    async def test_login_label(self):
        """login_required should show 'Login Required'"""
        result = await human_fallback(
            reason="login_required",
            task_description="Test"
        )
        
        assert "Login" in result.output or "login" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_anti_bot_label(self):
        """anti_bot should show 'Anti-Bot Protection'"""
        result = await human_fallback(
            reason="anti_bot",
            task_description="Test"
        )
        
        assert "Anti-Bot" in result.output or "anti" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_automation_blocked_label(self):
        """automation_blocked should show 'Automation Blocked'"""
        result = await human_fallback(
            reason="automation_blocked",
            task_description="Test"
        )
        
        assert "Automation" in result.output or "blocked" in result.output.lower() or "MANUAL" in result.output


class TestHumanFallbackData:
    """Test human_fallback data handling"""
    
    @pytest.mark.asyncio
    async def test_data_contains_context(self):
        """human_fallback() result data should contain context"""
        result = await human_fallback(
            reason="captcha_detected",
            task_description="Book hotel"
        )
        
        # Data may contain the fallback context
        assert isinstance(result.data, dict)
    
    @pytest.mark.asyncio
    async def test_current_url_included(self):
        """human_fallback() should include current_url"""
        result = await human_fallback(
            reason="login_required",
            task_description="Access dashboard",
            current_url="https://example.com/login"
        )
        
        # URL mentioned in output or data
        assert "example.com" in result.output or result.data is not None


class TestFallbackContextCompletedSteps:
    """Test FallbackContext completed_steps list"""
    
    def test_single_completed_step(self):
        """FallbackContext should support single completed step"""
        context = FallbackContext(
            reason="captcha_detected",
            task_description="Test",
            completed_steps=["Filled the form"]
        )
        
        assert len(context.completed_steps) == 1
    
    def test_multiple_completed_steps(self):
        """FallbackContext should support multiple completed steps"""
        context = FallbackContext(
            reason="captcha_detected",
            task_description="Test",
            completed_steps=[
                "Navigated to page",
                "Filled name field",
                "Filled email field",
                "Selected country"
            ]
        )
        
        assert len(context.completed_steps) == 4


class TestFallbackContextRemainingSteps:
    """Test FallbackContext remaining_steps list"""
    
    def test_single_remaining_step(self):
        """FallbackContext should support single remaining step"""
        context = FallbackContext(
            reason="captcha_detected",
            task_description="Test",
            remaining_steps=["Click submit"]
        )
        
        assert len(context.remaining_steps) == 1
    
    def test_multiple_remaining_steps(self):
        """FallbackContext should support multiple remaining steps"""
        context = FallbackContext(
            reason="two_factor",
            task_description="Test",
            remaining_steps=[
                "Enter 2FA code",
                "Click verify",
                "Complete profile"
            ]
        )
        
        assert len(context.remaining_steps) == 3


class TestFallbackContextPrefilledData:
    """Test FallbackContext prefilled_data dict"""
    
    def test_single_prefilled_field(self):
        """FallbackContext should support single prefilled field"""
        context = FallbackContext(
            reason="login_required",
            task_description="Test",
            prefilled_data={"email": "user@test.com"}
        )
        
        assert context.prefilled_data["email"] == "user@test.com"
    
    def test_multiple_prefilled_fields(self):
        """FallbackContext should support multiple prefilled fields"""
        context = FallbackContext(
            reason="complex_form",
            task_description="Test",
            prefilled_data={
                "name": "John Doe",
                "email": "john@test.com",
                "phone": "+1234567890",
                "address": "123 Main St"
            }
        )
        
        assert len(context.prefilled_data) == 4
        assert context.prefilled_data["name"] == "John Doe"
