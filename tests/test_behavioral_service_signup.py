"""
Behavioral Tests: Service Signup
=================================
Tests that the service signup module ACTUALLY works:
- SignupResult dataclass
- CaptchaSolver class
- CAPTCHA_API_KEY environment handling

README Requirements:
- Automated service signup
- CAPTCHA solving
- Email verification handling
"""

import pytest
from dataclasses import fields, is_dataclass

from backend.agent.service_signup import (
    SignupResult,
    CaptchaSolver,
    CAPTCHA_API_KEY,
)


class TestCaptchaApiKey:
    """Test CAPTCHA_API_KEY configuration"""
    
    def test_is_string(self):
        """CAPTCHA_API_KEY should be string"""
        assert isinstance(CAPTCHA_API_KEY, str)


class TestSignupResultDataclass:
    """Test SignupResult dataclass"""
    
    def test_can_create_minimal(self):
        """SignupResult should be creatable with minimal fields"""
        result = SignupResult(
            success=True,
            service_name="groq",
            message="Success"
        )
        assert result is not None
    
    def test_is_dataclass(self):
        """SignupResult should be a dataclass"""
        assert is_dataclass(SignupResult)
    
    def test_has_success(self):
        """Should have success field"""
        result = SignupResult(success=True, service_name="test", message="ok")
        assert result.success is True
    
    def test_has_service_name(self):
        """Should have service_name field"""
        result = SignupResult(success=True, service_name="openai", message="ok")
        assert result.service_name == "openai"
    
    def test_has_message(self):
        """Should have message field"""
        result = SignupResult(success=True, service_name="test", message="All good")
        assert result.message == "All good"
    
    def test_default_account_email_is_none(self):
        """Default account_email should be None"""
        result = SignupResult(success=True, service_name="test", message="ok")
        assert result.account_email is None
    
    def test_default_account_username_is_none(self):
        """Default account_username should be None"""
        result = SignupResult(success=True, service_name="test", message="ok")
        assert result.account_username is None
    
    def test_default_api_key_is_none(self):
        """Default api_key should be None"""
        result = SignupResult(success=True, service_name="test", message="ok")
        assert result.api_key is None
    
    def test_default_api_secret_is_none(self):
        """Default api_secret should be None"""
        result = SignupResult(success=True, service_name="test", message="ok")
        assert result.api_secret is None
    
    def test_default_additional_data_is_empty_dict(self):
        """Default additional_data should be empty dict"""
        result = SignupResult(success=True, service_name="test", message="ok")
        assert result.additional_data == {}
        assert isinstance(result.additional_data, dict)
    
    def test_default_needs_verification_is_false(self):
        """Default needs_verification should be False"""
        result = SignupResult(success=True, service_name="test", message="ok")
        assert result.needs_verification is False
    
    def test_default_needs_user_input_is_none(self):
        """Default needs_user_input should be None"""
        result = SignupResult(success=True, service_name="test", message="ok")
        assert result.needs_user_input is None
    
    def test_default_blocked_reason_is_none(self):
        """Default blocked_reason should be None"""
        result = SignupResult(success=True, service_name="test", message="ok")
        assert result.blocked_reason is None
    
    def test_can_set_api_key(self):
        """Should accept api_key"""
        result = SignupResult(
            success=True,
            service_name="groq",
            message="ok",
            api_key="sk-abc123"
        )
        assert result.api_key == "sk-abc123"
    
    def test_can_set_api_secret(self):
        """Should accept api_secret"""
        result = SignupResult(
            success=True,
            service_name="aws",
            message="ok",
            api_secret="secret-xyz"
        )
        assert result.api_secret == "secret-xyz"
    
    def test_can_set_account_email(self):
        """Should accept account_email"""
        result = SignupResult(
            success=True,
            service_name="test",
            message="ok",
            account_email="user@example.com"
        )
        assert result.account_email == "user@example.com"
    
    def test_can_set_needs_verification(self):
        """Should accept needs_verification"""
        result = SignupResult(
            success=False,
            service_name="test",
            message="Pending",
            needs_verification=True
        )
        assert result.needs_verification is True
    
    def test_can_set_blocked_reason(self):
        """Should accept blocked_reason"""
        result = SignupResult(
            success=False,
            service_name="test",
            message="Blocked",
            blocked_reason="IP banned"
        )
        assert result.blocked_reason == "IP banned"
    
    def test_additional_data_accepts_dict(self):
        """Should accept additional_data dict"""
        result = SignupResult(
            success=True,
            service_name="test",
            message="ok",
            additional_data={"org_id": "org-123", "tier": "free"}
        )
        assert result.additional_data["org_id"] == "org-123"
        assert result.additional_data["tier"] == "free"


class TestSignupResultFields:
    """Test SignupResult field structure"""
    
    def test_field_count(self):
        """SignupResult should have expected number of fields"""
        result_fields = fields(SignupResult)
        # success, service_name, message, account_email, account_username,
        # api_key, api_secret, additional_data, needs_verification, 
        # needs_user_input, blocked_reason = 11 fields
        assert len(result_fields) == 11
    
    def test_required_fields(self):
        """Should have success, service_name, message as required"""
        # Creating without these should fail
        with pytest.raises(TypeError):
            SignupResult()
    
    def test_success_can_be_false(self):
        """success can be False"""
        result = SignupResult(success=False, service_name="test", message="Failed")
        assert result.success is False


class TestCaptchaSolverInit:
    """Test CaptchaSolver initialization"""
    
    def test_can_instantiate(self):
        """CaptchaSolver should be instantiatable"""
        solver = CaptchaSolver()
        assert solver is not None
    
    def test_accepts_api_key(self):
        """Should accept api_key"""
        solver = CaptchaSolver(api_key="my-key")
        assert solver.api_key == "my-key"
    
    def test_default_api_key_from_env(self):
        """Default api_key should come from env"""
        solver = CaptchaSolver()
        assert solver.api_key == CAPTCHA_API_KEY


class TestCaptchaSolverApiUrl:
    """Test CaptchaSolver API URL"""
    
    def test_has_api_url(self):
        """Should have API_URL"""
        assert hasattr(CaptchaSolver, "API_URL")
    
    def test_api_url_is_2captcha(self):
        """API_URL should be 2captcha"""
        assert "2captcha" in CaptchaSolver.API_URL


class TestCaptchaSolverMethods:
    """Test CaptchaSolver methods"""
    
    def test_has_solve_recaptcha(self):
        """Should have solve_recaptcha method"""
        solver = CaptchaSolver()
        assert hasattr(solver, "solve_recaptcha")
        assert callable(solver.solve_recaptcha)
    
    def test_has_solve_hcaptcha(self):
        """Should have solve_hcaptcha method"""
        solver = CaptchaSolver()
        assert hasattr(solver, "solve_hcaptcha")
        assert callable(solver.solve_hcaptcha)
    
    def test_solve_recaptcha_is_async(self):
        """solve_recaptcha should be async"""
        import inspect
        solver = CaptchaSolver()
        assert inspect.iscoroutinefunction(solver.solve_recaptcha)
    
    def test_solve_hcaptcha_is_async(self):
        """solve_hcaptcha should be async"""
        import inspect
        solver = CaptchaSolver()
        assert inspect.iscoroutinefunction(solver.solve_hcaptcha)


class TestCaptchaSolverWithoutKey:
    """Test CaptchaSolver graceful degradation without API key"""
    
    @pytest.mark.asyncio
    async def test_solve_recaptcha_returns_none_without_key(self):
        """solve_recaptcha should return None without API key"""
        solver = CaptchaSolver(api_key="")
        result = await solver.solve_recaptcha(
            site_key="test-site-key",
            page_url="https://example.com"
        )
        assert result is None
    
    @pytest.mark.asyncio
    async def test_solve_hcaptcha_returns_none_without_key(self):
        """solve_hcaptcha should return None without API key"""
        solver = CaptchaSolver(api_key="")
        result = await solver.solve_hcaptcha(
            site_key="test-site-key",
            page_url="https://example.com"
        )
        assert result is None


class TestSignupResultUseCases:
    """Test SignupResult for various use cases"""
    
    def test_successful_signup_with_api_key(self):
        """Successful signup returns api_key"""
        result = SignupResult(
            success=True,
            service_name="groq",
            message="Account created successfully",
            account_email="ai@example.com",
            api_key="gsk_abc123"
        )
        assert result.success is True
        assert result.api_key == "gsk_abc123"
    
    def test_failed_signup_with_reason(self):
        """Failed signup with blocked_reason"""
        result = SignupResult(
            success=False,
            service_name="openai",
            message="Signup blocked",
            blocked_reason="VPN detected"
        )
        assert result.success is False
        assert result.blocked_reason == "VPN detected"
    
    def test_pending_verification(self):
        """Signup pending email verification"""
        result = SignupResult(
            success=False,
            service_name="anthropic",
            message="Awaiting email verification",
            needs_verification=True,
            account_email="user@example.com"
        )
        assert result.needs_verification is True
        assert result.account_email is not None
    
    def test_needs_user_input(self):
        """Signup needs user input (e.g., phone number)"""
        result = SignupResult(
            success=False,
            service_name="twilio",
            message="Additional info needed",
            needs_user_input="phone_number"
        )
        assert result.needs_user_input == "phone_number"
