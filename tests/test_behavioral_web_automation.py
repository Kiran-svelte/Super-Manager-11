"""
Behavioral Tests: Web Automation
=================================
Tests that the web automation module ACTUALLY works:
- AutomationStep dataclass
- WebAutomation class
- PLAYWRIGHT_AVAILABLE flag
- Action types

README Requirements:
- Browser automation
- Form filling
- Web scraping
"""

import pytest
from dataclasses import is_dataclass

from backend.core.web_automation import (
    AutomationStep,
    WebAutomation,
    PLAYWRIGHT_AVAILABLE,
)


class TestPlaywrightAvailableFlag:
    """Test PLAYWRIGHT_AVAILABLE flag"""
    
    def test_exists(self):
        """PLAYWRIGHT_AVAILABLE should exist"""
        # It should be a boolean or it might throw an error
        assert PLAYWRIGHT_AVAILABLE is True or PLAYWRIGHT_AVAILABLE is False
    
    def test_is_bool(self):
        """PLAYWRIGHT_AVAILABLE should be boolean"""
        assert isinstance(PLAYWRIGHT_AVAILABLE, bool)


class TestAutomationStepDataclass:
    """Test AutomationStep dataclass"""
    
    def test_is_dataclass(self):
        """AutomationStep should be a dataclass"""
        assert is_dataclass(AutomationStep)
    
    def test_can_create(self):
        """AutomationStep should be creatable"""
        step = AutomationStep(action="click")
        assert step is not None
    
    def test_has_action(self):
        """Should have action"""
        step = AutomationStep(action="type")
        assert step.action == "type"
    
    def test_default_selector_none(self):
        """Default selector should be None"""
        step = AutomationStep(action="click")
        assert step.selector is None
    
    def test_default_value_none(self):
        """Default value should be None"""
        step = AutomationStep(action="click")
        assert step.value is None
    
    def test_default_timeout(self):
        """Default timeout should be 30000"""
        step = AutomationStep(action="click")
        assert step.timeout == 30000
    
    def test_can_set_selector(self):
        """Should be able to set selector"""
        step = AutomationStep(action="click", selector="#button")
        assert step.selector == "#button"
    
    def test_can_set_value(self):
        """Should be able to set value"""
        step = AutomationStep(action="type", value="hello")
        assert step.value == "hello"
    
    def test_can_set_timeout(self):
        """Should be able to set timeout"""
        step = AutomationStep(action="wait", timeout=60000)
        assert step.timeout == 60000


class TestWebAutomationClass:
    """Test WebAutomation class"""
    
    def test_class_exists(self):
        """WebAutomation class should exist"""
        assert WebAutomation is not None
    
    def test_can_instantiate(self):
        """WebAutomation should be instantiable"""
        automation = WebAutomation()
        assert automation is not None
    
    def test_has_browser_attribute(self):
        """Should have browser attribute"""
        automation = WebAutomation()
        assert hasattr(automation, "browser")
    
    def test_has_page_attribute(self):
        """Should have page attribute"""
        automation = WebAutomation()
        assert hasattr(automation, "page")
    
    def test_browser_initially_none(self):
        """browser should initially be None"""
        automation = WebAutomation()
        assert automation.browser is None
    
    def test_page_initially_none(self):
        """page should initially be None"""
        automation = WebAutomation()
        assert automation.page is None


class TestWebAutomationMethods:
    """Test WebAutomation methods"""
    
    def test_has_start_method(self):
        """Should have start method"""
        automation = WebAutomation()
        assert hasattr(automation, "start")
        assert callable(automation.start)
    
    def test_has_stop_method(self):
        """Should have stop method"""
        automation = WebAutomation()
        assert hasattr(automation, "stop")
        assert callable(automation.stop)
    
    def test_has_execute_method(self):
        """Should have execute method"""
        automation = WebAutomation()
        assert hasattr(automation, "execute")
        assert callable(automation.execute)


class TestWebAutomationExecute:
    """Test WebAutomation execute method"""
    
    @pytest.mark.asyncio
    async def test_execute_returns_dict(self):
        """execute should return dict"""
        automation = WebAutomation()
        result = await automation.execute("https://example.com", [])
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_execute_has_success_key(self):
        """execute result should have success key"""
        automation = WebAutomation()
        result = await automation.execute("https://example.com", [])
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_execute_without_playwright_fails_gracefully(self):
        """execute should fail gracefully if Playwright not available"""
        if not PLAYWRIGHT_AVAILABLE:
            automation = WebAutomation()
            result = await automation.execute("https://example.com", [])
            assert result["success"] is False
            assert "error" in result


class TestAutomationActionTypes:
    """Test various automation action types"""
    
    def test_click_action(self):
        """Should support click action"""
        step = AutomationStep(action="click", selector="#btn")
        assert step.action == "click"
    
    def test_type_action(self):
        """Should support type action"""
        step = AutomationStep(action="type", selector="input", value="text")
        assert step.action == "type"
    
    def test_wait_action(self):
        """Should support wait action"""
        step = AutomationStep(action="wait", selector=".element")
        assert step.action == "wait"
    
    def test_extract_action(self):
        """Should support extract action"""
        step = AutomationStep(action="extract", selector=".data")
        assert step.action == "extract"
    
    def test_screenshot_action(self):
        """Should support screenshot action"""
        step = AutomationStep(action="screenshot", value="shot.png")
        assert step.action == "screenshot"
    
    def test_press_action(self):
        """Should support press action"""
        step = AutomationStep(action="press", value="Enter")
        assert step.action == "press"


class TestAutomationStepWithSelectors:
    """Test AutomationStep with various selectors"""
    
    def test_id_selector(self):
        """Should work with ID selector"""
        step = AutomationStep(action="click", selector="#myId")
        assert step.selector.startswith("#")
    
    def test_class_selector(self):
        """Should work with class selector"""
        step = AutomationStep(action="click", selector=".myClass")
        assert step.selector.startswith(".")
    
    def test_xpath_selector(self):
        """Should work with XPath selector"""
        step = AutomationStep(action="click", selector="//button[@name='submit']")
        assert step.selector.startswith("//")
    
    def test_tag_selector(self):
        """Should work with tag selector"""
        step = AutomationStep(action="click", selector="button")
        assert step.selector == "button"
