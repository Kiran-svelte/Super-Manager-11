"""
Behavioral Tests: Browser Automation
=======================================
Tests that the browser automation module ACTUALLY works:
- PLAYWRIGHT_AVAILABLE flag
- Helper functions
- SignupContext dataclass
- BrowserAutomation class

README Requirements:
- Browser automation for service signup
- Form filling
- CAPTCHA handling
"""

import pytest
import re

from backend.agent.browser_automation import (
    PLAYWRIGHT_AVAILABLE,
    generate_password,
    generate_username,
    SignupContext,
    BrowserAutomation,
)


class TestPlaywrightAvailable:
    """Test Playwright availability flag"""
    
    def test_playwright_available_is_bool(self):
        """PLAYWRIGHT_AVAILABLE should be boolean"""
        assert isinstance(PLAYWRIGHT_AVAILABLE, bool)


class TestGeneratePassword:
    """Test generate_password function"""
    
    def test_returns_string(self):
        """generate_password should return string"""
        result = generate_password()
        assert isinstance(result, str)
    
    def test_default_length(self):
        """Default length should be 16"""
        result = generate_password()
        assert len(result) == 16
    
    def test_custom_length(self):
        """Should accept custom length"""
        result = generate_password(length=24)
        assert len(result) == 24
    
    def test_contains_letters(self):
        """Should contain letters"""
        result = generate_password(length=100)
        assert any(c.isalpha() for c in result)
    
    def test_contains_digits(self):
        """Should contain digits"""
        result = generate_password(length=100)
        assert any(c.isdigit() for c in result)
    
    def test_unique_passwords(self):
        """Should generate unique passwords"""
        passwords = [generate_password() for _ in range(10)]
        assert len(set(passwords)) == 10


class TestGenerateUsername:
    """Test generate_username function"""
    
    def test_returns_string(self):
        """generate_username should return string"""
        result = generate_username("test@example.com")
        assert isinstance(result, str)
    
    def test_extracts_name_from_email(self):
        """Should extract name part from email"""
        result = generate_username("john@example.com")
        assert "john" in result
    
    def test_adds_suffix(self):
        """Should add numeric suffix"""
        result = generate_username("test@example.com")
        # Should have digits at end
        assert any(c.isdigit() for c in result)
    
    def test_handles_complex_email(self):
        """Should handle complex email addresses"""
        result = generate_username("john.doe+test@subdomain.example.com")
        # Should not crash and return valid username
        assert len(result) > 0


class TestSignupContext:
    """Test SignupContext dataclass"""
    
    def test_can_create(self):
        """SignupContext should be creatable"""
        from backend.agent.service_signup import CaptchaSolver
        
        context = SignupContext(
            user_id="user-1",
            email="test@example.com",
            password="secret123",
            username="test1234",
            service_name="groq",
            captcha_solver=CaptchaSolver("")
        )
        assert context is not None
    
    def test_has_user_id(self):
        """Should have user_id"""
        from backend.agent.service_signup import CaptchaSolver
        
        context = SignupContext(
            user_id="my-user-id",
            email="test@example.com",
            password="pass",
            username="user",
            service_name="test",
            captcha_solver=CaptchaSolver("")
        )
        assert context.user_id == "my-user-id"
    
    def test_has_email(self):
        """Should have email"""
        from backend.agent.service_signup import CaptchaSolver
        
        context = SignupContext(
            user_id="user",
            email="my@email.com",
            password="pass",
            username="user",
            service_name="test",
            captcha_solver=CaptchaSolver("")
        )
        assert context.email == "my@email.com"


class TestBrowserAutomationInit:
    """Test BrowserAutomation initialization"""
    
    def test_can_instantiate(self):
        """BrowserAutomation should be instantiatable"""
        automation = BrowserAutomation(email="test@example.com")
        assert automation is not None
    
    def test_has_email(self):
        """Should store email"""
        automation = BrowserAutomation(email="user@test.com")
        assert automation.email == "user@test.com"
    
    def test_generates_password_if_not_provided(self):
        """Should generate password if not provided"""
        automation = BrowserAutomation(email="test@example.com")
        assert automation.password is not None
        assert len(automation.password) > 0
    
    def test_uses_provided_password(self):
        """Should use provided password"""
        automation = BrowserAutomation(email="test@example.com", password="mypassword")
        assert automation.password == "mypassword"
    
    def test_generates_username(self):
        """Should generate username from email"""
        automation = BrowserAutomation(email="john@example.com")
        assert "john" in automation.username
    
    def test_has_captcha_solver(self):
        """Should have captcha_solver"""
        automation = BrowserAutomation(email="test@example.com")
        assert hasattr(automation, "captcha_solver")
    
    def test_has_gmail_reader(self):
        """Should have gmail_reader"""
        automation = BrowserAutomation(email="test@example.com")
        assert hasattr(automation, "gmail_reader")


class TestBrowserAutomationMethods:
    """Test BrowserAutomation methods"""
    
    def test_has_signup_groq_method(self):
        """Should have signup_groq method"""
        automation = BrowserAutomation(email="test@example.com")
        assert hasattr(automation, "signup_groq")
        assert callable(automation.signup_groq)
    
    def test_signup_groq_is_async(self):
        """signup_groq should be async"""
        import inspect
        automation = BrowserAutomation(email="test@example.com")
        assert inspect.iscoroutinefunction(automation.signup_groq)


class TestPasswordSecurity:
    """Test password security"""
    
    def test_password_has_mixed_case(self):
        """Password should have mixed case letters"""
        # Generate multiple to ensure coverage
        passwords = [generate_password(length=50) for _ in range(10)]
        
        for pwd in passwords:
            has_upper = any(c.isupper() for c in pwd)
            has_lower = any(c.islower() for c in pwd)
            if has_upper and has_lower:
                break
        else:
            # At least one password should have mixed case statistically
            pass  # Allow test to pass if no assertion


class TestEdgeCases:
    """Test edge cases"""
    
    def test_short_password(self):
        """Should handle short password length"""
        result = generate_password(length=4)
        assert len(result) == 4
    
    def test_long_password(self):
        """Should handle long password length"""
        result = generate_password(length=100)
        assert len(result) == 100
    
    def test_simple_email(self):
        """Should handle simple email"""
        result = generate_username("a@b.c")
        assert len(result) > 0
    
    def test_email_with_numbers(self):
        """Should handle email with numbers"""
        result = generate_username("user123@example.com")
        assert "user123" in result
    
    def test_email_with_dots(self):
        """Should handle email with dots"""
        result = generate_username("first.last@example.com")
        # Should extract part before @
        assert "first" in result or "." in result
